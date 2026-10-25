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

**Runtime.** RUNTIME_PLACEHOLDER

## Paper items and where they come from

Each row is one check in `code/check.py`. The value is read from the
regenerated output file and must round to the number printed in the paper.
"Reproduced" shows the value from our own run (`logs/reproduce.log`).
Table and figure numbers follow the submitted version (Tables I to IV,
Figs. 1 to 4).

TABLE_PLACEHOLDER

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
