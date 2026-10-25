# Reproducibility package: ICAISC 2027 visitor-demand paper

This repository regenerates every computed table, number and figure in

> A. Khanzada, M. Sohail, J. Wasfi and A. Showail, "Forecasting Visitor Demand
> from Open AI-Camera Counts and Weather: Lessons from Japan for Saudi Heritage
> Sites," paper prepared for the International Conference on Advanced
> Innovations in Smart Cities (ICAISC 2027), Jeddah, Saudi Arabia.

The paper forecasts daily visitor counts at three sites in Fukui, Japan (Fukui
Station, the Tojinbo coastal cliff and the Rainbow Line summit park) from open
AI-camera counts, a holiday calendar and the weather forecast that was actually
issued in advance, and tests busy-day warnings and a cold start for new counters.

Everything needed is in this repository: the input data as frozen snapshots
(27 MB), the analysis scripts, one command that runs them, and a checker that
compares the results with the numbers printed in the paper. No network access
is needed after installing the Python packages.

## How to run

With Python 3.12:

```sh
git clone https://github.com/amilkh/paper-icaisc-supplement.git
cd paper-icaisc-supplement
python3.12 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python reproduce.py --jobs 4
```

`reproduce.py` verifies the checksums in `data/SHA256SUMS`, runs the 13 analysis
steps into `out/`, then prints PASS or FAIL for each paper item and compares
every regenerated file with the copy in `expected/`. The last line should read
`SUMMARY: 57/57 paper items reproduced`; the exit code is 0 only then.

- `--jobs N` runs independent steps in parallel (default 1). Memory use stays
  under about 2 GB.
- `python reproduce.py --check` repeats only the comparison on an existing `out/`.
- Console output goes to `logs/reproduce.log`, each step's output to
  `logs/steps/<step>.log`.

**Runtime.** 63 minutes with `--jobs 4` on a 4-vCPU, 16 GB cloud VM (Python 3.12). The two slowest steps, scan04 (25 min) and scan05 (38 min), refit models weekly for every site and lead and run in sequence, so more cores do not shorten the run much.

## Paper items and where they come from

Each row is one check in `code/check.py`. The value is read from the
regenerated output file and must round to the number printed in the paper.
"Reproduced" shows the value from our own run (`logs/reproduce.log`).
Table and figure numbers follow the submitted version (Tables I to IV,
Figs. 1 to 4).

