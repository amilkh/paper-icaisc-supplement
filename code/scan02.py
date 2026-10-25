"""Scan 2: weather sensitivity and operational (staffing) forecast skill.

Everything here uses only an entry counter, a public calendar and a global
weather source, so the same code can run for a Madinah site.
Writes ../out/20261011_weather_openmeteo.md.
"""
import sys, warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from common import WX_SITE, daily_counts, daily_weather_active, daytype, fivemin

warnings.filterwarnings("ignore")
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "openmeteo"
SRC_TXT = {"openmeteo": "the Open-Meteo archive", "jma": "JMA station observations (Fukui City, Mikuni AMeDAS, Mihama AMeDAS; peak wind is the highest hourly mean)"}[SOURCE]
L = []
def p(s=""): L.append(s)
def tbl(df, fmt="{:.2f}"):
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join([df.index.name or ""] + cols) + " |"); p("|" + "---|" * (len(cols) + 1))
    for i, r in df.iterrows():
        p("| " + " | ".join([str(i)] + [fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r]) + " |")
    p()

D = daily_counts()
FEEDS = ["station", "tojinbo", "rl1"]
NAMES = {"station": "Fukui Station (people)", "tojinbo": "Tojinbo (people)", "rl1": "Rainbow Line lot 1 (cars)"}

def frame(k):
    w = daily_weather_active(WX_SITE[k], source=SOURCE)
    f = pd.DataFrame({"y": D[k]}).join(w, how="left")
    dt = daytype(f.index)
    f["dow"] = f.index.dayofweek.astype(str)
    f["off"] = (dt.values != "weekday").astype(int)
    f["hol"] = (dt.values == "holiday").astype(int)
    f["ym"] = f.index.to_period("M").astype(str)
    f["month"] = f.index.month
    f["ly"] = np.log1p(f["y"])
    return f

p("# Scan 02: weather sensitivity and staffing-forecast skill\n")
p(f"Data: camera counts @ b89bc2c; weather from {SRC_TXT}, aggregated over each site's own active hours (hours holding at least 2% of the day's detections in that calendar month, which follow opening hours and season). Outage days are excluded.\n")

# A. weather elasticities
p("## A. Weather effect on daily counts\n")
p("OLS on log counts with day-of-week, holiday and year-month fixed effects, HAC errors (lag 7). Effects are % change in the daily count.\n")
rows = []
for k in FEEDS:
    f = frame(k).dropna(subset=["ly", "rain_mm"])
    m = smf.ols("ly ~ C(dow) + hol + C(ym) + rain_mm + gust_ms + sun_h + temp_c", f).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
    def eff(v, scale):
        b, se = m.params[v] * scale, m.bse[v] * scale
        lo, hi = 100 * (np.exp(b - 1.96 * se) - 1), 100 * (np.exp(b + 1.96 * se) - 1)
        return f"{100*(np.exp(b)-1):+.1f}% [{lo:+.1f}, {hi:+.1f}]"
    rows.append({"feed": NAMES[k], "n days": int(m.nobs), "per 10 mm rain": eff("rain_mm", 10),
                 "per +5 m/s peak hourly wind": eff("gust_ms", 5), "per +3 h sun": eff("sun_h", 3),
                 "per +5 °C": eff("temp_c", 5), "R²": m.rsquared})
tbl(pd.DataFrame(rows).set_index("feed"))
p("Brackets: 95% interval, endpoints transformed from the log(1+y) scale.\n")

# B. forecast skill at 1 and 3 days ahead
p("## B. Daily forecast skill, rolling origin (weekly refit, test 2025-10-13 to 2026-10-10)\n")
p("Models: *naive* = same weekday last week; *calendar* = ridge on day-of-week, holiday, month and the latest available lags; *calendar + weather* adds the day's observed weather as a stand-in for a perfect forecast. *Within ±30%* is the share of days whose error is under 30%, close to the operator's '70% accuracy three days ahead'.\n")

def design(f, h, weather):
    X = pd.get_dummies(f[["dow"]], drop_first=False).astype(float)
    X["hol"] = f["hol"]
    X = X.join(pd.get_dummies(f["month"], prefix="m").astype(float))
    lag = f["ly"].shift(7 if h <= 7 else 14)
    X["lag_wk"] = lag
    X["lag_h"] = f["ly"].shift(h)
    X["roll28"] = f["ly"].shift(h).rolling(28, min_periods=10).mean()
    if weather:
        for c in ["rain_mm", "gust_ms", "sun_h", "temp_c", "snow_cm"]:
            X[c] = f[c]
        X["rain_off"] = f["rain_mm"] * f["off"]
    return X

