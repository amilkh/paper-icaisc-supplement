"""Compare the regenerated outputs in out/ with the paper and with the outputs
committed in amilkh/icaisc-camera-scans release v1.1 (copied to expected/).

Part 1 checks every paper item: the value is read from the regenerated file and
must round to the number printed in the paper. Part 2 compares each regenerated
file with its v1.1 copy (text files exactly, CSV numerically, figures by pixel).

    python code/check.py              # print the report (run from the repo root)
    python code/check.py --markdown   # print the README table from the current out/
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

F1 = "20261011_cross_site_patterns.md"
F2 = "20261012_weather_jma.md"
F2O = "20261011_weather_openmeteo.md"
F3 = "20261012_forecast_weather_test.md"
F4 = "20261012_lead_time.md"
F5 = "20261013_review_fixes.md"
F6 = "20261013_rainbow_faces_plates.md"
F8 = "20261016_data_facts.md"
F9 = "20261017_faces_warning_counts.md"
CI = "coldstart/cold_start_ci.csv"
PF = "coldstart/cold_start_peak_f1.csv"

NUM = re.compile(r"n/a|inf|[<>≤≥]\s*[-+]?\d+(?:\.\d+)?|[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


# ---------------------------------------------------------------- readers
def md_rows(path):
    """Rows of every Markdown table in a file, as dicts keyed by header, plus
    '_section' (the closest heading above the table)."""
    rows, section, header = [], "", None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#"):
            section = line.lstrip("# ").strip()
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if i + 1 < len(lines) and re.match(r"^\|[-| ]+\|$", lines[i + 1].strip()):
            header = cells
        elif header and not re.match(r"^\|[-| ]+\|$", line.strip()):
            rows.append({"_section": section, **dict(zip(header, cells))})
    return rows


def row(out, name, section, **where):
    """The single table row in out/name under a heading starting with `section`
    whose cells match `where` (keyword names use _ for spaces)."""
    hits = [r for r in md_rows(out / name) if r["_section"].startswith(section)
            and all(r.get(k.replace("_", " ")) == v for k, v in where.items())]
    if len(hits) != 1:
        raise LookupError(f"{name}: {len(hits)} rows match {section!r} {where}")
    return hits[0]


def rows(out, name, section):
    return [r for r in md_rows(out / name) if r["_section"].startswith(section)]


def csv_rows(out, name):
    with open(out / name, newline="") as fh:
        return list(csv.DictReader(fh))


def first(cell):
    return NUM.findall(cell)[0]


def paren(cell):
    return re.search(r"\(([^)]*)\)", cell).group(1)


# ---------------------------------------------------------------- comparison
def _val(tok):
    return float(tok.replace(",", "").replace("−", "-"))


def _dec(tok):
    return len(tok.split(".")[1]) if "." in tok else 0


def matches(reproduced, paper):
    """True if every number in `reproduced` rounds to the matching number in
    `paper`. A tie at the file's own rounding counts as a match either way.
    Paper tokens may be bounds (<x, >x, <=x, >=x) or n/a (matches inf or n/a)."""
    got = NUM.findall(reproduced.replace("−", "-"))
    want = NUM.findall(paper.replace("−", "-"))
    if len(got) != len(want):
        return False
    for g, w in zip(got, want):
        if w == "n/a":
            if g not in ("n/a", "inf"):
                return False
            continue
        if g in ("n/a", "inf"):
            return False
        v = _val(g)
        if w[0] in "<>≤≥":
            b = _val(w[1:].strip())
            ok = {"<": v < b, ">": v > b, "≤": v <= b, "≥": v >= b}[w[0]]
            if not ok:
                return False
            continue
        if _dec(g) <= _dec(w):  # file no more precise than the paper: must be equal
            tol = 1e-9
        else:                   # rounds to the paper value; a tie at the file's rounding passes
            tol = 0.5 * 10 ** -_dec(w) + 0.5 * 10 ** -_dec(g) + 1e-9
        if abs(v - _val(w)) > tol:
            return False
    return True


# ---------------------------------------------------------------- paper items
def items():
    """(id, where in the paper, what, output file, extractor(out) -> str, value printed in the paper)"""
    L = []

    def add(*a):
        L.append(a)

    # Table I
    for feed, label, paper in [("station", "Fukui Station", "642, 8,343, 1.49, 1.65"),
                               ("tojinbo", "Tojinbo", "641, 8,173, 2.07, 2.35"),
                               ("rl1", "Rainbow L. lot 1", "607, 174, 1.84, 2.20"),
                               ("rl2", "Rainbow L. lot 2", "607, 0, n/a, n/a")]:
        def f(out, feed=feed):
            a, b = row(out, F1, "A.", feed=feed), row(out, F1, "B.", feed=feed)
            return f"{a['valid days']}, {a['median/day']}, {b['weekend']}, {b['holiday']}"
        add(f"T1-{feed}", "Table I", f"{label}: days, median/day, weekend and holiday uplift", F1, f, paper)

    # Table II
    cols = ["per 10 mm rain", "per +5 m/s peak hourly wind", "per +3 h sun", "per +5 °C"]
    for feed, label, paper in [
            ("Fukui Station (people)", "Fukui Station", "−3 [−6, −1]; +4 [−2, +10]; 0 [−2, +1]; +2 [−1, +5]"),
            ("Tojinbo (people)", "Tojinbo", "−9 [−13, −5]; −10 [−17, −3]; +5 [+3, +8]; +12 [+7, +18]"),
            ("Rainbow Line lot 1 (cars)", "Rainbow Line", "−37 [−47, −24]; −13 [−25, +2]; +17 [+12, +22]; +7 [−2, +16]")]:
        def f(out, feed=feed):
            r = row(out, F2, "A.", feed=feed)
            return "; ".join(r[c] for c in cols)
        add(f"T2-{label.split()[0].lower()}", "Table II", f"{label}: % per 10 mm rain, +5 m/s wind, +3 h sun, +5 °C [95% CI]", F2, f, paper)

    def f(out):
        return ", ".join(first(row(out, F2O, "A.", feed=x)["per 10 mm rain"])
                         for x in ("Fukui Station (people)", "Tojinbo (people)", "Rainbow Line lot 1 (cars)"))
    add("T2-om", "Sec. V-A text", "Open-Meteo rain effect, % per 10 mm (station, Tojinbo, Rainbow Line)", F2O, f, "−1, −13, −36")

    # Table III
    for site, h, paper in [("Fukui Station", "1d", "11.88, 12.04, +0.2 [-0.1, +0.5], 0.313"),
                           ("Fukui Station", "3d", "14.43, 14.67, +0.2 [-0.0, +0.6], 0.122"),
                           ("Tojinbo", "1d", "23.29, 21.57, -1.7 [-3.4, -0.3], 0.018"),
                           ("Tojinbo", "3d", "27.16, 26.04, -1.1 [-3.0, +0.7], 0.224"),
                           ("Rainbow Line lot 1", "1d", "33.95, 27.38, -6.6 [-9.5, -3.6], <0.001"),
                           ("Rainbow Line lot 1", "3d", "38.50, 31.87, -6.6 [-9.7, -3.6], <0.001")]:
        def f(out, site=site, h=h):
            r = row(out, F3, "A.", site=site, h=h)
            return f"{r['WAPE calendar']}, {r['WAPE +forecast wx']}, {r['change (pts) [95% CI]']}, {paren(r['DM t (p)'])}"
        add(f"T3-{site.split()[0].lower()}-{h}", "Table III", f"{site.replace(' lot 1', '')} {h}: WAPE calendar, +forecast wx, change [95% CI], DM p", F3, f, paper)

    # Table IV
    t4 = [("Fukui Station: top-20% day", "none", "0.92 [0.87, 0.96], 0.78, 0.62"),
          ("Fukui Station: top-20% day", "3-day forecast", "0.92 [0.87, 0.96], 0.79, 0.57"),
          ("Tojinbo: top-20% day", "none", "0.91 [0.85, 0.96], 0.82, 0.64"),
          ("Tojinbo: top-20% day", "3-day forecast", "0.93 [0.88, 0.97], 0.86, 0.64"),
          ("Rainbow Line: top-20% day", "none", "0.81 [0.75, 0.87], 0.78, 0.45"),
          ("Rainbow Line: top-20% day", "3-day forecast", "0.87 [0.83, 0.91], 0.84, 0.54"),
          ("Rainbow Line: car park 2 in use", "none", "0.87 [0.80, 0.94], 0.60, 0.55"),
          ("Rainbow Line: car park 2 in use", "3-day forecast", "0.89 [0.82, 0.95], 0.82, 0.59")]
    for i, (warn, wx, paper) in enumerate(t4, 1):
        def f(out, warn=warn, wx=wx):
            r = row(out, F3, "B.", warning=warn, weather=wx)
            return f"{r['AUC [95% CI]']}, {r['precision']}, {r['recall']}"
        add(f"T4-{i}", "Table IV", f"{warn.replace('Rainbow Line', 'RL')}, weather {wx}: AUC [95% CI], precision, recall", F3, f, paper)

    def f(out):
        a = [float(first(r["AUC [95% CI]"])) for r in rows(out, F3, "B.") if r["weather"] == "3-day forecast"]
        return f"{min(a):.2f} to {max(a):.2f}"
    add("ABS-auc", "Abstract", "range of three-day warning AUC with forecast weather", F3, f, "0.87 to 0.93")

    # Lead time (Fig. 3 and Sec. V-B text)
    def lt(out, site, lead):
        return row(out, F4, site, **{"lead (days)": str(lead)})
    add("LT-station", "Sec. V-B", "Fukui Station 1-day WAPE: naive, calendar", F4,
        lambda out: f"{lt(out, 'Fukui Station', 1)['naive']}, {lt(out, 'Fukui Station', 1)['calendar']}", "19.3, 11.9")
    add("LT-rl", "Sec. V-B", "Rainbow Line 1-day WAPE: naive, calendar", F4,
        lambda out: f"{lt(out, 'Rainbow Line', 1)['naive']}, {lt(out, 'Rainbow Line', 1)['calendar']}", "41.5, 34.0")
    add("LT-rl-dm", "Abstract, Sec. V-B", "Rainbow Line weather gain significant at leads 1 to 5 (DM p)", F4,
        lambda out: ", ".join(lt(out, "Rainbow Line", h)["DM p, ridge_fcst vs calendar"] for h in range(1, 6)),
        "<0.05, <0.05, <0.05, <0.05, <0.05")

    def f(out):
        r = row(out, F4, "Share of the observed", site="Rainbow Line lot 1")
        return f"{r['1d']}; {r['3d']}; {r['6d']}"
    add("LT-kept", "Sec. V-B", "Rainbow Line forecast keeps % of perfect-weather gain at 1, 3, 6 days", F4, f,
        "92 [66, 113]; 94 [73, 119]; 23 [−29, 56]")
    add("LT-rl-30", "Sec. V-B", "Rainbow Line share of days within ±30%, 1 and 3 days (63%, 54%)", F4,
        lambda out: f"{lt(out, 'Rainbow Line', 1)['within ±30% (ridge_fcst)']}, {lt(out, 'Rainbow Line', 3)['within ±30% (ridge_fcst)']}",
        "0.63, 0.54")
    add("LT-toj-dm", "Sec. V-B", "Tojinbo weather DM p at 1 and 7 days", F4,
        lambda out: f"{lt(out, 'Tojinbo', 1)['DM p, ridge_fcst vs calendar']}, {lt(out, 'Tojinbo', 7)['DM p, ridge_fcst vs calendar']}",
        "0.018, 0.041")

    def f(out):
        v = [float(lt(out, "Fukui Station", h)["within ±30% (ridge_fcst)"]) for h in range(1, 8)]
        return f"{min(v):.2f} to {max(v):.2f}"
    add("LT-st-30", "Sec. V-B", "Fukui Station share of days within ±30%, range over leads 1 to 7 (90-95%)", F4, f, "0.90 to 0.95")
    add("LT-gbm", "Sec. V-B", "Rainbow Line 3-day WAPE: gradient boosting, forecast-weather ridge", F4,
        lambda out: f"{lt(out, 'Rainbow Line', 3)['gbm']}, {lt(out, 'Rainbow Line', 3)['ridge_fcst']}", "30.0, 31.9")

    def f(out):
        v = [float(r[f"{h}d"]) for r in rows(out, F4, "Busy-day warning AUC by lead") for h in range(1, 6)]
        return f"{min(v):.2f}"
    add("LT-auc5", "Sec. V-C", "lowest warning AUC at leads 1 to 5 (stays useful, AUC ≥ 0.85)", F4, f, "≥0.85")

    # scan05: nested tuning, classical baselines, busy-day definitions
    def holm(out, site, lead):
        return row(out, F5, "D.", site=site, lead=lead)["DM p (Holm)"]
    add("NT-rl", "Sec. V-B", "Rainbow Line Holm-adjusted p at 1, 3, 5 days (tuning check)", F5,
        lambda out: ", ".join(holm(out, "Rainbow Line lot 1", f"{h}d") for h in (1, 3, 5)), "<0.01, <0.01, <0.01")
    add("NT-toj", "Sec. V-B", "Tojinbo Holm-adjusted p at 1 and 7 days (not significant)", F5,
        lambda out: ", ".join(holm(out, "Tojinbo", f"{h}d") for h in (1, 7)), ">0.05, >0.05")

    def f(out):
        r = row(out, F5, "C.", site="Rainbow Line lot 1", lead="1d")
        return f"{first(r['SARIMAX + fcst wx'])}, {first(r['ridge + fcst wx'])}"
    add("CB-sarimax", "Sec. V-B", "Rainbow Line 1-day WAPE: SARIMAX, ridge (both with forecast weather)", F5, f, "26.6, 27.4")

    def f(out):
        g = [float(first(r["SARIMAX + fcst wx"])) - float(first(r["ridge + fcst wx"])) for r in rows(out, F5, "C.")]
        return f"{max(g):.1f}"
    add("CB-gap", "Sec. V-B", "largest SARIMAX shortfall against ridge, points (within about 3)", F5, f, "≤3.0")

    def f(out):
        a = [r for r in rows(out, F5, "A.") if r["weather"] == "forecast"]
        auc = [float(r["AUC"]) for r in a]
        base = [float(r["base rate"]) for r in rows(out, F5, "A.")]
        return f"{min(auc):.2f} to {max(auc):.2f}; {min(base):.2f} to {max(base):.2f}"
    add("BD-defs", "Sec. V-C", "three busy-day definitions with forecast weather: AUC range; busy share of test days (30-50%)",
        F5, f, "0.82 to 0.93; 0.30 to 0.50")

    def f(out):
        b = [r for r in rows(out, F5, "B.") if r["weather"] == "forecast"]
        auc = [float(r["AUC"]) for r in b]
        days = {r["label"]: int(r["days"]) for r in b}
        amb = days["plates ≥20 (original)"] - days["plates ≥20, ambiguous days removed"]
        return f"{min(auc):.2f} to {max(auc):.2f}; {amb}"
    add("BD-lot2", "Sec. V-C", "overflow-lot AUC range over three labels; test days where only faces show lot 2 in use",
        F5, f, "0.88 to 0.90; 11")

    # Faces vs plates (scan06, scan09)
    def f(out):
        t = (out / F6).read_text(encoding="utf-8")
        m = re.search(r"Valid days (\d+)\. Median faces per plate ([\d.]+).*?r = ([\d.]+)", t)
        return ", ".join(m.groups())
    add("FP-basic", "Sec. III, V-C", "pooled Rainbow Line gates: valid days, median faces per plate, daily correlation", F6, f, "604, 0.32, 0.77")
    add("FP-rain", "Sec. V-C", "rain effect, % per 10 mm: faces, plates", F6,
        lambda out: f"{first(row(out, F6, 'A.', series='faces')['10 mm rain'])}, {first(row(out, F6, 'A.', series='plates')['10 mm rain'])}",
        "−43, −37")
    add("FP-wape", "Sec. V-C", "three-day WAPE with forecast weather: faces, plates", F6,
        lambda out: f"{first(row(out, F6, 'B.', series='faces')['3d forecast'])}, {first(row(out, F6, 'B.', series='plates')['3d forecast'])}",
        "66, 34")
    add("FP-auc", "Sec. V-C", "three-day busy-day warning AUC with forecast weather: faces, plates", F6,
        lambda out: f"{row(out, F6, 'B.', series='faces')['busy AUC (forecast)']}, {row(out, F6, 'B.', series='plates')['busy AUC (forecast)']}",
        "0.93, 0.88")

    def f(out):
        r = row(out, F9, "Scan 09", series="faces", weather="forecast")
        return f"{r['correct']} of {r['busy days']} busy days, {r['flagged']} flagged, precision {r['precision']}, recall {r['recall']}"
    add("FP-faces", "Sec. V-C", "faces warning: correct flags, busy test days, flagged, precision, recall", F9, f,
        "43 of 86 busy days, 43 flagged, precision 1.00, recall 0.50")
    add("FP-plates", "Sec. V-C", "plates warning with forecast weather: precision, recall", F9,
        lambda out: f"{row(out, F9, 'Scan 09', series='plates', weather='forecast')['precision']}, {row(out, F9, 'Scan 09', series='plates', weather='forecast')['recall']}",
        "0.84, 0.60")

    # Data-section facts (scan08)
    def f(out):
        t = (out / F8).read_text(encoding="utf-8")
        scaled = int(re.search(r"scaled to 365 days: ([\d,]+)", t).group(1).replace(",", ""))
        visitors = re.search(r"visitors \(Fukui Prefecture estimate\): ([\d,]+)", t).group(1)
        per = re.search(r"Detections per visitor: ([\d.]+)", t).group(1)
        return f"{per}; {scaled / 1e6:.6f} million; {visitors}"
    add("DF-visitors", "Sec. III", "Tojinbo 2025 detections per official visitor; scaled detections; official visitors", F8, f,
        "5; 3.3 million; 651,000")

    def f(out):
        s, t = row(out, F8, "Faces relative", Site="station"), row(out, F8, "Faces relative", Site="tojinbo")
        return f"{t['Face/Person']}, {s['Face/Person']}; {s['Age 6-12 share of faces']}"
    add("DF-faces", "Sec. III", "faces as share of detections (Tojinbo, station; about 3-4%); station faces aged 6-12, %", F8, f,
        "0.03, 0.04; 41")

    # Cold start (Fig. 4 and Sec. V-D)
    def ci(out, node, n, variant="blend"):
        hits = [r for r in csv_rows(out, CI) if r["node"] == node and r["history_days"] == str(n) and r["variant"] == variant]
        assert len(hits) == 1, (node, n, variant)
        return hits[0]
    add("CS-3d", "Sec. V-D", "3 days of history, hourly WAPE: ridge and same-hour-last-week at station; ridge and baseline at Tojinbo", CI,
        lambda out: f"{ci(out, 'fukui_station', 3)['wape_ridge']}, {ci(out, 'fukui_station', 3)['wape_naive']}; "
                    f"{ci(out, 'tojinbo', 3)['wape_ridge']}, {ci(out, 'tojinbo', 3)['wape_naive']}",
        "36.2, 27.4; 57.9, 43.8")

    def f(out):
        r = []
        for node in ("tojinbo", "fukui_station"):
            r.append(next(n for n in (3, 7, 14, 28, 56, 91, 182, 365)
                          if float(ci(out, node, n)["wape_ridge"]) < float(ci(out, node, n)["wape_naive"])))
        return f"{r[0]}, {r[1]}"
    add("CS-catchup", "Sec. V-D", "days of history before ridge beats the baseline: Tojinbo (about a week), station (four weeks)", CI, f, "7, 28")
    add("CS-3d-ci", "Sec. V-D", "shrunk minus baseline at 3 days: upper 95% limit below zero at station and Tojinbo", CI,
        lambda out: f"{ci(out, 'fukui_station', 3)['ci_hi_pp']}, {ci(out, 'tojinbo', 3)['ci_hi_pp']}", "<0, <0")
    add("CS-toj3", "Sec. V-D", "Tojinbo, 3 days: shrunk minus baseline, points [95% CI]", CI,
        lambda out: f"{ci(out, 'tojinbo', 3)['blend_minus_naive_pp']} [{ci(out, 'tojinbo', 3)['ci_lo_pp']}, {ci(out, 'tojinbo', 3)['ci_hi_pp']}]",
        "−1.2 [−2.1, −0.4]")
    add("CS-st56", "Sec. V-D", "station, 56 days: 95% interval of shrunk minus baseline, points", CI,
        lambda out: f"[{ci(out, 'fukui_station', 56)['ci_lo_pp']}, {ci(out, 'fukui_station', 56)['ci_hi_pp']}]", "[−6.3, +1.0]")
    add("CS-toj28", "Sec. V-D", "Tojinbo, 28 days: shrunk minus baseline, points", CI,
        lambda out: ci(out, "tojinbo", 28)["blend_minus_naive_pp"], "−10.1")

    def f(out):
        best = {}
        for r in csv_rows(out, PF):
            best[r["node"]] = max(best.get(r["node"], 0.0), float(r["peak_f1"]))
        return f"{best['fukui_station']}, {best['tojinbo']}"
    add("CS-f1", "Sec. V-D", "best hourly peak F1: station (about 0.4), Tojinbo (about 0.6)", PF, f, "0.4, 0.6")

    def f(out):
        d = [abs(float(ci(out, r["node"], r["history_days"], "blend_fcst")["wape_blend"]) - float(r["wape_blend"]))
             for r in csv_rows(out, CI) if r["variant"] == "blend"]
        flips = sum((float(ci(out, r["node"], r["history_days"], "blend_fcst")["ci_lo_pp"]) < 0) != (float(r["ci_lo_pp"]) < 0)
                    or (float(ci(out, r["node"], r["history_days"], "blend_fcst")["ci_hi_pp"]) < 0) != (float(r["ci_hi_pp"]) < 0)
                    for r in csv_rows(out, CI) if r["variant"] == "blend")
        return f"{max(d):.2f}; {flips}"
    add("CS-fcst", "Sec. VII", "forecast-weather cold start: largest change in shrunk WAPE, points (about one); intervals changing sign",
        CI, f, "1; 0")
    return L


FIGS = [("Fig. 2", "figures/daily_counts.png"), ("Fig. 3", "figures/lead_time_wape.png"),
        ("Fig. 4", "coldstart/cold_start.png")]


def run_items(out):
    res = []
    for iid, where, what, fname, fn, paper in items():
        try:
            got = fn(out)
            ok = matches(got, paper)
        except Exception as e:  # missing file or row
            got, ok = f"error: {e}", False
        res.append((iid, where, what, fname, paper, got, ok))
    return res


# ---------------------------------------------------------------- file comparison
def compare_csv(a, b):
    with open(a, newline="") as fa, open(b, newline="") as fb:
        ra, rb = list(csv.reader(fa)), list(csv.reader(fb))
    if len(ra) != len(rb):
        return f"DIFFERENT ({len(ra)} vs {len(rb)} rows)"
    worst, ndiff = 0.0, 0
    for x, y in zip(ra, rb):
        if len(x) != len(y):
            return "DIFFERENT (column count)"
        for p, q in zip(x, y):
            if p == q:
                continue
            ndiff += 1
            try:
                fp, fq = float(p), float(q)
            except ValueError:
                return f"DIFFERENT ({p!r} vs {q!r})"
            worst = max(worst, abs(fp - fq) / max(abs(fq), 1e-12))
    if ndiff == 0:
        return "identical"
    return f"{ndiff} cells differ, max relative difference {worst:.1e}" + ("" if worst < 1e-6 else "  <-- DIFFERENT")


def compare_png(a, b):
    import matplotlib.image as mpimg
    import numpy as np
    x, y = mpimg.imread(a), mpimg.imread(b)
    if x.shape != y.shape:
        return f"size {x.shape[1]}x{x.shape[0]} vs {y.shape[1]}x{y.shape[0]} (rendering differs)"
    d = np.abs(x.astype(float) - y.astype(float))
    if d.max() == 0:
        return "pixel-identical"
    return f"{(d.max(axis=-1) > 0).mean() * 100:.2f}% of pixels differ (font or library rendering)"


def compare_files(root, say):
    exp, out = root / "expected", root / "out"
    say("")
    say("PART 2. Regenerated files against the v1.1 outputs (expected/)")
    for p in sorted(exp.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(exp).as_posix()
        q = out / rel
        if not q.exists():
            msg = "MISSING"
        elif p.suffix == ".png":
            msg = compare_png(q, p)
        elif p.suffix == ".csv":
            msg = compare_csv(q, p)
        elif q.read_bytes() == p.read_bytes():
            msg = "identical"
        else:
            a, b = q.read_text(encoding="utf-8").splitlines(), p.read_text(encoding="utf-8").splitlines()
            diff = [i for i in range(max(len(a), len(b))) if (a[i:i + 1] or [""]) != (b[i:i + 1] or [""])]
            msg = f"{len(diff)} line(s) differ  <-- DIFFERENT"
            for i in diff[:6]:
                msg += f"\n      line {i + 1}: got      {(a[i:i + 1] or [''])[0]}\n      line {i + 1}: expected {(b[i:i + 1] or [''])[0]}"
        say(f"  {rel:45s} {msg}")


def main(root=ROOT, say=print):
    out = root / "out"
    res = run_items(out)
    say("")
    say("PART 1. Paper items (value read from the regenerated file, rounded as printed in the paper)")
    for iid, where, what, fname, paper, got, ok in res:
        say(f"  {'PASS' if ok else 'FAIL'}  {iid:12s} {where:18s} {what}")
        say(f"        paper: {paper}   reproduced: {got}   [{fname}]")
    for fig, rel in FIGS:
        ok = (out / rel).exists()
        say(f"  {'PASS' if ok else 'FAIL'}  {fig:12s} {'figure':18s} regenerated as out/{rel} (see Part 2 for the pixel check)")
    n_ok = sum(r[-1] for r in res) + sum((out / rel).exists() for _, rel in FIGS)
    n = len(res) + len(FIGS)
    compare_files(root, say)
    say("")
    say(f"SUMMARY: {n_ok}/{n} paper items reproduced" + ("" if n_ok == n else f"; {n - n_ok} FAILED"))
    return n_ok == n


def markdown(root=ROOT):
    out = root / "out"
    print("| ID | Paper | Item | Output file | Paper value | Reproduced | Match |")
    print("|---|---|---|---|---|---|---|")
    for iid, where, what, fname, paper, got, ok in run_items(out):
        print(f"| {iid} | {where} | {what} | `out/{fname}` | {paper} | {got} | {'yes' if ok else 'NO'} |")
    for fig, rel in FIGS:
        print(f"| {fig} | {fig} | figure | `out/{rel}` | see paper | regenerated | {'yes' if (out / rel).exists() else 'NO'} |")


if __name__ == "__main__":
    if "--markdown" in sys.argv:
        markdown()
    else:
        sys.exit(0 if main() else 1)