| Paper item | What is checked | Output file | Paper | Reproduced |
|---|---|---|---|---|
| Table I | Fukui Station: days, median/day, weekend and holiday uplift | `20261011_cross_site_patterns.md` | 642, 8,343, 1.49, 1.65 | 642, 8,343, 1.49, 1.65 |
| Table I | Tojinbo: days, median/day, weekend and holiday uplift | `20261011_cross_site_patterns.md` | 641, 8,173, 2.07, 2.35 | 641, 8,173, 2.07, 2.35 |
| Table I | Rainbow L. lot 1: days, median/day, weekend and holiday uplift | `20261011_cross_site_patterns.md` | 607, 174, 1.84, 2.20 | 607, 174, 1.84, 2.20 |
| Table I | Rainbow L. lot 2: days, median/day, weekend and holiday uplift | `20261011_cross_site_patterns.md` | 607, 0, n/a, n/a | 607, 0, inf, inf |
| Table II | Fukui Station: % per 10 mm rain, +5 m/s wind, +3 h sun, +5 °C [95% CI] | `20261012_weather_jma.md` | −3 [−6, −1]; +4 [−2, +10]; 0 [−2, +1]; +2 [−1, +5] | -3.4% [-5.5, -1.3]; +4.1% [-1.6, +10.1]; -0.4% [-1.6, +0.9]; +2.4% [-0.5, +5.4] |
| Table II | Tojinbo: % per 10 mm rain, +5 m/s wind, +3 h sun, +5 °C [95% CI] | `20261012_weather_jma.md` | −9 [−13, −5]; −10 [−17, −3]; +5 [+3, +8]; +12 [+7, +18] | -8.8% [-12.7, -4.8]; -10.4% [-17.0, -3.3]; +5.3% [+2.5, +8.2]; +12.3% [+7.2, +17.6] |
| Table II | Rainbow Line: % per 10 mm rain, +5 m/s wind, +3 h sun, +5 °C [95% CI] | `20261012_weather_jma.md` | −37 [−47, −24]; −13 [−25, +2]; +17 [+12, +22]; +7 [−2, +16] | -36.5% [-46.9, -24.1]; -12.7% [-25.4, +2.2]; +17.2% [+12.3, +22.4]; +6.7% [-1.5, +15.5] |
| Sec. V-A text | Open-Meteo rain effect, % per 10 mm (station, Tojinbo, Rainbow Line) | `20261011_weather_openmeteo.md` | −1, −13, −36 | -0.8, -13.4, -36.2 |
| Table III | Fukui Station 1d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 11.88, 12.04, +0.2 [-0.1, +0.5], 0.313 | 11.88, 12.04, +0.2 [-0.1, +0.5], 0.313 |
| Table III | Fukui Station 3d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 14.43, 14.67, +0.2 [-0.0, +0.6], 0.122 | 14.43, 14.67, +0.2 [-0.0, +0.6], 0.122 |
| Table III | Tojinbo 1d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 23.29, 21.57, -1.7 [-3.4, -0.3], 0.018 | 23.29, 21.57, -1.7 [-3.4, -0.3], 0.018 |
| Table III | Tojinbo 3d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 27.16, 26.04, -1.1 [-3.0, +0.7], 0.224 | 27.16, 26.04, -1.1 [-3.0, +0.7], 0.224 |
| Table III | Rainbow Line 1d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 33.95, 27.38, -6.6 [-9.5, -3.6], <0.001 | 33.95, 27.38, -6.6 [-9.5, -3.6], 0.000 |
| Table III | Rainbow Line 3d: WAPE calendar, +forecast wx, change [95% CI], DM p | `20261012_forecast_weather_test.md` | 38.50, 31.87, -6.6 [-9.7, -3.6], <0.001 | 38.50, 31.87, -6.6 [-9.7, -3.6], 0.000 |
| Table IV | Fukui Station: top-20% day, weather none: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.92 [0.87, 0.96], 0.78, 0.62 | 0.92 [0.87, 0.96], 0.78, 0.62 |
| Table IV | Fukui Station: top-20% day, weather 3-day forecast: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.92 [0.87, 0.96], 0.79, 0.57 | 0.92 [0.87, 0.96], 0.79, 0.57 |
| Table IV | Tojinbo: top-20% day, weather none: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.91 [0.85, 0.96], 0.82, 0.64 | 0.91 [0.85, 0.96], 0.82, 0.64 |
| Table IV | Tojinbo: top-20% day, weather 3-day forecast: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.93 [0.88, 0.97], 0.86, 0.64 | 0.93 [0.88, 0.97], 0.86, 0.64 |
| Table IV | RL: top-20% day, weather none: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.81 [0.75, 0.87], 0.78, 0.45 | 0.81 [0.75, 0.87], 0.78, 0.45 |
| Table IV | RL: top-20% day, weather 3-day forecast: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.87 [0.83, 0.91], 0.84, 0.54 | 0.87 [0.83, 0.91], 0.84, 0.54 |
| Table IV | RL: car park 2 in use, weather none: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.87 [0.80, 0.94], 0.60, 0.55 | 0.87 [0.80, 0.94], 0.60, 0.55 |
| Table IV | RL: car park 2 in use, weather 3-day forecast: AUC [95% CI], precision, recall | `20261012_forecast_weather_test.md` | 0.89 [0.82, 0.95], 0.82, 0.59 | 0.89 [0.82, 0.95], 0.82, 0.59 |
| Abstract | range of three-day warning AUC with forecast weather | `20261012_forecast_weather_test.md` | 0.87 to 0.93 | 0.87 to 0.93 |
| Sec. V-B | Fukui Station 1-day WAPE: naive, calendar | `20261012_lead_time.md` | 19.3, 11.9 | 19.3, 11.9 |
| Sec. V-B | Rainbow Line 1-day WAPE: naive, calendar | `20261012_lead_time.md` | 41.5, 34.0 | 41.5, 34.0 |
|  | Abstract, Sec. V-B Rainbow Line weather gain significant at leads 1 to 5 (DM p) | `20261012_lead_time.md` | <0.05, <0.05, <0.05, <0.05, <0.05 | 0.0, 0.0, 0.0, 0.001, 0.0 |
| Sec. V-B | Rainbow Line forecast keeps % of perfect-weather gain at 1, 3, 6 days | `20261012_lead_time.md` | 92 [66, 113]; 94 [73, 119]; 23 [−29, 56] | 92% [66, 113]; 94% [73, 119]; 23% [-29, 56] |
| Sec. V-B | Rainbow Line share of days within ±30%, 1 and 3 days (63%, 54%) | `20261012_lead_time.md` | 0.63, 0.54 | 0.63, 0.54 |
| Sec. V-B | Tojinbo weather DM p at 1 and 7 days | `20261012_lead_time.md` | 0.018, 0.041 | 0.018, 0.041 |
| Sec. V-B | Fukui Station share of days within ±30%, range over leads 1 to 7 (90-95%) | `20261012_lead_time.md` | 0.90 to 0.95 | 0.90 to 0.95 |
| Sec. V-B | Rainbow Line 3-day WAPE: gradient boosting, forecast-weather ridge | `20261012_lead_time.md` | 30.0, 31.9 | 30.0, 31.9 |
| Sec. V-C | lowest warning AUC at leads 1 to 5 (stays useful, AUC ≥ 0.85) | `20261012_lead_time.md` | ≥0.85 | 0.86 |
| Sec. V-B | Rainbow Line Holm-adjusted p at 1, 3, 5 days (tuning check) | `20261013_review_fixes.md` | <0.01, <0.01, <0.01 | 0.00, 0.00, 0.00 |
| Sec. V-B | Tojinbo Holm-adjusted p at 1 and 7 days (not significant) | `20261013_review_fixes.md` | >0.05, >0.05 | 0.76, 0.90 |
| Sec. V-B | Rainbow Line 1-day WAPE: SARIMAX, ridge (both with forecast weather) | `20261013_review_fixes.md` | 26.6, 27.4 | 26.6, 27.4 |
| Sec. V-B | largest SARIMAX shortfall against ridge, points (within about 3) | `20261013_review_fixes.md` | ≤3.0 | 2.7 |
| Sec. V-C | three busy-day definitions with forecast weather: AUC range; busy share of test days (30-50%) | `20261013_review_fixes.md` | 0.82 to 0.93; 0.30 to 0.50 | 0.82 to 0.93; 0.30 to 0.50 |
| Sec. V-C | overflow-lot AUC range over three labels; test days where only faces show lot 2 in use | `20261013_review_fixes.md` | 0.88 to 0.90; 11 | 0.88 to 0.90; 11 |
| Sec. III, V-C | pooled Rainbow Line gates: valid days, median faces per plate, daily correlation | `20261013_rainbow_faces_plates.md` | 604, 0.32, 0.77 | 604, 0.32, 0.77 |
| Sec. V-C | rain effect, % per 10 mm: faces, plates | `20261013_rainbow_faces_plates.md` | −43, −37 | -43, -37 |
| Sec. V-C | three-day WAPE with forecast weather: faces, plates | `20261013_rainbow_faces_plates.md` | 66, 34 | 65.9, 33.7 |
| Sec. V-C | three-day busy-day warning AUC with forecast weather: faces, plates | `20261013_rainbow_faces_plates.md` | 0.93, 0.88 | 0.93, 0.88 |
| Sec. V-C | faces warning: correct flags, busy test days, flagged, precision, recall | `20261017_faces_warning_counts.md` | 43 of 86 busy days, 43 flagged, precision 1.00, recall 0.50 | 43 of 86 busy days, 43 flagged, precision 1.00, recall 0.50 |
| Sec. V-C | plates warning with forecast weather: precision, recall | `20261017_faces_warning_counts.md` | 0.84, 0.60 | 0.84, 0.60 |
| Sec. III | Tojinbo 2025 detections per official visitor; scaled detections; official visitors | `20261016_data_facts.md` | 5; 3.3 million; 651,000 | 5.05; 3.285746 million; 651,000 |
| Sec. III | faces as share of detections (Tojinbo, station; about 3-4%); station faces aged 6-12, % | `20261016_data_facts.md` | 0.03, 0.04; 41 | 0.026, 0.043; 40.7% |
| Sec. V-D | 3 days of history, hourly WAPE: ridge and same-hour-last-week at station; ridge and baseline at Tojinbo | `coldstart/cold_start_ci.csv` | 36.2, 27.4; 57.9, 43.8 | 36.22, 27.38; 57.86, 43.78 |
| Sec. V-D | days of history before ridge beats the baseline: Tojinbo (about a week), station (four weeks) | `coldstart/cold_start_ci.csv` | 7, 28 | 7, 28 |
| Sec. V-D | shrunk minus baseline at 3 days: upper 95% limit below zero at station and Tojinbo | `coldstart/cold_start_ci.csv` | <0, <0 | -0.28, -0.42 |
| Sec. V-D | Tojinbo, 3 days: shrunk minus baseline, points [95% CI] | `coldstart/cold_start_ci.csv` | −1.2 [−2.1, −0.4] | -1.21 [-2.15, -0.42] |
| Sec. V-D | station, 56 days: 95% interval of shrunk minus baseline, points | `coldstart/cold_start_ci.csv` | [−6.3, +1.0] | [-6.3, 1.0] |
| Sec. V-D | Tojinbo, 28 days: shrunk minus baseline, points | `coldstart/cold_start_ci.csv` | −10.1 | -10.08 |
| Sec. V-D | best hourly peak F1: station (about 0.4), Tojinbo (about 0.6) | `coldstart/cold_start_peak_f1.csv` | 0.4, 0.6 | 0.429, 0.628 |
| Sec. VII | forecast-weather cold start: largest change in shrunk WAPE, points (about one); intervals changing sign | `coldstart/cold_start_ci.csv` | 1; 0 | 1.01; 0 |
| 2 | figure             regenerated as out/figures/daily_counts.png | `out/figures/daily_counts.png` | figure | pixel-identical |
| 3 | figure             regenerated as out/figures/lead_time_wape.png | `out/figures/lead_time_wape.png` | figure | pixel-identical |
| 4 | figure             regenerated as out/coldstart/cold_start.png | `out/coldstart/cold_start.png` | figure | identical up to canvas size |

