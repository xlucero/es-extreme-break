"""Charts for the extreme-break study."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from stats import minute_grid, cumulative_incidence, hazard_blocks

INK, ACCENT, MUTED = "#1a1a1a", "#2563eb", "#9ca3af"


def ticks(grid, every=10):
    """Index positions and labels for every Nth minute."""
    pos = list(range(0, len(grid), every))
    return pos, [grid[i] for i in pos]


def chart_cumulative(table, grid, path):
    """Cumulative incidence: any break, with-trend, counter-trend."""
    fig, ax = plt.subplots(figsize=(9, 5))

    series = [("Any break", None, INK),
              ("With-trend", table["break_class"] == "with_trend", ACCENT),
              ("Counter-trend", table["break_class"] == "counter_trend", MUTED)]

    for label, mask, color in series:
        if mask is None:
            ci = cumulative_incidence(table, grid)
        else:
            sub = table.copy()
            sub.loc[~mask, "first_break_minute"] = None
            ci = cumulative_incidence(sub, grid)
        ax.plot(range(len(grid)), ci["rate"] * 100, label=label, color=color, lw=2)

    for cut in ["11:30", "11:45", "12:00"]:
        ax.axvline(grid.index(cut), color=MUTED, ls=":", lw=1)

    pos, labels = ticks(grid)
    ax.set_xticks(pos)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Eastern time")
    ax.set_ylabel("% of sessions broken by this minute")
    ax.set_title(f"Cumulative incidence of a new extreme (n={len(table)})")
    ax.set_ylim(0, 80)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_hazard(table, grid, path):
    """Hazard rate per 5-minute block."""
    h = hazard_blocks(table, grid)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(range(len(h)), h["hazard"] * 100, color=ACCENT, alpha=0.8)
    ax.set_xticks(range(len(h)))
    ax.set_xticklabels([b[:5] for b in h["block"]], rotation=45, ha="right")
    ax.set_xlabel("5-minute block, start time")
    ax.set_ylabel("% of still-unbroken sessions that break")
    ax.set_title("Hazard rate: the chance of a break given it hasn't happened yet")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_stability(table, grid, path):
    """First half vs second half, cumulative."""
    half = len(table) // 2
    fig, ax = plt.subplots(figsize=(9, 5))

    for label, part, color in [("First 170 sessions", table.iloc[:half], ACCENT),
                               ("Last 170 sessions", table.iloc[half:], INK)]:
        ci = cumulative_incidence(part, grid)
        ax.plot(range(len(grid)), ci["rate"] * 100, label=label, color=color, lw=2)
        ax.fill_between(range(len(grid)), ci["lo"] * 100, ci["hi"] * 100,
                        color=color, alpha=0.12)

    pos, labels = ticks(grid)
    ax.set_xticks(pos)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Eastern time")
    ax.set_ylabel("% of sessions broken by this minute")
    ax.set_title("Stability check: shaded bands are 95% Wilson intervals")
    ax.set_ylim(0, 90)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_by_distance(table, grid, path):
    """Cumulative incidence split by distance to the nearest level at 10:59."""
    t = table.copy()
    t["min_dist"] = t[["dist_to_ref_high", "dist_to_ref_low"]].min(axis=1)
    bands = [("Within 2 pts", t["min_dist"] <= 2, ACCENT),
             ("2 to 10 pts", (t["min_dist"] > 2) & (t["min_dist"] <= 10), INK),
             ("More than 10 pts", t["min_dist"] > 10, MUTED)]

    fig, ax = plt.subplots(figsize=(9, 5))
    for label, mask, color in bands:
        ci = cumulative_incidence(t[mask], grid)
        ax.plot(range(len(grid)), ci["rate"] * 100, color=color, lw=2,
                label=f"{label}  (n={int(mask.sum())})")
        ax.fill_between(range(len(grid)), ci["lo"] * 100, ci["hi"] * 100,
                        color=color, alpha=0.10)

    for cut in ["11:30", "11:45"]:
        ax.axvline(grid.index(cut), color=MUTED, ls=":", lw=1)

    pos, labels = ticks(grid)
    ax.set_xticks(pos)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Eastern time")
    ax.set_ylabel("% of sessions broken by this minute")
    ax.set_title("Where price sat at 10:59 decides almost everything")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    table = pd.read_csv("output/session_features.csv")
    grid = minute_grid()

    chart_cumulative(table, grid, "output/fig1_cumulative.png")
    chart_hazard(table, grid, "output/fig2_hazard.png")
    chart_stability(table, grid, "output/fig3_stability.png")
    chart_by_distance(table, grid, "output/fig4_by_distance.png")
    print("wrote 3 figures to output/")