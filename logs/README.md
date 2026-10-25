# Run record

Clean run of `python reproduce.py --jobs 4` on 25 October 2026 on an Ubuntu box
(2 vCPU, 4 GB RAM, Python 3.12), 1 h 50 min wall time. `console.txt` holds the
full console output, `steps/` one log per analysis step.

Result: 57 of 57 paper items reproduced at the paper's rounding.

Files that differ from `expected/` and why:

- `20261012_weather_jma.md`, section C (busy-day table from scan02): three cells
  differ by 0.01. This table is not used in the paper (the paper's warning
  results come from scan03 and scan05, which reproduced exactly).
- `20261015_forecast_gain_kept.csv`: floating-point noise in the 15th digit.
- `coldstart/cold_start_peak_f1.csv` and `cold_start_results.csv`: last-digit
  noise and an empty cell written as 0.0; the pooled `cold_start_ci.csv` used by
  the paper is identical.
- Figures: pixel-identical except `cold_start.png`, where the renderer gives a
  slightly different canvas size.
