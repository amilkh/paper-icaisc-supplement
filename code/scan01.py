"""Scan 1: cross-site patterns in the Fukui camera feeds. Writes out/20261011_cross_site_patterns.md."""
import numpy as np
import pandas as pd
from common import FEEDS, REGIONS, daily_counts, daytype, fivemin

L = []
def p(s=""): L.append(s)
def tbl(df, fmt="{:.2f}"):
    df = df.copy()
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join([df.index.name or ""] + cols) + " |")
    p("|" + "---|" * (len(cols) + 1))
    for i, r in df.iterrows():
        p("| " + " | ".join([str(i)] + [fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r]) + " |")
    p()

D = daily_counts()
p("# Scan 01: cross-site patterns (data @ b89bc2c, 2024-12-20 to 2026-10-10)\n")
p("Outage days (zero or <80% of 5-min bins) are excluded.\n")

# A. coverage
p("## A. Coverage\n")
cov = pd.DataFrame({"valid days": D.notna().sum(), "median/day": D.median(), "max/day": D.max()})
cov.index.name = "feed"; tbl(cov, "{:,.0f}")

# B. day-type uplift
p("## B. Weekend and holiday uplift (median ÷ weekday median)\n")
dt = daytype(D.index)
m = D.groupby(dt.values).median()
up = (m / m.loc["weekday"]).T[["weekend", "holiday"]]
up.index.name = "feed"; tbl(up)

# C. cross-site correlation, raw and after removing weekday x month means
p("## C. Cross-site daily correlation\n")
lg = np.log1p(D)
p("Raw log counts:\n"); c = lg.corr().round(2); c.index.name = ""; tbl(c)
resid = lg - lg.groupby([lg.index.dayofweek, lg.index.month]).transform("mean")
resid = resid[dt.values != "holiday"]
p("Residuals after weekday x month means, holidays excluded (shared shocks such as weather):\n")
c = resid.corr().round(2); c.index.name = ""; tbl(c)

# D. lead-lag on hourly residuals
p("## D. Hourly lead-lag (residual cross-correlation, 09:00 to 17:00)\n")
H = {}
for k in FEEDS:
    s = fivemin(k).set_index("t0")["count"].resample("h").sum()
    H[k] = s
H = pd.DataFrame(H)
H = H[(H.index.hour >= 9) & (H.index.hour <= 17)]
day = H.groupby(H.index.normalize()).transform("sum")
share = H / day.replace(0, np.nan)
r = share - share.groupby([share.index.dayofweek, share.index.hour]).transform("mean")
rows = []
for a, b in [("rl1", "tojinbo"), ("station", "tojinbo"), ("rl1", "station"), ("rl1", "rl2")]:
    out = {"pair": f"{a} → {b}"}
    for lag in [-2, -1, 0, 1, 2]:
        out[f"lag {lag:+d}h"] = r[a].corr(r[b].shift(-lag))
    rows.append(out)
ll = pd.DataFrame(rows).set_index("pair"); tbl(ll)
p("Positive lag: the first feed's intraday deviation precedes the second's by that many hours.\n")

# E. intraday peak hour by day type
p("## E. Intraday profile: peak hour and share of the day in the peak hour\n")
rows = []
for k in FEEDS:
    s = fivemin(k).set_index("t0")["count"].resample("h").sum()
    t = daytype(s.index.normalize())
    for typ in ["weekday", "weekend", "holiday"]:
        prof = s[t.values == typ].groupby(s[t.values == typ].index.hour).mean()
        rows.append({"feed": k, "day": typ, "peak hour": int(prof.idxmax()),
                     "peak share": prof.max() / prof.sum(),
                     "09-12 share": prof.loc[9:11].sum() / prof.sum(),
                     "15-18 share": prof.loc[15:17].sum() / prof.sum()})
tbl(pd.DataFrame(rows).set_index("feed"))

# F. licence-plate origin
p("## F. Rainbow Line plate origin (lot 1 + lot 2)\n")
pl = pd.concat([fivemin("rl1"), fivemin("rl2")])
cols = [c for c in pl.columns if c not in ("t0", "t1", "count")]
daily = pl.set_index("t0")[cols].groupby(lambda t: t.normalize()).sum()
pref = daily.T.groupby(lambda c: c.rsplit(" ", 1)[0]).sum().T
kind = daily.T.groupby(lambda c: c.rsplit(" ", 1)[1]).sum().T
reg = pd.DataFrame({r: pref[[x for x in ps if x in pref]].sum(1) for r, ps in REGIONS.items()})
reg["Other"] = pref.sum(1) - reg.sum(1)
tot = pref.sum(1)
ok = tot > 0
t = daytype(tot.index)
sh = reg[ok].div(tot[ok], axis=0)
sh["RentACar"] = (kind["RentACar"] / tot)[ok]
sh["Commercial"] = (kind["CommercialVehicle"] / tot)[ok]
g = sh.groupby(t[ok].values).apply(lambda x: (x.mul(tot[ok][x.index], axis=0).sum() / tot[ok][x.index].sum()))
g.index.name = "day type"; p("Share of plates by origin region and kind, count-weighted:\n"); tbl(g)
mon = sh.groupby(sh.index.to_period("M")).apply(lambda x: (x.mul(tot[ok][x.index], axis=0).sum() / tot[ok][x.index].sum()))
mon["plates/day"] = tot[ok].groupby(tot[ok].index.to_period("M")).mean()
mon.index.name = "month"; p("By month:\n"); tbl(mon)
# busy days vs quiet days
q = tot[ok].quantile([.25, .75])
busy = sh[tot[ok] >= q[.75]].mean(); quiet = sh[tot[ok] <= q[.25]].mean()
bq = pd.DataFrame({"quiet days (bottom 25%)": quiet, "busy days (top 25%)": busy}); bq.index.name = "share"
p("Origin mix on quiet versus busy days (unweighted daily means):\n"); tbl(bq)

# G. lot 2 overflow
p("## G. Does lot 2 open as overflow?\n")
dd = D[["rl1", "rl2"]].dropna()
bins = pd.qcut(dd["rl1"], 5)
ov = dd.groupby(bins, observed=True).agg(days=("rl2", "size"), rl2_median=("rl2", "median"),
                                          rl2_share=("rl2", lambda x: (x / (x + dd.loc[x.index, "rl1"])).median()))
ov.index = ov.index.astype(str); ov.index.name = "lot 1 plates/day"; tbl(ov)

open("../out/20261011_cross_site_patterns.md", "w").write("\n".join(L))
print("\n".join(L))
