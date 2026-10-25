"""Cold-start experiment: how much history does a new AI camera need to forecast
hourly crowds and warn of peaks?

Setup
-----
For each test window (28 days) and each history length N, pretend the camera was
installed N days before the window: every count before that date is hidden.
Models are fitted on the N visible days and forecast each test day's 24 hourly
counts at the end of the previous day (day-ahead). Lag features use only data
observed after the install date.

Models (each camera uses only its own history; no cross-camera transfer)
------
naive_week   same hour, same weekday last week (falls back to yesterday, then 0)
profile      mean of log counts by (hour, day-off flag) over visible history
ridge        Ridge on log1p: hour x day-off profile, lags, weather
ridge_noweather  same, without weather (ablation)
blend        ridge shrunk toward naive_week, weight min(n/56, 1) for n days of history
blend_noweather  same, shrinking ridge_noweather (needs no weather at all)
blend_fcst   same as blend, but test-day weather is the archived day-ahead forecast
gbm          histogram gradient boosting on the ridge features

Weather for ridge/blend/gbm uses observed JMA hourly values for the target day (a perfect
forecast). blend_fcst is the ex-ante check: it trains on observed weather but forecasts with
the Open-Meteo forecast issued the day before (previous_day1 in data/fcst7_<site>.parquet),
as in the main forecast-weather test.

Run from the repo root:  python code/cold_start.py
Inputs (built by scripts/build_data.py, get_jma.py and get_forecasts.py, as for the scans):
  data/5min_<site>_Person.parquet   camera counts, code4fukui @ b89bc2c
  data/jma_<site>.parquet           JMA hourly observations (hour starting)
  data/fcst7_<site>.parquet         Open-Meteo previous-runs forecasts
Outputs (in out/coldstart/): cold_start_results.csv, cold_start_ci.csv, cold_start_peak_f1.csv,
  cold_start.png/pdf (Fig. 4)
"""
from pathlib import Path

import jpholiday
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
# Vendored copy: outputs go to out/coldstart/ instead of the script folder.
OUTDIR = HERE.parent / "out" / "coldstart"
OUTDIR.mkdir(parents=True, exist_ok=True)
SITES = {"fukui-station-east-entrance": "fukui_station", "tojinbo-shotaro": "tojinbo"}
WX_SITE = {"fukui_station": "station", "tojinbo": "tojinbo"}  # data/jma_<x>, data/fcst7_<x>
LABEL = {"fukui_station": "Fukui Station", "tojinbo": "Tojinbo"}
HISTORY = [3, 7, 14, 28, 56, 91, 182, 365]
WINDOW = 28
MODELS = ["naive_week", "profile", "ridge", "ridge_noweather", "blend", "blend_noweather",
          "blend_fcst", "gbm"]
WX_COLS = ["rain", "temp", "temp2"]


def load_counts(site):
    d = pd.read_parquet(DATA / f"5min_{site}_Person.parquet").set_index("t0")["count"]
    s = d.resample("h").sum(min_count=1).astype(float)   # hourly totals; hours with no bins stay NaN
    s = s.reindex(pd.date_range(s.index.min().normalize(), s.index.max().normalize()
                                + pd.Timedelta(hours=23), freq="h"))
    # Outage days: daily total 0, or under 15% of the trailing 28-day median.
    daily = s.resample("D").sum(min_count=20)
    ref = daily.rolling(28, min_periods=7).median().shift(1)
    bad = daily.isna() | (daily == 0) | (daily < 0.15 * ref)
    s[s.index.normalize().isin(daily.index[bad])] = np.nan
    return s, int(bad.sum())


