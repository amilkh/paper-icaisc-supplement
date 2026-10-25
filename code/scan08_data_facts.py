"""Data-section facts: outage runs, detections per official visitor, face share and face age mix.

Writes out/20261016_data_facts.md. Official Tojinbo visitors: Fukui Prefecture,
令和7年 福井県観光客入込数 (推計), 651 thousand in 2025 (delayed-count basis).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from common import daily_counts, load, FEEDS

OUT = Path(__file__).resolve().parent.parent / "out" / "20261016_data_facts.md"
TOJINBO_OFFICIAL_2025 = 651_000

lines = ["# Data-section facts (scan08)", ""]
dc = daily_counts()

# 1. Outage runs (NaN days after each feed's first valid day)
lines += ["## Outage days (zero total or fewer than 80% of 288 bins)", "",
          "| Feed | Valid days | Outage days | Runs of 2+ days |", "|---|---|---|---|"]
for k in FEEDS:
    s = dc[k]
    s = s[s.first_valid_index():]
    miss = s[s.isna()].index
    runs, start, prev = [], None, None
    for d in miss:
        if start is None:
            start = prev = d
        elif d == prev + pd.Timedelta(days=1):
            prev = d
        else:
            runs.append((start, prev)); start = prev = d
    if start is not None:
        runs.append((start, prev))
    txt = "; ".join(f"{a:%Y-%m-%d}" + (f" to {b:%Y-%m-%d} ({(b-a).days+1} d)" if b != a else "")
                    for a, b in runs if (b - a).days >= 1)
    lines.append(f"| {k} | {int(s.notna().sum())} | {len(miss)} | {txt or 'none'} |")

# 2. Tojinbo detections per officially reported visitor, calendar 2025
t = dc["tojinbo"]["2025-01-01":"2025-12-31"]
valid = t.notna().sum()
tot = t.sum()
scaled = tot * 365 / valid
lines += ["", "## Tojinbo detections per official visitor, 2025", "",
          f"Person detections on {valid} valid days: {tot:,.0f}; scaled to 365 days: {scaled:,.0f}.",
          f"Official 2025 visitors (Fukui Prefecture estimate): {TOJINBO_OFFICIAL_2025:,}.",
          f"Detections per visitor: {scaled / TOJINBO_OFFICIAL_2025:.2f} (unscaled {tot / TOJINBO_OFFICIAL_2025:.2f})."]

# 3. Face share of person detections and face age mix
lines += ["", "## Faces relative to person detections", "",
          "| Site | Person | Face | Face/Person | Age 6-12 share of faces | Age 65+ share |", "|---|---|---|---|---|---|"]
for k in ("station", "tojinbo"):
    site, _ = FEEDS[k]
    p = load("5min", site, "Person").set_index("t0")["count"]
    f = load("5min", site, "Face")
    f = f.set_index("t0")
    days = dc[k].dropna().index
    pd_ = p.groupby(p.index.normalize()).sum().reindex(days).sum()
    fd = f["count"].groupby(f.index.normalize()).sum().reindex(days).sum()
    age = {b: sum(f[c].sum() for c in f.columns if c.endswith(b)) for b in ("range06to12", "range65over")}
    ftot = sum(f[c].sum() for c in f.columns if "range" in c)
    lines.append(f"| {k} | {pd_:,.0f} | {fd:,.0f} | {fd / pd_:.3f} | {age['range06to12'] / ftot:.1%} | {age['range65over'] / ftot:.1%} |")

OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
