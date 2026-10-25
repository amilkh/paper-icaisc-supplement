# Window sensitivity (scan 07)

Headline results under four definitions of the active-hours window. Rain effect: JMA, % per 10 mm with 95% interval. Forecast test: 3-day WAPE, calendar ridge vs ridge with the archived forecast, Diebold-Mariano p.

| window | site | rain % per 10 mm | 3d WAPE calendar | 3d WAPE + forecast | DM p |
|---|---|---|---|---|---|
| 1% share | Fukui Station | -3 [-5, -1] | 14.43 | 14.62 | 0.22 |
| 1% share | Tojinbo | -9 [-12, -5] | 27.16 | 25.87 | 0.16 |
| 1% share | Rainbow Line lot 1 | -35 [-44, -23] | 38.50 | 31.78 | 0.00 |
| 2% share (paper) | Fukui Station | -3 [-6, -1] | 14.43 | 14.67 | 0.12 |
| 2% share (paper) | Tojinbo | -9 [-13, -5] | 27.16 | 26.04 | 0.22 |
| 2% share (paper) | Rainbow Line lot 1 | -37 [-47, -24] | 38.50 | 31.87 | 0.00 |
| 5% share | Fukui Station | -3 [-6, -1] | 14.43 | 14.69 | 0.08 |
| 5% share | Tojinbo | -10 [-16, -5] | 27.16 | 26.09 | 0.25 |
| 5% share | Rainbow Line lot 1 | -37 [-49, -22] | 38.50 | 32.14 | 0.00 |
| fixed 09:00-17:00 | Fukui Station | -3 [-6, -1] | 14.43 | 14.70 | 0.08 |
| fixed 09:00-17:00 | Tojinbo | -9 [-13, -5] | 27.16 | 26.18 | 0.28 |
| fixed 09:00-17:00 | Rainbow Line lot 1 | -40 [-51, -26] | 38.50 | 32.59 | 0.00 |

## Faces warning at Rainbow Line (lots 1+2, paper outage rule): precision and recall

| series | weather | days | AUC | precision | recall |
|---|---|---|---|---|---|
| plates | calendar | 295 | 0.83 [0.77, 0.89] | 0.78 | 0.50 |
| plates | forecast | 295 | 0.88 [0.84, 0.92] | 0.84 | 0.60 |
| faces | calendar | 296 | 0.91 [0.86, 0.96] | 0.90 | 0.41 |
| faces | forecast | 296 | 0.93 [0.87, 0.98] | 1.00 | 0.50 |
