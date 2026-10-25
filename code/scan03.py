"""Scan 3: honest ex-ante test. Models are trained on observed weather (Open-Meteo
archive) but predict with the forecast issued h days earlier (Open-Meteo
previous-runs API). Adds Diebold-Mariano tests and block-bootstrap intervals.
Writes ../out/20261012_forecast_weather_test.md.
"""
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from common import DATA, WX_SITE, daily_counts, daily_weather_active, daytype, active_hours

warnings.filterwarnings("ignore")
rng = np.random.default_rng(0)
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
NAMES = {"station": "Fukui Station", "tojinbo": "Tojinbo", "rl1": "Rainbow Line lot 1"}
WX = ["rain_mm", "gust_ms", "sun_h", "temp_c"]
START = pd.Timestamp("2025-10-13")

def forecast_weather(site, h, h0=9, h1=17):
    fp = DATA / f"fcst7_{site}.parquet"
    f = pd.read_parquet(fp if fp.exists() else DATA / f"fcst_{site}.parquet").set_index("t0")
    ah = active_hours(site)
    f = f[np.array([hr in ah[m] for m, hr in zip(f.index.month, f.index.hour)])]
    g = f.groupby(f.index.normalize())
    return pd.DataFrame({
        "rain_mm": g[f"precipitation_previous_day{h}"].sum(),
        "gust_ms": g[f"wind_gusts_10m_previous_day{h}"].max(),
        "sun_h": g[f"sunshine_duration_previous_day{h}"].sum() / 3600,
        "temp_c": g[f"temperature_2m_previous_day{h}"].mean(),
    })

def frame(k):
    f = pd.DataFrame({"y": D[k]}).join(daily_weather_active(WX_SITE[k]), how="left")
    dt = daytype(f.index)
    f["dow"] = f.index.dayofweek.astype(str)
    f["off"] = (dt.values != "weekday").astype(int)
    f["hol"] = (dt.values == "holiday").astype(int)
    f["month"] = f.index.month
    f["ly"] = np.log1p(f["y"])
    return f

def design(f, h, wx):
    X = pd.get_dummies(f[["dow"]]).astype(float)
    X["hol"] = f["hol"]
    X = X.join(pd.get_dummies(f["month"], prefix="m").astype(float))
    X["lag_wk"] = f["ly"].shift(7)
    X["lag_h"] = f["ly"].shift(h)
    X["roll28"] = f["ly"].shift(h).rolling(28, min_periods=10).mean()
    if wx is not None:
        for c in WX:
            X[c] = wx[c].reindex(f.index)
        X["rain_off"] = X["rain_mm"] * f["off"]
    return X

def run(k, h, mode):
    """mode: calendar | observed | forecast. Returns predictions on test days."""
    f = frame(k)
    obs = f[WX]
    Xtr = design(f, h, None if mode == "calendar" else obs)
    Xte = design(f, h, None if mode == "calendar" else (obs if mode == "observed" else forecast_weather(WX_SITE[k], h)))
    preds = []
    for monday in pd.date_range(START, f.index.max(), freq="W-MON"):
        cutoff = monday - pd.Timedelta(days=h)
        ok = (Xtr.index < cutoff) & Xtr.notna().all(1) & f["ly"].notna()
        mdl = Ridge(alpha=1.0).fit(Xtr[ok], f["ly"][ok])
        idx = f.loc[monday: monday + pd.Timedelta(days=6)].index
        Xt = Xte.loc[idx]; good = Xt.notna().all(1)
        if good.any():
            preds.append(pd.Series(np.expm1(mdl.predict(Xt[good])), index=idx[good]))
    return pd.concat(preds), f["y"]

def gain_kept(w_cal, w_fcst, w_obs):
    """Share of the observed-weather WAPE gain over calendar that the issued forecast keeps.
    NaN where observed weather does not beat calendar, so there is no gain to keep."""
    gain = w_cal - w_obs
    return (w_cal - w_fcst) / gain if gain > 0 else np.nan