def load_weather(node):
    # JMA hourly observations, already shifted to hour starting by scripts/get_jma.py.
    j = pd.read_parquet(DATA / f"jma_{WX_SITE[node]}.parquet").set_index("t0")
    w = pd.DataFrame({"temp_c": j["temperature_2m"], "precip_1h_mm": j["precipitation"]})
    # Day-ahead forecast (issued the day before), same convention as scan03.forecast_weather.
    f = pd.read_parquet(DATA / f"fcst7_{WX_SITE[node]}.parquet").set_index("t0")
    f = pd.DataFrame({"fc_temp_c": f["temperature_2m_previous_day1"],
                      "fc_precip_1h_mm": f["precipitation_previous_day1"]})
    return w.join(f, how="outer")


def day_off(d):
    return d.dayofweek >= 5 or jpholiday.is_holiday(d.date()) or (d.month, d.day) >= (12, 29) \
        or (d.month == 1 and d.day <= 3)


def frame(s, w):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    days = pd.Series(df.index.normalize().unique())
    off = {d: day_off(d) for d in days}
    df["off"] = [off[d] for d in df.index.normalize()]
    df = df.join(w, how="left")
    df["temp_c"] = df["temp_c"].interpolate(limit=3)
    df["precip_1h_mm"] = df["precip_1h_mm"].fillna(0.0)
    df["fc_temp_c"] = df["fc_temp_c"].interpolate(limit=3)
    return df


def design(df, visible_y, prof):
    """Feature matrix for rows of df, using only visible_y for lags."""
    z = np.log1p(visible_y)
    lag24 = z.shift(24).reindex(df.index)
    lag168 = z.shift(168).reindex(df.index)
    base = np.array([prof.get((h, o), np.nan) for h, o in zip(df["hour"], df["off"])])
    lag24 = lag24.fillna(pd.Series(base, index=df.index))
    lag168 = lag168.fillna(pd.Series(base, index=df.index))
    X = pd.DataFrame(index=df.index)
    for h in range(24):
        X[f"h{h}"] = (df["hour"] == h).astype(float)
        X[f"h{h}_off"] = ((df["hour"] == h) & df["off"]).astype(float)
    X["lag24"] = lag24 - base
    X["lag168"] = lag168 - base
    X["rain"] = np.log1p(df["precip_1h_mm"])
    X["temp"] = df["temp_c"].fillna(df["temp_c"].mean()) / 10.0
    X["temp2"] = X["temp"] ** 2
    return X.fillna(0.0), base


def profile_of(df_vis):
    z = np.log1p(df_vis["y"])
    p = z.groupby([df_vis["hour"], df_vis["off"]]).mean().to_dict()
    # If the visible history has no day off yet (or no workday), borrow the other.
    for h in range(24):
        for o in (False, True):
            if (h, o) not in p and (h, not o) in p:
                p[(h, o)] = p[(h, not o)]
    return p


