"""Scan 7: sensitivity of the headline results to the active-hours window.
Reruns the weather regression (JMA) and the 3-day ex-ante forecast test with
the window defined at 1%, 2% (paper) and 5% share thresholds, and with the
fixed 09:00-17:00 window. Also reports recall for the faces busy-day warning.
Writes ../out/20261014_window_sensitivity.md.
"""
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import common
from common import WX_SITE, daily_counts, daytype
import scan03 as s3

warnings.filterwarnings("ignore")
L = []
def p(x=""): L.append(x); print(x, flush=True)
def tbl(df, fmt="{:.2f}"):
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join([df.index.name or ""] + cols) + " |"); p("|" + "---|" * (len(cols) + 1))
    for i, r in df.iterrows():
        p("| " + " | ".join([str(i)] + [fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r]) + " |")
    p()

VARIANTS = {"1% share": dict(min_share=0.01), "2% share (paper)": dict(min_share=0.02), "5% share": dict(min_share=0.05), "fixed 09:00-17:00": "fixed"}
orig_active = common.active_hours
def make_active(spec):
    if spec == "fixed":
        return lambda site, **kw: {m: list(range(9, 18)) for m in range(1, 13)}
    return lambda site, **kw: orig_active(site, **{**kw, **spec})

p("# Window sensitivity (scan 07)\n")
p("Headline results under four definitions of the active-hours window. Rain effect: JMA, % per 10 mm with 95% interval. Forecast test: 3-day WAPE, calendar ridge vs ridge with the archived forecast, Diebold-Mariano p.\n")
rows = []
for name, spec in VARIANTS.items():
    common.active_hours = make_active(spec); s3.active_hours = common.active_hours
    s3.daily_weather_active = common.daily_weather_active
    for k in s3.FEEDS:
        w = common.daily_weather_active(WX_SITE[k], source="jma")
        f = pd.DataFrame({"ly": np.log1p(s3.D[k])}).join(w).dropna()
        dt = daytype(f.index); f["dow"] = f.index.dayofweek.astype(str); f["hol"] = (dt.values == "holiday").astype(int); f["ym"] = f.index.to_period("M").astype(str)
        m = smf.ols("ly ~ C(dow) + hol + C(ym) + rain_mm + gust_ms + sun_h + temp_c", f).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
        b, se = m.params["rain_mm"] * 10, m.bse["rain_mm"] * 10
        rain = f"{100*(np.exp(b)-1):+.0f} [{100*(np.exp(b-1.96*se)-1):+.0f}, {100*(np.exp(b+1.96*se)-1):+.0f}]"
        P = {mm: s3.run(k, 3, mm) for mm in ["calendar", "forecast"]}
        y = P["calendar"][1]
        idx = P["calendar"][0].index.intersection(P["forecast"][0].index); idx = idx[y.loc[idx].notna() & (y.loc[idx] > 0)]
        yy = y.loc[idx].values
        wc = 100 * np.abs(P["calendar"][0].loc[idx].values - yy).sum() / yy.sum()
        wf = 100 * np.abs(P["forecast"][0].loc[idx].values - yy).sum() / yy.sum()
        t, pv = s3.dm_test(pd.Series(P["calendar"][0].loc[idx].values - yy), pd.Series(P["forecast"][0].loc[idx].values - yy))
        rows.append({"window": name, "site": s3.NAMES[k], "rain % per 10 mm": rain, "3d WAPE calendar": wc, "3d WAPE + forecast": wf, "DM p": pv})
        print(name, k, "done", flush=True)
common.active_hours = orig_active; s3.active_hours = orig_active
R = pd.DataFrame(rows).set_index("window"); tbl(R)

# faces busy-day warning: recall
p("## Faces warning at Rainbow Line (lots 1+2, paper outage rule): precision and recall\n")
from common import load
def daily(site, cls):
    d = load("5min", site, cls).set_index("t0")["count"]; g = d.groupby(d.index.normalize()); tot, n = g.sum(), g.size(); tot[n < 0.8 * 288] = np.nan; return tot
S1, S2 = "rainbow-line-parking-lot-1-gate", "rainbow-line-parking-lot-2-gate"
p1, p2, f1, f2 = daily(S1, "LicensePlate"), daily(S2, "LicensePlate"), daily(S1, "Face"), daily(S2, "Face")
idx = p1.index.union(p2.index).union(f1.index).union(f2.index); p1, p2, f1, f2 = (s.reindex(idx) for s in (p1, p2, f1, f2))
lot1_on = p1 > 0
series = {"plates": (p1 + p2).where(lot1_on), "faces": (f1 + f2).where(lot1_on)}
orig = s3.D.copy(); out = []
for name, ser in series.items():
    s3.D = orig.copy(); s3.D["rl1"] = ser.asfreq("D")
    for mode in ["calendar", "forecast"]:
        r = s3.busy_eval("rl1", "top", mode, h=3)
        out.append({"series": name, "weather": mode, "days": r["days"], "AUC": r["AUC [95% CI]"], "precision": r["precision"], "recall": r["recall"]})
s3.D = orig
tbl(pd.DataFrame(out).set_index("series"))
open("../out/20261014_window_sensitivity.md", "w").write("\n".join(L))