Fig. 1 (site photos and aerial imagery) is not computed and is not part of
this package.

## Layout

```
reproduce.py          one command: verify data, run every step, check
requirements.txt      pinned package versions (same as the analysis repository)
data/                 input snapshots (parquet) and SHA256SUMS; see DATA_PROVENANCE.md
code/                 analysis scripts (vendored, see below) and check.py
expected/             outputs committed in icaisc-camera-scans release v1.1
logs/                 console log and per-step logs of our own full run
out/                  created by reproduce.py (not committed)
```

| Step | Script | Writes (under `out/`) | Paper |
|---|---|---|---|
| scan01 | `code/scan01.py` | `20261011_cross_site_patterns.md` | Table I |
| scan02_jma | `code/scan02.py jma` | `20261012_weather_jma.md` | Table II |
| scan02_openmeteo | `code/scan02.py openmeteo` | `20261011_weather_openmeteo.md` | Open-Meteo check in Sec. V-A |
| scan03 | `code/scan03.py` | `20261012_forecast_weather_test.md` | Tables III and IV |
| scan04 | `code/scan04.py` | `20261012_lead_time.md`, `.csv`, `20261015_forecast_gain_kept.csv` | Fig. 3 and lead-time text |
| scan05 | `code/scan05.py` | `20261013_review_fixes.md`, `20261013_busy_definitions.csv` | baselines, tuning check, warning definitions |
| scan06 | `code/scan06.py` | `20261013_rainbow_faces_plates.md` | faces vs plates |
| scan07 | `code/scan07.py` | `20261014_window_sensitivity.md` | active-hours window sensitivity |
| scan08 | `code/scan08_data_facts.py` | `20261016_data_facts.md` | Data section facts |
| scan09 | `code/scan09_faces_warning_counts.py` | `20261017_faces_warning_counts.md` | faces warning counts |
| fig_timeseries | `code/fig_timeseries.py` | `figures/daily_counts.{pdf,png}` | Fig. 2 |
| fig_leadtime | `code/fig_leadtime.py` | `figures/lead_time_wape.{pdf,png}` | Fig. 3 |
| cold_start | `code/cold_start.py` | `coldstart/cold_start_{results,ci,peak_f1}.csv`, `coldstart/cold_start.{pdf,png}` | cold start text and Fig. 4 |

