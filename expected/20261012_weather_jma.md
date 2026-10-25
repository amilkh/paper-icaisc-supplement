# Scan 02: weather sensitivity and staffing-forecast skill

Data: camera counts @ b89bc2c; weather from JMA station observations (Fukui City, Mikuni AMeDAS, Mihama AMeDAS; peak wind is the highest hourly mean), aggregated over each site's own active hours (hours holding at least 2% of the day's detections in that calendar month, which follow opening hours and season). Outage days are excluded.

## A. Weather effect on daily counts

OLS on log counts with day-of-week, holiday and year-month fixed effects, HAC errors (lag 7). Effects are % change in the daily count.

| feed | n days | per 10 mm rain | per +5 m/s peak hourly wind | per +3 h sun | per +5 °C | R² |
|---|---|---|---|---|---|---|
| Fukui Station (people) | 642 | -3.4% [-5.5, -1.3] | +4.1% [-1.6, +10.1] | -0.4% [-1.6, +0.9] | +2.4% [-0.5, +5.4] | 0.68 |
| Tojinbo (people) | 640 | -8.8% [-12.7, -4.8] | -10.4% [-17.0, -3.3] | +5.3% [+2.5, +8.2] | +12.3% [+7.2, +17.6] | 0.72 |
| Rainbow Line lot 1 (cars) | 605 | -36.5% [-46.9, -24.1] | -12.7% [-25.4, +2.2] | +17.2% [+12.3, +22.4] | +6.7% [-1.5, +15.5] | 0.63 |

Brackets: 95% interval, endpoints transformed from the log(1+y) scale.

## B. Daily forecast skill, rolling origin (weekly refit, test 2025-10-13 to 2026-10-10)

Models: *naive* = same weekday last week; *calendar* = ridge on day-of-week, holiday, month and the latest available lags; *calendar + weather* adds the day's observed weather as a stand-in for a perfect forecast. *Within ±30%* is the share of days whose error is under 30%, close to the operator's '70% accuracy three days ahead'.

| feed | h | model | days | WAPE % | within ±30% |
|---|---|---|---|---|---|
| Fukui Station (people) | 1d | naive | 340 | 19.28 | 0.84 |
| Fukui Station (people) | 1d | calendar | 338 | 11.88 | 0.95 |
| Fukui Station (people) | 1d | calendar+weather | 338 | 11.95 | 0.94 |
| Fukui Station (people) | 3d | naive | 340 | 19.28 | 0.84 |
| Fukui Station (people) | 3d | calendar | 338 | 14.43 | 0.90 |
| Fukui Station (people) | 3d | calendar+weather | 338 | 14.64 | 0.90 |
| Tojinbo (people) | 1d | naive | 356 | 36.47 | 0.54 |
| Tojinbo (people) | 1d | calendar | 353 | 23.29 | 0.73 |
| Tojinbo (people) | 1d | calendar+weather | 353 | 21.00 | 0.76 |
| Tojinbo (people) | 3d | naive | 356 | 36.47 | 0.54 |
| Tojinbo (people) | 3d | calendar | 352 | 27.16 | 0.65 |
| Tojinbo (people) | 3d | calendar+weather | 352 | 25.12 | 0.70 |
| Rainbow Line lot 1 (cars) | 1d | naive | 301 | 41.78 | 0.44 |
| Rainbow Line lot 1 (cars) | 1d | calendar | 295 | 33.95 | 0.51 |
| Rainbow Line lot 1 (cars) | 1d | calendar+weather | 294 | 29.05 | 0.60 |
| Rainbow Line lot 1 (cars) | 3d | naive | 301 | 41.78 | 0.44 |
| Rainbow Line lot 1 (cars) | 3d | calendar | 296 | 38.50 | 0.40 |
| Rainbow Line lot 1 (cars) | 3d | calendar+weather | 295 | 33.29 | 0.51 |

## C. Busy-day warning three days ahead

A busy day is a day in the site's top 20% (training-period threshold). For Rainbow Line, also *lot 2 in use* (≥20 plates at the overflow lot), which is what triggers the shuttle and extra staff. Logistic regression on the same features, same rolling origin.

| trigger | features | test days | busy share | AUC | precision | recall |
|---|---|---|---|---|---|---|
| Fukui Station (people): top 20% day | calendar | 338 | 0.30 | 0.92 | 0.79 | 0.63 |
| Tojinbo (people): top 20% day | calendar | 352 | 0.30 | 0.91 | 0.82 | 0.64 |
| Rainbow Line lot 1 (cars): top 20% day | calendar | 296 | 0.40 | 0.81 | 0.78 | 0.45 |
| Rainbow Line: lot 2 in use | calendar | 297 | 0.23 | 0.87 | 0.60 | 0.55 |
| Fukui Station (people): top 20% day | calendar+weather | 338 | 0.30 | 0.91 | 0.80 | 0.59 |
| Tojinbo (people): top 20% day | calendar+weather | 352 | 0.30 | 0.93 | 0.88 | 0.60 |
| Rainbow Line lot 1 (cars): top 20% day | calendar+weather | 295 | 0.40 | 0.88 | 0.86 | 0.51 |
| Rainbow Line: lot 2 in use | calendar+weather | 296 | 0.23 | 0.90 | 0.84 | 0.68 |

## D. Counts outside opening hours (Rainbow Line road open about 08:00 to 18:00)

| feed | plates 19:00 to 07:00 | share of all |
|---|---|---|
| rl1 | 852.000 | 0.007 |
| rl2 | 51.000 | 0.004 |