def forecast(df, model, vis_start, test_days):
    vis = df[(df.index >= vis_start) & (df.index < test_days[0])].dropna(subset=["y"])
    if len(vis) < 24:
        return None
    prof = profile_of(vis)
    visible_y = df["y"].where(df.index >= vis_start)
    test = df[df.index.normalize().isin(test_days)]
    if model == "naive_week":
        z = np.log1p(visible_y)
        pred = z.shift(168).reindex(test.index)
        pred = pred.fillna(z.shift(24).reindex(test.index)).fillna(0.0)
        return np.expm1(pred.values)
    if model == "profile":
        return np.expm1([prof.get((h, o), 0.0) for h, o in zip(test["hour"], test["off"])])
    if model == "ridge":
        Xv, bv = design(vis, visible_y, prof)
        m = Ridge(alpha=3.0).fit(Xv, np.log1p(vis["y"]) - bv)
        Xt, bt = design(test, visible_y, prof)
        return np.expm1(bt + m.predict(Xt))
    if model in ("ridge_noweather", "blend", "blend_noweather", "blend_fcst", "gbm"):
        Xv, bv = design(vis, visible_y, prof)
        if model == "blend_fcst":
            # Ex-ante: the test day's weather is what was forecast the day before.
            test = test.assign(temp_c=test["fc_temp_c"], precip_1h_mm=test["fc_precip_1h_mm"].fillna(0.0))
        Xt, bt = design(test, visible_y, prof)
        cols = list(Xv.columns)
        if model in ("ridge_noweather", "blend_noweather"):
            cols = [c for c in cols if c not in WX_COLS]
        if model == "ridge_noweather":
            m = Ridge(alpha=3.0).fit(Xv[cols], np.log1p(vis["y"]) - bv)
            return np.expm1(bt + m.predict(Xt[cols]))
        if model == "gbm":
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                              min_samples_leaf=20, random_state=0)
            m.fit(Xv, np.log1p(vis["y"]) - bv)
            return np.expm1(bt + m.predict(Xt))
        # blend: shrink Ridge toward same-hour-last-week while history is short (full trust at 56 days).
        m = Ridge(alpha=3.0).fit(Xv[cols], np.log1p(vis["y"]) - bv)
        z = np.log1p(visible_y)
        naive = z.shift(168).reindex(test.index).fillna(z.shift(24).reindex(test.index))
        naive = naive.fillna(pd.Series(bt, index=test.index)).values
        n_days = (test_days[0] - vis_start).days   # nominal days of history, as in the paper
        w = min(n_days / 56.0, 1.0)
        return np.expm1(w * (bt + m.predict(Xt[cols])) + (1 - w) * naive)
    raise ValueError(model)


def score(y, p, thr):
    ok = ~np.isnan(y)
    y, p = y[ok], np.clip(p[ok], 0, None)
    wape = np.abs(y - p).sum() / max(y.sum(), 1)
    a, f = y >= thr, p >= thr
    tp = (a & f).sum()
    prec = tp / f.sum() if f.sum() else np.nan
    rec = tp / a.sum() if a.sum() else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec and rec and prec + rec > 0 else 0.0
    return wape, prec, rec, f1


def main():
    data = {}
    for site, node in SITES.items():
        s, n_bad = load_counts(site)
        data[node] = frame(s, load_weather(node))
        print(f"{node}: {s.notna().sum()} valid hours, {n_bad} outage days excluded")

    start = max(df.index.min() for df in data.values()).normalize()
    end = min(df.index.max() for df in data.values()).normalize()
    first_test = start + pd.Timedelta(days=max(HISTORY))
    origins = pd.date_range(first_test, end - pd.Timedelta(days=WINDOW - 1), freq=f"{WINDOW}D")
    print(f"{len(origins)} test windows, {origins[0].date()} to {end.date()}")

    rows, daily = [], []
    for node, df in data.items():
        # Fixed peak threshold: 90th percentile of daytime hours in calendar 2025.
        ref = df.loc["2025", "y"]
        thr = ref[(ref.index.hour >= 8) & (ref.index.hour <= 19)].quantile(0.9)
        for o in origins:
            test_days = pd.date_range(o, periods=WINDOW, freq="D")
            sel = df.index.normalize().isin(test_days)
            y = df.loc[sel, "y"].values
            day = df.index[sel].normalize()
            for n in HISTORY:
                vis_start = o - pd.Timedelta(days=n)
                for m in MODELS:
                    p = forecast(df, m, vis_start, test_days)
                    if p is None:
                        continue
                    p = np.clip(np.asarray(p), 0, None)
                    rows.append((node, o.date(), n, m, *score(y, p, thr), thr))
                    ok = ~np.isnan(y)
                    g = pd.DataFrame({"day": day[ok], "abs_err": np.abs(y[ok] - p[ok]), "y": y[ok]})
                    for d, r in g.groupby("day").sum().iterrows():
                        daily.append((node, n, m, d.date(), r.abs_err, r.y))
    res = pd.DataFrame(rows, columns=["node", "origin", "history_days", "model", "wape",
                                      "peak_precision", "peak_recall", "peak_f1", "peak_threshold"])
    res.to_csv(OUTDIR / "cold_start_results.csv", index=False)
    summary = res.groupby(["node", "model", "history_days"])[["wape", "peak_f1"]].mean().round(3)
    print(summary.unstack("history_days").to_string())
    # Hourly peak warnings (Section V-D): mean peak F1 over the windows, per site, model and history,
    # and the best value per site, which the paper reports (about 0.4 and 0.6).
    pf = res.groupby(["node", "model", "history_days"])["peak_f1"].mean().round(3).reset_index()
    pf.to_csv(OUTDIR / "cold_start_peak_f1.csv", index=False)
    best = pf.loc[pf.groupby("node")["peak_f1"].idxmax()]
    print("Best mean peak F1 per site:")
    print(best.to_string(index=False))
    daily = pd.DataFrame(daily, columns=["node", "history_days", "model", "day", "abs_err", "y"])
    ci = bootstrap_gain(daily)
    ci.to_csv(OUTDIR / "cold_start_ci.csv", index=False)
    print(ci.to_string(index=False))
    plot_fig4(ci)


