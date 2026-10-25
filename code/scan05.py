"""Scan 5: answers to the 12 Oct review.
A. Busy-day warnings under three busy definitions, with base rates, lift and Brier score.
B. Car park 2 label robustness (ambiguous gate-2 days).
C. Classical baselines: ETS and SARIMAX (with forecast weather) at leads 1, 3, 7.
D. Nested evaluation: tune on the first half of the test year, report on the second; Holm-adjusted DM.
E. Figures for the paper.
Writes ../out/20261013_review_fixes.md and ../out/figures/*.
"""
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, roc_auc_score
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.multitest import multipletests
import scan03 as s3
from common import fivemin

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent.parent / "out"
FIG = OUT / "figures"; FIG.mkdir(parents=True, exist_ok=True)
L = []
def p(x=""): L.append(x); print(x, flush=True)
def tbl(df, fmt="{:.2f}"):
    cols = [str(c) for c in df.columns]
    p("| " + " | ".join([df.index.name or ""] + cols) + " |"); p("|" + "---|" * (len(cols) + 1))
    for i, r in df.iterrows():
        p("| " + " | ".join([str(i)] + [fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r]) + " |")
    p()

START, END = s3.START, pd.Timestamp("2026-10-10")
MID = START + pd.Timedelta(weeks=26)

# ---------- A. busy-day definitions ----------
def labels(f, cutoff, kind):
    y = f["y"]; tr = y[(y.index < cutoff)].dropna()
    if kind == "rolling top 20%":       # threshold from all data before the cutoff (original)
        thr = tr.quantile(0.8); return (y >= thr).where(y.notna())
    if kind == "fixed first-year top 20%":  # threshold frozen at the start of the test year
        thr = y[y.index < START].dropna().quantile(0.8); return (y >= thr).where(y.notna())
    if kind == "same-month top 20%":    # seasonal: top 20% within each calendar month of training data
        q = tr.groupby(tr.index.month).quantile(0.8)
        thr = pd.Series(y.index.month.map(q), index=y.index)
        return (y >= thr).where(y.notna() & thr.notna())
    raise ValueError(kind)

def warn_eval(k, label_fn, h, weather, exclude=None):
    f = s3.frame(k)
    obs = f[s3.WX]
    Xtr = s3.design(f, h, obs if weather else None)
    Xte = s3.design(f, h, s3.forecast_weather(s3.WX_SITE[k], h) if weather else None)
    probs, labs = [], []
    for monday in pd.date_range(START, END, freq="W-MON"):
        cutoff = monday - pd.Timedelta(days=h)
        lab = label_fn(f, cutoff)
        if exclude is not None:
            lab = lab.where(~lab.index.isin(exclude))
        tr = (Xtr.index < cutoff) & Xtr.notna().all(1) & lab.notna()
        if lab[tr].nunique() < 2:
            continue
        mdl = LogisticRegression(max_iter=3000).fit(Xtr[tr], lab[tr].astype(int))
        idx = f.loc[monday: monday + pd.Timedelta(days=6)].index
        te = Xte.loc[idx].notna().all(1) & lab.loc[idx].notna()
        if te.any():
            probs.append(pd.Series(mdl.predict_proba(Xte.loc[idx][te])[:, 1], index=idx[te]))
            labs.append(lab.loc[idx][te])
    pr, yb = pd.concat(probs), pd.concat(labs).astype(int)
    hit = pr >= 0.5; tp = (hit & (yb == 1)).sum()
    prec = tp / max(hit.sum(), 1); base = yb.mean()
    return {"days": len(yb), "base rate": base, "AUC": roc_auc_score(yb, pr), "precision": prec,
            "recall": tp / max(yb.sum(), 1), "lift": prec / base if base else np.nan,
            "Brier": brier_score_loss(yb, pr), "Brier (climatology)": brier_score_loss(yb, np.full(len(yb), base))}, pr, yb

