"""Scan 9: day counts behind the faces vs plates busy-day warning at Rainbow Line
(lots 1+2, paper outage rule), three days ahead with forecast weather. Same series
and model as the faces table in scan07, plus the number of busy test days and of
days the warning flagged, so the precision of 1.00 can be read as a count.
Needs no JMA data. Writes ../out/20261017_faces_warning_counts.md.
"""
import numpy as np
import pandas as pd
import scan03 as s3
from common import load

L = []
def p(x=""): L.append(x); print(x, flush=True)

def daily(site, cls):
    d = load("5min", site, cls).set_index("t0")["count"]; g = d.groupby(d.index.normalize()); tot, n = g.sum(), g.size(); tot[n < 0.8 * 288] = np.nan; return tot

S1, S2 = "rainbow-line-parking-lot-1-gate", "rainbow-line-parking-lot-2-gate"
p1, p2, f1, f2 = daily(S1, "LicensePlate"), daily(S2, "LicensePlate"), daily(S1, "Face"), daily(S2, "Face")
idx = p1.index.union(p2.index).union(f1.index).union(f2.index); p1, p2, f1, f2 = (s.reindex(idx) for s in (p1, p2, f1, f2))
lot1_on = p1 > 0
series = {"plates": (p1 + p2).where(lot1_on), "faces": (f1 + f2).where(lot1_on)}
orig = s3.D.copy(); rows = []
for name, ser in series.items():
    s3.D = orig.copy(); s3.D["rl1"] = ser.asfreq("D")
    for mode in ["calendar", "forecast"]:
        r = s3.busy_eval("rl1", "top", mode, h=3)
        rows.append({"series": name, "weather": mode, "test days": r["days"], "busy days": r["busy days"],
                     "flagged": r["flagged"], "correct": round(r["precision"] * r["flagged"]),
                     "precision": f"{r['precision']:.2f}", "recall": f"{r['recall']:.2f}"})
s3.D = orig

p("# Scan 09: faces vs plates busy-day warning at Rainbow Line, as day counts\n")
p("Lots 1+2, paper outage rule, three days ahead, rolling top-20% threshold, logistic regression as in scan03. "
  "Flagged = days with predicted probability >= 0.5; correct = flagged days that were busy.\n")
cols = list(rows[0])
p("| " + " | ".join(cols) + " |"); p("|" + "---|" * len(cols))
for r in rows:
    p("| " + " | ".join(str(r[c]) for c in cols) + " |")
p()
open("../out/20261017_faces_warning_counts.md", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