`code/common.py` holds the shared loaders. Random seeds are fixed in the
scripts, so the results are deterministic for a given platform.

## Relation to the analysis repository

The full analysis history, the data download and build scripts, and extra
analyses not used in the paper (warning cut-off sweep, calendar-block
sensitivity, superseded first versions) live in
[amilkh/icaisc-camera-scans](https://github.com/amilkh/icaisc-camera-scans),
release [v1.1](https://github.com/amilkh/icaisc-camera-scans/releases/tag/v1.1),
which the paper cites.

The scripts in `code/` are copies of the files at tag v1.1 (commit `d85afdb`),
byte for byte, except:

- `cold_start.py` (from `coldstart/` there) writes its outputs to
  `out/coldstart/` instead of its own folder; two docstring lines are updated
  to match.
- The scans are run from `code/`, so their relative paths `../data` and
  `../out` resolve to this repository's `data/` and `out/` without edits.
- The download and build steps (`build_data.py`, `get_weather.py`,
  `get_forecasts.py`, `get_jma.py`) are omitted; their outputs are the
  snapshots in `data/`.
- `reproduce.py` and `code/check.py` are new.

No modelling code was changed.

## What can differ on another machine

Direct dependencies are pinned, but the BLAS library, operating system and
fonts are not. On a different platform expect, at most, last-digit
floating-point differences in the CSV files (the checker reports the largest
relative difference) and small pixel differences in the figures. PDF figures
are not compared because they embed creation dates. The paper items are
checked at the paper's rounding, so they are not affected by such noise.

## Licence and data

Code: all rights reserved for now; a licence will be added before publication of the paper. Data: camera counts from Code for FUKUI (MIT), JMA
observations (source: Japan Meteorological Agency) and Open-Meteo weather data
(CC BY 4.0); details, versions and fetch dates in
[DATA_PROVENANCE.md](DATA_PROVENANCE.md).