p("# Review fixes (scan 05)\n")
p("Test year 2025-10-13 to 2026-10-10, rolling origin with weekly refits; weather at test time is the archived Open-Meteo forecast issued h days before. *Lift* = precision ÷ base rate. *Brier (climatology)* is the score of always predicting the base rate; lower is better.\n")
p("## A. Busy-day warnings under three definitions (3 days ahead)\n")
rows = []
for k in s3.FEEDS:
    for kind in ["rolling top 20%", "fixed first-year top 20%", "same-month top 20%"]:
        for wx in [False, True]:
            r, _, _ = warn_eval(k, lambda f, c, kind=kind: labels(f, c, kind), 3, wx)
            rows.append({"site": s3.NAMES[k], "definition": kind, "weather": "forecast" if wx else "none", **r})
A = pd.DataFrame(rows).set_index("site"); tbl(A)
A.to_csv(OUT / "20261013_busy_definitions.csv")

# ---------- B. car park 2 robustness ----------
p("## B. Car park 2 warning: label robustness (3 days ahead)\n")
plates2 = s3.D["rl2"]
f2 = fivemin("rl2").set_index("t0")["count"]  # plates at gate 2 (5-min)
faces2 = pd.read_parquet(s3.DATA / "5min_rainbow-line-parking-lot-2-gate_Face.parquet").set_index("t0")["count"]
faces2 = faces2.groupby(faces2.index.normalize()).sum()
amb = faces2[(faces2 >= 20) & (plates2.reindex(faces2.index) < 20)].index
p(f"Ambiguous days (≥20 faces but <20 plates at gate 2): {len(amb)}; on those days lot 1 median = {s3.D['rl1'].reindex(amb).median():.0f} cars, against {s3.D['rl1'][plates2 >= 20].median():.0f} on overflow days.\n")
def lot2_plates(f, c): return (plates2 >= 20).reindex(f.index).where(plates2.reindex(f.index).notna())
def lot2_either(f, c):
    pl = plates2.reindex(f.index); fa = faces2.reindex(f.index)
    return ((pl >= 20) | (fa >= 20)).where(pl.notna())
rows = []
for name, fn, ex in [("plates ≥20 (original)", lot2_plates, None), ("plates ≥20, ambiguous days removed", lot2_plates, amb),
                     ("plates or faces ≥20", lot2_either, None)]:
    for wx in [False, True]:
        r, _, _ = warn_eval("rl1", fn, 3, wx, exclude=ex)
        rows.append({"label": name, "weather": "forecast" if wx else "none", **r})
B = pd.DataFrame(rows).set_index("label"); tbl(B)

# ---------- C. classical baselines, true h-day lead (method by Mohammed Sohail, 14 Oct) ----------
p("## C. Classical baselines with a true h-day lead (WAPE %, within ±30% in brackets)\n")
p("ETS: Holt-Winters on log(1+y), additive weekly seasonality, damped additive trend. SARIMAX(1,0,1)(1,0,1)7 on log(1+y) with forecast weather as exogenous inputs. Parameters are refit weekly on data before the Monday cutoff; for each target day the fitted model is then run over counts up to d-h and forecasts exactly h steps, as ridge does. SARIMAX receives the weather forecast issued at d-h for each future day; days with a missing forecast are skipped. Training gaps are interpolated.\n")
DAY = pd.Timedelta(days=1)
def ets_known(series, res):
    """Run Holt-Winters with the weekly fit's parameters and initial states over a longer series."""
    pr = res.params
    m = ExponentialSmoothing(series, trend="add", damped_trend=True, seasonal="add", seasonal_periods=7,
                             initialization_method="known", initial_level=pr["initial_level"],
                             initial_trend=pr["initial_trend"], initial_seasonal=pr["initial_seasons"])
    return m.fit(smoothing_level=pr["smoothing_level"], smoothing_trend=pr["smoothing_trend"],
                 smoothing_seasonal=pr["smoothing_seasonal"], damping_trend=pr["damping_trend"], optimized=False)