def gain_kept_ci(y, cal, fcst, obs, B=2000, block=7, seed=1):
    """95% weekly block-bootstrap interval for gain_kept, as in block_boot. Uses its own
    generator so the existing intervals keep their random draws. Resamples where observed
    weather does not beat calendar are dropped; returns (lo, hi, share of resamples kept)."""
    g = np.random.default_rng(seed)
    idx = np.arange(len(y)); nb = int(np.ceil(len(y) / block)); out = []
    ec, ef, eo = np.abs(cal - y), np.abs(fcst - y), np.abs(obs - y)
    for _ in range(B):
        starts = g.integers(0, len(y) - block + 1, nb)
        s = np.concatenate([idx[s:s + block] for s in starts])[:len(y)]
        gain = ec[s].sum() - eo[s].sum()
        if gain > 0:
            out.append((ec[s].sum() - ef[s].sum()) / gain)
    if len(out) < B / 2:
        return np.nan, np.nan, len(out) / B
    lo, hi = np.percentile(out, [2.5, 97.5])
    return lo, hi, len(out) / B

def fmt_kept(k, lo, hi):
    return "n/a" if np.isnan(k) else f"{100 * k:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]" if not np.isnan(lo) else f"{100 * k:.0f}%"

def dm_test(e1, e2, lag=7):
    """Diebold-Mariano on absolute errors with Newey-West variance. Negative = model 2 better."""
    d = (np.abs(e2) - np.abs(e1)).dropna()
    n = len(d); dc = d - d.mean()
    v = np.dot(dc, dc) / n
    for l in range(1, lag + 1):
        v += 2 * (1 - l / (lag + 1)) * np.dot(dc[l:], dc[:-l]) / n
    t = d.mean() / np.sqrt(v / n)
    return t, 2 * (1 - stats.norm.cdf(abs(t)))

def block_boot(y, a, b, B=2000, block=7):
    """95% interval for WAPE(a) - WAPE(b) in points, weekly blocks."""
    idx = np.arange(len(y)); nb = int(np.ceil(len(y) / block)); out = []
    for _ in range(B):
        starts = rng.integers(0, len(y) - block + 1, nb)
        s = np.concatenate([idx[s:s + block] for s in starts])[:len(y)]
        yy, aa, bb = y[s], a[s], b[s]
        out.append(100 * (np.abs(aa - yy).sum() - np.abs(bb - yy).sum()) / yy.sum())
    return np.percentile(out, [2.5, 97.5])

# B. busy-day warnings with forecast weather
def busy_eval(k, label, mode, h=3):
    f = frame(k)
    if label == "lot2":
        f["rl2"] = D["rl2"]
    obs = f[WX]
    Xtr = design(f, h, None if mode == "calendar" else obs)
    Xte = design(f, h, None if mode == "calendar" else forecast_weather(WX_SITE[k], h))
    probs, labs = [], []
    for monday in pd.date_range(START, f.index.max(), freq="W-MON"):
        cutoff = monday - pd.Timedelta(days=h)
        if label == "lot2":
            lab = (f["rl2"] >= 20).where(f["rl2"].notna())
        else:
            lab = (f["y"] >= f.loc[f.index < cutoff, "y"].quantile(0.8)).where(f["y"].notna())
        tr = (Xtr.index < cutoff) & Xtr.notna().all(1) & lab.notna()
        mdl = LogisticRegression(max_iter=3000).fit(Xtr[tr], lab[tr].astype(int))
        idx = f.loc[monday: monday + pd.Timedelta(days=6)].index
        te = Xte.loc[idx].notna().all(1) & lab.loc[idx].notna()
        if te.any():
            probs.append(pd.Series(mdl.predict_proba(Xte.loc[idx][te])[:, 1], index=idx[te])); labs.append(lab.loc[idx][te])
    pr, yb = pd.concat(probs), pd.concat(labs).astype(int)
    aucs = []
    weeks = pr.index.to_period("W").unique()
    wk = pr.index.to_period("W")
    for _ in range(1000):  # resample calendar weeks jointly for predictions and labels
        pick = rng.choice(len(weeks), len(weeks), replace=True)
        s = np.concatenate([np.where(wk == weeks[i])[0] for i in pick])
        if yb.iloc[s].nunique() == 2:
            aucs.append(roc_auc_score(yb.iloc[s], pr.iloc[s]))
    hit = pr >= 0.5; tp = (hit & (yb == 1)).sum()
    return {"AUC [95% CI]": f"{roc_auc_score(yb, pr):.2f} [{np.percentile(aucs, 2.5):.2f}, {np.percentile(aucs, 97.5):.2f}]",
            "precision": tp / max(hit.sum(), 1), "recall": tp / max(yb.sum(), 1), "days": len(yb),
            "busy days": int(yb.sum()), "flagged": int(hit.sum())}


