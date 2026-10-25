# Scan 03: ex-ante forecasts with archived weather forecasts

Training uses observed weather; test predictions use the Open-Meteo forecast issued h days before (previous-runs API). Rolling origin, weekly refit, test 2025-10-13 to 2026-10-10. DM = Diebold-Mariano test on absolute errors, forecast-weather model against calendar only (negative t means weather helps). CI = 95% weekly block bootstrap of the WAPE change.

## A. Daily count forecasts

| site | h | days | WAPE calendar | WAPE +forecast wx | WAPE +observed wx | change (pts) [95% CI] | DM t (p) | within ±30%, forecast wx | observed-wx gain kept [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| Fukui Station | 1d | 338 | 11.88 | 12.04 | 12.15 | +0.2 [-0.1, +0.5] | +1.01 (0.313) | 0.95 | n/a |
| Fukui Station | 3d | 338 | 14.43 | 14.67 | 14.73 | +0.2 [-0.0, +0.6] | +1.54 (0.122) | 0.90 | n/a |
| Tojinbo | 1d | 353 | 23.29 | 21.57 | 21.44 | -1.7 [-3.4, -0.3] | -2.36 (0.018) | 0.75 | 93% [45, 142] |
| Tojinbo | 3d | 352 | 27.16 | 26.04 | 25.33 | -1.1 [-3.0, +0.7] | -1.22 (0.224) | 0.66 | 61% [-153, 100] |
| Rainbow Line lot 1 | 1d | 295 | 33.95 | 27.38 | 26.80 | -6.6 [-9.5, -3.6] | -4.69 (0.000) | 0.63 | 92% [66, 113] |
| Rainbow Line lot 1 | 3d | 296 | 38.50 | 31.87 | 31.47 | -6.6 [-9.7, -3.6] | -4.43 (0.000) | 0.54 | 94% [73, 119] |

*Observed-wx gain kept* = (WAPE calendar - WAPE +forecast wx) / (WAPE calendar - WAPE +observed wx): the share of the gain from perfectly known weather that the forecast issued h days earlier delivers; n/a where observed weather does not beat calendar. Interval: 2,000 weekly block-bootstrap resamples of the test days, dropping resamples where observed weather does not beat calendar.

## B. Busy-day warnings three days ahead, with the forecast available at the time

| warning | weather | days | AUC [95% CI] | precision | recall |
|---|---|---|---|---|---|
| Fukui Station: top-20% day | none | 338 | 0.92 [0.87, 0.96] | 0.78 | 0.62 |
| Fukui Station: top-20% day | 3-day forecast | 338 | 0.92 [0.87, 0.96] | 0.79 | 0.57 |
| Tojinbo: top-20% day | none | 352 | 0.91 [0.85, 0.96] | 0.82 | 0.64 |
| Tojinbo: top-20% day | 3-day forecast | 352 | 0.93 [0.88, 0.97] | 0.86 | 0.64 |
| Rainbow Line: top-20% day | none | 296 | 0.81 [0.75, 0.87] | 0.78 | 0.45 |
| Rainbow Line: top-20% day | 3-day forecast | 296 | 0.87 [0.83, 0.91] | 0.84 | 0.54 |
| Rainbow Line: car park 2 in use | none | 297 | 0.87 [0.80, 0.94] | 0.60 | 0.55 |
| Rainbow Line: car park 2 in use | 3-day forecast | 297 | 0.89 [0.82, 0.95] | 0.82 | 0.59 |