def classical(k, h, kind):
    f = s3.frame(k); ly = f["ly"].asfreq("D"); obs = f[s3.WX].asfreq("D")
    fc = {j: s3.forecast_weather(s3.WX_SITE[k], j).reindex(ly.index) for j in range(1, h + 1)}
    preds = {}
    for monday in pd.date_range(START, END, freq="W-MON"):
        fit_end = monday - pd.Timedelta(days=h) - DAY          # same training data as scan05
        hist = ly[:fit_end].interpolate(limit_direction="both")
        try:
            if kind == "ets":
                res = ExponentialSmoothing(hist.values, trend="add", damped_trend=True, seasonal="add",
                                           seasonal_periods=7).fit()
            else:
                ex = obs.loc[hist.index].interpolate(limit_direction="both").values
                res = SARIMAX(hist.values, exog=ex, order=(1, 0, 1), seasonal_order=(1, 0, 1, 7),
                              trend="c").fit(disp=False, maxiter=200)
        except Exception:
            continue
        for d in pd.date_range(monday, monday + pd.Timedelta(days=6)):
            if d > END:
                break
            avail = ly[:d - pd.Timedelta(days=h)].interpolate(limit_direction="both")   # known at issue time
            try:
                if kind == "ets":
                    fcv = ets_known(avail.values, res).forecast(h)
                else:
                    fut = pd.date_range(avail.index[-1] + DAY, periods=h)
                    exf = pd.DataFrame([fc[j].loc[t] for j, t in zip(range(1, h + 1), fut)])
                    if exf.isna().any().any():
                        continue
                    exh = obs.loc[avail.index].interpolate(limit_direction="both").values
                    fcv = res.apply(avail.values, exog=exh).forecast(h, exog=exf.values)
            except Exception:
                continue
            preds[d] = float(np.expm1(fcv[-1]))
    return pd.Series(preds)


rows = []
for k in s3.FEEDS:
    for h in [1, 3, 7]:
        y = s3.frame(k)["y"]
        P = {"naive": y.shift(7)}
        P["calendar"], _ = s3.run(k, h, "calendar")
        P["ridge + fcst wx"], _ = s3.run(k, h, "forecast")
        P["ETS"] = classical(k, h, "ets")
        P["SARIMAX + fcst wx"] = classical(k, h, "sarimax")
        idx = None
        for v in P.values():
            ii = v.dropna().index
            idx = ii if idx is None else idx.intersection(ii)
        idx = idx[(idx >= START) & (idx <= END)]
        idx = idx[y.reindex(idx).notna() & (y.reindex(idx) > 0)]
        yy = y.reindex(idx)
        row = {"site": s3.NAMES[k], "lead": f"{h}d", "days": len(idx)}
        for m, v in P.items():
            e = (v.reindex(idx) - yy).abs()
            row[m] = f"{100 * e.sum() / yy.sum():.1f} ({(e / yy < 0.3).mean():.2f})"
        rows.append(row)
        print(k, h, "done", flush=True)
C = pd.DataFrame(rows).set_index("site"); tbl(C)

# ---------- D. nested evaluation ----------
p("## D. Nested evaluation: tune on weeks 1 to 26, report on weeks 27 to 52\n")
def run_cfg(k, h, kind, params):
    f = s3.frame(k); obs = f[s3.WX]
    wx_te = None if kind == "calendar" else s3.forecast_weather(s3.WX_SITE[k], h)
    Xtr = s3.design(f, h, None if kind == "calendar" else obs); Xte = s3.design(f, h, wx_te)
    out = []
    for monday in pd.date_range(START, END, freq="W-MON"):
        cutoff = monday - pd.Timedelta(days=h)
        ok = (Xtr.index < cutoff) & Xtr.notna().all(1) & f["ly"].notna()
        mdl = (HistGradientBoostingRegressor(random_state=0, **params) if kind == "gbm" else Ridge(**params)).fit(Xtr[ok], f["ly"][ok])
        idx = f.loc[monday: monday + pd.Timedelta(days=6)].index; Xt = Xte.loc[idx]; g = Xt.notna().all(1)
        if g.any(): out.append(pd.Series(np.expm1(mdl.predict(Xt[g])), index=idx[g]))
    return pd.concat(out), f["y"]