res, preds = [], {}
start = pd.Timestamp("2025-10-13")
for k in FEEDS:
    f = frame(k)
    for h in [1, 3]:
        out = {"naive": [], "calendar": [], "calendar+weather": []}
        ys = []
        for monday in pd.date_range(start, f.index.max(), freq="W-MON"):
            test = f.loc[monday: monday + pd.Timedelta(days=6)]
            cutoff = monday - pd.Timedelta(days=h)  # data known at forecast time
            for name, wx in [("calendar", False), ("calendar+weather", True)]:
                X = design(f, h, wx)
                tr = X.index < cutoff
                ok = tr & X.notna().all(1) & f["ly"].notna()
                mdl = Ridge(alpha=1.0).fit(X[ok], f["ly"][ok])
                Xt = X.loc[test.index]
                pr = pd.Series(np.nan, index=test.index)
                good = Xt.notna().all(1)
                if good.any():
                    pr[good] = np.expm1(mdl.predict(Xt[good]))
                out[name].append(pr)
            out["naive"].append(f["y"].shift(7).loc[test.index])
            ys.append(test["y"])
        y = pd.concat(ys)
        for name, ps in out.items():
            pr = pd.concat(ps)
            ok = y.notna() & pr.notna() & (y > 0)
            if name == "naive":
                ok_naive = ok
            e = (pr[ok] - y[ok]).abs()
            res.append({"feed": NAMES[k], "h": f"{h}d", "model": name, "days": int(ok.sum()),
                        "WAPE %": 100 * e.sum() / y[ok].sum(),
                        "within ±30%": (e / y[ok] < 0.30).mean()})
            preds[(k, h, name)] = pr
        preds[(k, h, "y")] = y
r = pd.DataFrame(res).set_index("feed"); tbl(r)

# C. staffing triggers
p("## C. Busy-day warning three days ahead\n")
p("A busy day is a day in the site's top 20% (training-period threshold). For Rainbow Line, also *lot 2 in use* (≥20 plates at the overflow lot), which is what triggers the shuttle and extra staff. Logistic regression on the same features, same rolling origin.\n")

def trigger_eval(k, label_fn, name, wx):
    f = frame(k)
    if k == "rl1":
        f["rl2"] = D["rl2"]
    X = design(f, 3, wx)
    probs, labs = [], []
    for monday in pd.date_range(start, f.index.max(), freq="W-MON"):
        cutoff = monday - pd.Timedelta(days=3)
        tr = (X.index < cutoff) & X.notna().all(1)
        lab = label_fn(f, f.index < cutoff)
        tr &= lab.notna()
        if lab[tr].nunique() < 2:
            continue
        mdl = LogisticRegression(max_iter=2000, C=1.0).fit(X[tr], lab[tr].astype(int))
        idx = f.loc[monday: monday + pd.Timedelta(days=6)].index
        te = X.loc[idx].notna().all(1) & lab.loc[idx].notna()
        if te.any():
            probs.append(pd.Series(mdl.predict_proba(X.loc[idx][te])[:, 1], index=idx[te]))
            labs.append(lab.loc[idx][te])
    pr, yb = pd.concat(probs), pd.concat(labs).astype(int)
    hit = pr >= 0.5
    tp = (hit & (yb == 1)).sum()
    return {"trigger": name, "features": "calendar+weather" if wx else "calendar",
            "test days": len(yb), "busy share": yb.mean(), "AUC": roc_auc_score(yb, pr),
            "precision": tp / max(hit.sum(), 1), "recall": tp / max(yb.sum(), 1)}

def top20(k):
    def fn(f, train_mask):
        thr = f.loc[train_mask, "y"].quantile(0.8)
        return (f["y"] >= thr).where(f["y"].notna())
    return fn
def lot2(f, train_mask):
    return (f["rl2"] >= 20).where(f["rl2"].notna())

rows = []
for wx in [False, True]:
    for k in FEEDS:
        rows.append(trigger_eval(k, top20(k), f"{NAMES[k]}: top 20% day", wx))
    rows.append(trigger_eval("rl1", lot2, "Rainbow Line: lot 2 in use", wx))
t = pd.DataFrame(rows).set_index("trigger"); tbl(t)

# D. data-quality flags an operator would see
p("## D. Counts outside opening hours (Rainbow Line road open about 08:00 to 18:00)\n")
rows = []
for k in ["rl1", "rl2"]:
    s = fivemin(k).set_index("t0")["count"]
    night = s[(s.index.hour < 7) | (s.index.hour >= 19)].sum()
    rows.append({"feed": k, "plates 19:00 to 07:00": int(night), "share of all": night / s.sum()})
tbl(pd.DataFrame(rows).set_index("feed"), "{:.3f}")

open("../out/20261011_weather_openmeteo.md" if SOURCE == "openmeteo" else "../out/20261012_weather_jma.md", "w").write("\n".join(L))
print("\n".join(L))
