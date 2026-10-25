# Scan 01: cross-site patterns (data @ b89bc2c, 2024-12-20 to 2026-10-10)

Outage days (zero or <80% of 5-min bins) are excluded.

## A. Coverage

| feed | valid days | median/day | max/day |
|---|---|---|---|
| station | 642 | 8,343 | 20,408 |
| tojinbo | 641 | 8,173 | 33,586 |
| rl1 | 607 | 174 | 540 |
| rl2 | 607 | 0 | 376 |

## B. Weekend and holiday uplift (median ÷ weekday median)

| feed | weekend | holiday |
|---|---|---|
| station | 1.49 | 1.65 |
| tojinbo | 2.07 | 2.35 |
| rl1 | 1.84 | 2.20 |
| rl2 | inf | inf |

## C. Cross-site daily correlation

Raw log counts:

|  | station | tojinbo | rl1 | rl2 |
|---|---|---|---|---|
| station | 1.00 | 0.78 | 0.50 | 0.55 |
| tojinbo | 0.78 | 1.00 | 0.64 | 0.60 |
| rl1 | 0.50 | 0.64 | 1.00 | 0.44 |
| rl2 | 0.55 | 0.60 | 0.44 | 1.00 |

Residuals after weekday x month means, holidays excluded (shared shocks such as weather):

|  | station | tojinbo | rl1 | rl2 |
|---|---|---|---|---|
| station | 1.00 | 0.57 | 0.29 | 0.23 |
| tojinbo | 0.57 | 1.00 | 0.44 | 0.35 |
| rl1 | 0.29 | 0.44 | 1.00 | 0.29 |
| rl2 | 0.23 | 0.35 | 0.29 | 1.00 |

## D. Hourly lead-lag (residual cross-correlation, 09:00 to 17:00)

| pair | lag -2h | lag -1h | lag +0h | lag +1h | lag +2h |
|---|---|---|---|---|---|
| rl1 → tojinbo | -0.05 | 0.00 | 0.07 | 0.07 | 0.08 |
| station → tojinbo | 0.03 | 0.05 | 0.05 | 0.05 | 0.03 |
| rl1 → station | 0.00 | 0.03 | 0.04 | 0.03 | 0.01 |
| rl1 → rl2 | 0.03 | -0.01 | -0.03 | 0.01 | 0.05 |

Positive lag: the first feed's intraday deviation precedes the second's by that many hours.

## E. Intraday profile: peak hour and share of the day in the peak hour

| feed | day | peak hour | peak share | 09-12 share | 15-18 share |
|---|---|---|---|---|---|
| station | weekday | 16 | 0.10 | 0.22 | 0.28 |
| station | weekend | 15 | 0.10 | 0.24 | 0.28 |
| station | holiday | 15 | 0.10 | 0.23 | 0.29 |
| tojinbo | weekday | 13 | 0.13 | 0.29 | 0.24 |
| tojinbo | weekend | 13 | 0.14 | 0.29 | 0.25 |
| tojinbo | holiday | 11 | 0.13 | 0.34 | 0.23 |
| rl1 | weekday | 13 | 0.14 | 0.38 | 0.11 |
| rl1 | weekend | 14 | 0.13 | 0.36 | 0.16 |
| rl1 | holiday | 14 | 0.13 | 0.34 | 0.16 |
| rl2 | weekday | 10 | 0.15 | 0.44 | 0.08 |
| rl2 | weekend | 13 | 0.20 | 0.38 | 0.05 |
| rl2 | holiday | 11 | 0.17 | 0.45 | 0.05 |

## F. Rainbow Line plate origin (lot 1 + lot 2)

Share of plates by origin region and kind, count-weighted:

| day type | Fukui | Hokuriku | Kansai | Chubu | Kanto | Other | RentACar | Commercial |
|---|---|---|---|---|---|---|---|---|
| holiday | 0.27 | 0.09 | 0.32 | 0.20 | 0.06 | 0.06 | 0.11 | 0.07 |
| weekday | 0.28 | 0.07 | 0.31 | 0.20 | 0.07 | 0.07 | 0.10 | 0.11 |
| weekend | 0.26 | 0.08 | 0.33 | 0.22 | 0.05 | 0.06 | 0.11 | 0.08 |

By month:

| month | Fukui | Hokuriku | Kansai | Chubu | Kanto | Other | RentACar | Commercial | plates/day |
|---|---|---|---|---|---|---|---|---|---|
| 2024-12 | 0.32 | 0.05 | 0.25 | 0.15 | 0.07 | 0.16 | 0.11 | 0.13 | 86.25 |
| 2025-01 | 0.34 | 0.06 | 0.24 | 0.15 | 0.05 | 0.16 | 0.09 | 0.11 | 81.84 |
| 2025-02 | 0.36 | 0.04 | 0.23 | 0.16 | 0.04 | 0.18 | 0.08 | 0.14 | 57.36 |
| 2025-03 | 0.24 | 0.08 | 0.28 | 0.18 | 0.05 | 0.17 | 0.08 | 0.09 | 153.52 |
| 2025-04 | 0.24 | 0.07 | 0.28 | 0.21 | 0.07 | 0.13 | 0.10 | 0.09 | 214.50 |
| 2025-05 | 0.28 | 0.07 | 0.29 | 0.19 | 0.07 | 0.10 | 0.09 | 0.09 | 190.65 |
| 2025-06 | 0.31 | 0.07 | 0.29 | 0.19 | 0.04 | 0.09 | 0.09 | 0.10 | 148.86 |
| 2025-07 | 0.25 | 0.08 | 0.35 | 0.22 | 0.05 | 0.06 | 0.10 | 0.08 | 147.00 |
| 2025-08 | 0.23 | 0.08 | 0.36 | 0.22 | 0.07 | 0.05 | 0.11 | 0.07 | 243.73 |
| 2025-09 | 0.25 | 0.08 | 0.34 | 0.21 | 0.06 | 0.05 | 0.12 | 0.08 | 189.89 |
| 2025-10 | 0.24 | 0.09 | 0.33 | 0.23 | 0.07 | 0.06 | 0.12 | 0.09 | 249.29 |
| 2025-11 | 0.26 | 0.09 | 0.32 | 0.23 | 0.06 | 0.05 | 0.12 | 0.09 | 320.47 |
| 2025-12 | 0.33 | 0.07 | 0.30 | 0.20 | 0.06 | 0.04 | 0.12 | 0.11 | 109.11 |
| 2026-01 | 0.67 | 0.04 | 0.17 | 0.07 | 0.02 | 0.02 | 0.09 | 0.25 | 17.29 |
| 2026-02 | 0.34 | 0.10 | 0.34 | 0.16 | 0.02 | 0.03 | 0.08 | 0.11 | 133.54 |
| 2026-03 | 0.31 | 0.08 | 0.34 | 0.20 | 0.04 | 0.04 | 0.10 | 0.10 | 215.29 |
| 2026-04 | 0.31 | 0.07 | 0.32 | 0.20 | 0.06 | 0.04 | 0.10 | 0.11 | 221.90 |
| 2026-05 | 0.30 | 0.09 | 0.31 | 0.19 | 0.06 | 0.05 | 0.10 | 0.10 | 340.87 |
| 2026-06 | 0.35 | 0.07 | 0.30 | 0.19 | 0.05 | 0.04 | 0.10 | 0.11 | 229.63 |
| 2026-07 | 0.26 | 0.07 | 0.33 | 0.23 | 0.05 | 0.04 | 0.11 | 0.09 | 251.81 |
| 2026-08 | 0.23 | 0.07 | 0.35 | 0.25 | 0.07 | 0.04 | 0.12 | 0.07 | 392.74 |
| 2026-09 | 0.27 | 0.08 | 0.34 | 0.20 | 0.06 | 0.05 | 0.12 | 0.09 | 259.37 |
| 2026-10 | 0.26 | 0.08 | 0.32 | 0.22 | 0.06 | 0.05 | 0.10 | 0.09 | 291.80 |

Origin mix on quiet versus busy days (unweighted daily means):

| share | quiet days (bottom 25%) | busy days (top 25%) |
|---|---|---|
| Fukui | 0.47 | 0.26 |
| Hokuriku | 0.05 | 0.08 |
| Kansai | 0.21 | 0.33 |
| Chubu | 0.12 | 0.22 |
| Kanto | 0.05 | 0.06 |
| Other | 0.10 | 0.05 |
| RentACar | 0.09 | 0.11 |
| Commercial | 0.16 | 0.08 |

## G. Does lot 2 open as overflow?

| lot 1 plates/day | days | rl2_median | rl2_share |
|---|---|---|---|
| (0.999, 78.0] | 123.00 | 0.00 | 0.00 |
| (78.0, 146.2] | 119.00 | 0.00 | 0.00 |
| (146.2, 202.0] | 123.00 | 0.00 | 0.00 |
| (202.0, 294.0] | 119.00 | 0.00 | 0.00 |
| (294.0, 540.0] | 120.00 | 62.00 | 0.14 |
