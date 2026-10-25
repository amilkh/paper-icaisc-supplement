# Scan 09: faces vs plates busy-day warning at Rainbow Line, as day counts

Lots 1+2, paper outage rule, three days ahead, rolling top-20% threshold, logistic regression as in scan03. Flagged = days with predicted probability >= 0.5; correct = flagged days that were busy.

| series | weather | test days | busy days | flagged | correct | precision | recall |
|---|---|---|---|---|---|---|---|
| plates | calendar | 295 | 107 | 69 | 54 | 0.78 | 0.50 |
| plates | forecast | 295 | 107 | 76 | 64 | 0.84 | 0.60 |
| faces | calendar | 296 | 86 | 39 | 35 | 0.90 | 0.41 |
| faces | forecast | 296 | 86 | 43 | 43 | 1.00 | 0.50 |

