"""Figure: daily detections at the three camera sites over the full period.
Small multiples (one axis each, scales differ by 40x), thin daily line in the
site colour, 7-day mean on top, outage days left as gaps.
Writes ../out/figures/daily_counts.pdf and .png."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from common import daily_counts
FIG = Path(__file__).resolve().parent.parent / "out" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
D = daily_counts()
panels = [("station", "Fukui Station (people)", "#2a78d6"), ("tojinbo", "Tojinbo (people)", "#eb6834"), ("rl1", "Rainbow Line lot 1 (vehicles)", "#1baf7a")]
plt.rcParams.update({"font.family": "serif", "font.size": 7})
fig, axes = plt.subplots(3, 1, figsize=(3.5, 3.6), sharex=True)
for ax, (k, name, col) in zip(axes, panels):
    s = D[k]
    ax.plot(s.index, s.values, color=col, lw=0.5, alpha=0.45)
    ax.plot(s.index, s.rolling(7, min_periods=4).mean().values, color=col, lw=1.4, label="7-day mean")
    ax.set_title(name, fontsize=7, loc="left", pad=2)
    ax.grid(axis="y", color="#e6e6e6", lw=0.5); ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2, labelsize=6)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}"))
axes[0].legend(frameon=False, fontsize=6, loc="upper left")
axes[-1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])); axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
fig.supylabel("Daily detections", fontsize=7, x=0.01)
fig.tight_layout(h_pad=0.6); fig.savefig(FIG / "daily_counts.pdf"); fig.savefig(FIG / "daily_counts.png", dpi=400)
print("ok")