def wape(pr, y, lo, hi):
    i = pr.index[(pr.index >= lo) & (pr.index < hi)]; i = i[y.reindex(i).notna() & (y.reindex(i) > 0)]
    return 100 * (pr[i] - y[i]).abs().sum() / y[i].sum(), i
GRID = {"ridge": [{"alpha": a} for a in [0.1, 1, 10, 100]],
        "gbm": [{"max_iter": it, "learning_rate": lr, "max_leaf_nodes": ln, "min_samples_leaf": 10}
                for it in [150, 300] for lr in [0.03, 0.1] for ln in [7, 15]]}
rows, pvals = [], []
for k in s3.FEEDS:
    for h in [1, 3, 5, 7]:
        cal, y = run_cfg(k, h, "calendar", {"alpha": 1.0})
        best = {}
        for kind, grid in GRID.items():
            scores = [(wape(run_cfg(k, h, kind if kind == "gbm" else "ridge_fcst", g)[0], y, START, MID)[0], i) for i, g in enumerate(grid)]
            bi = min(scores)[1]; best[kind] = grid[bi]
        r_pr, _ = run_cfg(k, h, "ridge_fcst", best["ridge"]); g_pr, _ = run_cfg(k, h, "gbm", best["gbm"])
        w_cal, i2 = wape(cal, y, MID, END + pd.Timedelta(days=1))
        w_r, _ = wape(r_pr, y, MID, END + pd.Timedelta(days=1)); w_g, _ = wape(g_pr, y, MID, END + pd.Timedelta(days=1))
        common = i2.intersection(r_pr.index)
        t, pv = s3.dm_test(pd.Series((cal[common] - y[common]).values), pd.Series((r_pr[common] - y[common]).values))
        pvals.append(pv)
        rows.append({"site": s3.NAMES[k], "lead": f"{h}d", "calendar": w_cal, "ridge + fcst wx (tuned)": w_r,
                     "GBM + fcst wx (tuned)": w_g, "ridge alpha": best["ridge"]["alpha"], "DM p": pv})
        print(k, h, "nested done", flush=True)
D = pd.DataFrame(rows)
D["DM p (Holm)"] = multipletests(D["DM p"], method="holm")[1]
D = D.set_index("site"); tbl(D)

# ---------- E. figures ----------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
lt = pd.read_csv(OUT / "20261012_lead_time.csv")
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), sharey=False)
for ax, (site, g) in zip(axes, lt.groupby("site", sort=False)):
    for m, st in [("naive", ":"), ("calendar", "--"), ("ridge_fcst", "-"), ("gbm", "-.")]:
        gg = g[g.model == m]; ax.plot(gg.lead_days, gg.wape, st, marker="o", ms=3, label={"ridge_fcst": "ridge + forecast weather", "gbm": "GBM + forecast weather"}.get(m, m))
    ax.set_title(site, fontsize=8); ax.set_xlabel("lead (days)", fontsize=7); ax.tick_params(labelsize=7)
axes[0].set_ylabel("WAPE (%)", fontsize=7); axes[0].legend(fontsize=6, frameon=False)
fig.tight_layout(); fig.savefig(FIG / "lead_time_wape.pdf"); fig.savefig(FIG / "lead_time_wape.png", dpi=200)
p("Figures: out/figures/lead_time_wape.pdf\n")

(OUT / "20261013_review_fixes.md").write_text("\n".join(L))