def main():
    p("# Scan 03: ex-ante forecasts with archived weather forecasts\n")
    p("Training uses observed weather; test predictions use the Open-Meteo forecast issued h days before (previous-runs API). Rolling origin, weekly refit, test 2025-10-13 to 2026-10-10. DM = Diebold-Mariano test on absolute errors, forecast-weather model against calendar only (negative t means weather helps). CI = 95% weekly block bootstrap of the WAPE change.\n")

    rows = []
    for k in FEEDS:
        for h in [1, 3]:
            P = {m: run(k, h, m) for m in ["calendar", "observed", "forecast"]}
            y = P["calendar"][1]
            common = P["calendar"][0].index.intersection(P["forecast"][0].index).intersection(P["observed"][0].index)
            common = common[y.loc[common].notna() & (y.loc[common] > 0)]
            yy = y.loc[common].values
            w = {m: 100 * np.abs(P[m][0].loc[common].values - yy).sum() / yy.sum() for m in P}
            within = {m: (np.abs(P[m][0].loc[common].values - yy) / yy < 0.3).mean() for m in P}
            t, pv = dm_test(pd.Series(P["calendar"][0].loc[common].values - yy), pd.Series(P["forecast"][0].loc[common].values - yy))
            lo, hi = block_boot(yy, P["forecast"][0].loc[common].values, P["calendar"][0].loc[common].values)
            kept = gain_kept(w["calendar"], w["forecast"], w["observed"])
            klo, khi, _ = gain_kept_ci(yy, P["calendar"][0].loc[common].values, P["forecast"][0].loc[common].values,
                                       P["observed"][0].loc[common].values) if not np.isnan(kept) else (np.nan, np.nan, 0)
            rows.append({"site": NAMES[k], "h": f"{h}d", "days": len(common),
                         "WAPE calendar": w["calendar"], "WAPE +forecast wx": w["forecast"], "WAPE +observed wx": w["observed"],
                         "change (pts) [95% CI]": f"{w['forecast']-w['calendar']:+.1f} [{lo:+.1f}, {hi:+.1f}]",
                         "DM t (p)": f"{t:+.2f} ({pv:.3f})",
                         "within ±30%, forecast wx": within["forecast"],
                         "observed-wx gain kept [95% CI]": fmt_kept(kept, klo, khi)})
    p("## A. Daily count forecasts\n"); tbl(pd.DataFrame(rows).set_index("site"))
    p("*Observed-wx gain kept* = (WAPE calendar - WAPE +forecast wx) / (WAPE calendar - WAPE +observed wx): the share of the gain from perfectly known weather that the forecast issued h days earlier delivers; n/a where observed weather does not beat calendar. Interval: 2,000 weekly block-bootstrap resamples of the test days, dropping resamples where observed weather does not beat calendar.\n")

    rows = []
    for k, label, name in [("station", "top", "Fukui Station: top-20% day"), ("tojinbo", "top", "Tojinbo: top-20% day"),
                           ("rl1", "top", "Rainbow Line: top-20% day"), ("rl1", "lot2", "Rainbow Line: car park 2 in use")]:
        for mode in ["calendar", "forecast"]:
            r = busy_eval(k, label, mode); r["warning"] = name; r["weather"] = "none" if mode == "calendar" else "3-day forecast"
            rows.append(r)
    p("## B. Busy-day warnings three days ahead, with the forecast available at the time\n")
    t = pd.DataFrame(rows).set_index("warning")[["weather", "days", "AUC [95% CI]", "precision", "recall"]]; tbl(t)

    open("../out/20261012_forecast_weather_test.md", "w").write("\n".join(L)); print("\n".join(L))


if __name__ == "__main__":
    main()
