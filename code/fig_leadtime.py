"""Figure: daily WAPE by lead time, one panel per site stacked for column width."""
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = Path(__file__).resolve().parent.parent / "out"; FIG = OUT / "figures"
lt = pd.read_csv(OUT / "20261012_lead_time.csv")
plt.rcParams.update({"font.family": "serif", "font.size": 7})
fig, axes = plt.subplots(3, 1, figsize=(3.5, 4.7), sharex=True)
styles = [("naive", ":", "#777777", "Same weekday last week"), ("calendar", "--", "#2a78d6", "Calendar ridge"),
          ("ridge_fcst", "-", "#eb6834", "Ridge + forecast weather"), ("gbm", "-.", "#1baf7a", "Boosting + forecast weather")]
for ax, (site, g) in zip(axes, lt.groupby("site", sort=False)):
    for m, ls, col, lab in styles:
        gg = g[g.model == m]; ax.plot(gg.lead_days, gg.wape, ls, color=col, marker="o", ms=2.5, lw=1.2, label=lab)
    ax.set_title(site, fontsize=7, loc="left", pad=2); ax.grid(axis="y", color="#e6e6e6", lw=0.5)
    ax.spines[["top", "right"]].set_visible(False); ax.tick_params(length=2, labelsize=6); ax.set_xticks(range(1, 8))
axes[0].legend(frameon=False, fontsize=6, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.08))
axes[-1].set_xlabel("Lead time (days)", fontsize=7); fig.supylabel("Daily WAPE (%)", fontsize=7, x=0.01)
fig.tight_layout(h_pad=0.6); fig.savefig(FIG / "lead_time_wape.pdf"); fig.savefig(FIG / "lead_time_wape.png", dpi=400); print("ok")