def bootstrap_gain(daily, reps=2000, seed=0):
    """Pooled hourly WAPE per model, and the blend-vs-naive gap with a 95% CI from a
    weekly block bootstrap (weeks resampled with replacement)."""
    rng = np.random.default_rng(seed)
    out = []
    for (node, n), g in daily.groupby(["node", "history_days"]):
        w = g.pivot_table(index="day", columns="model", values=["abs_err", "y"], aggfunc="sum")
        w["week"] = pd.to_datetime(w.index).to_period("W").astype(str)
        weeks = w.groupby("week").sum()
        e, y = weeks["abs_err"], weeks["y"]["naive_week"]
        idx = rng.integers(0, len(weeks), size=(reps, len(weeks)))
        for b in ["blend", "blend_noweather", "blend_fcst"]:
            wape = {m: e[m].sum() / y.sum() for m in ["naive_week", "ridge", b]}
            diff = (e[b].values[idx].sum(1) - e["naive_week"].values[idx].sum(1)) / y.values[idx].sum(1)
            lo, hi = np.percentile(diff, [2.5, 97.5])
            out.append((node, n, b, 100 * wape["naive_week"], 100 * wape["ridge"], 100 * wape[b],
                        100 * (wape[b] - wape["naive_week"]), 100 * lo, 100 * hi, len(weeks)))
    return pd.DataFrame(out, columns=["node", "history_days", "variant", "wape_naive", "wape_ridge",
                                      "wape_blend", "blend_minus_naive_pp", "ci_lo_pp", "ci_hi_pp",
                                      "weeks"]).round(2)


def plot_fig4(ci):
    """Fig. 4: pooled hourly WAPE against days of history (naive, ridge, shrunk)."""
    c = ci[ci.variant == "blend"]
    series = [("wape_naive", "Same hour last week", "#2a78d6", "o"),
              ("wape_ridge", "Ridge", "#eb6834", "s"),
              ("wape_blend", "Shrunk", "#1baf7a", "D")]
    plt.rcParams.update({"font.size": 8, "font.family": "serif"})
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.4), sharey=False)
    for ax, node in zip(axes, ["fukui_station", "tojinbo"]):
        g = c[c.node == node].sort_values("history_days")
        for col, name, color, mk in series:
            ax.plot(g.history_days, g[col], marker=mk, ms=4, lw=1.5, color=color, label=name)
        ax.set_xscale("log"); ax.set_xticks(HISTORY); ax.set_xticklabels(HISTORY)
        ax.set_title(LABEL[node], fontsize=8); ax.set_xlabel("Days of history")
        ax.yaxis.grid(True, color="#e5e5e5", lw=0.5)
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("Hourly WAPE (%)")
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUTDIR / "cold_start.pdf", bbox_inches="tight")
    fig.savefig(OUTDIR / "cold_start.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
