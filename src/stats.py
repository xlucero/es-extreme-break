"""Survival statistics on the per-session feature table.

Cumulative incidence, Wilson intervals, discrete-time hazard rate,
and a first-half / second-half stability check.
"""

import math
import pandas as pd


def wilson(successes, n, z=1.96):
    """95% Wilson score interval for a proportion. Returns (lo, hi)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (center - margin, center + margin)


def minute_grid(start="11:00", end="12:00"):
    """Every minute in the test window, as 'HH:MM' strings."""
    return list(pd.date_range(start, end, freq="1min").strftime("%H:%M"))


def cumulative_incidence(table, grid, subset=None):
    """Fraction of sessions broken by each minute. Returns a DataFrame."""
    t = table if subset is None else table[subset]
    n = len(t)
    broke = t["first_break_minute"].dropna()

    rows = []
    for m in grid:
        k = (broke <= m).sum()
        lo, hi = wilson(k, n)
        rows.append({"minute": m, "broken": k, "n": n,
                     "rate": k / n, "lo": lo, "hi": hi})
    return pd.DataFrame(rows)


def hazard_blocks(table, grid, block=5):
    """Discrete-time hazard: of sessions still unbroken, the fraction
    that break during each block."""
    broke = table["first_break_minute"].dropna()
    rows = []
    for i in range(0, len(grid) - 1, block):
        lo_m = grid[i]
        hi_m = grid[min(i + block, len(grid) - 1)]
        at_risk = (table["first_break_minute"].isna() |
                   (table["first_break_minute"] > lo_m)).sum()
        events = ((broke > lo_m) & (broke <= hi_m)).sum()
        rate = events / at_risk if at_risk else float("nan")
        rows.append({"block": f"{lo_m}-{hi_m}", "at_risk": at_risk,
                     "events": events, "hazard": rate})
    return pd.DataFrame(rows)


def summary(table, cutoffs=("11:30", "11:45", "12:00")):
    """Headline rates with Wilson intervals, overall and by class."""
    n = len(table)
    broke = table["first_break_minute"].dropna()
    with_t = table.loc[table["break_class"] == "with_trend", "first_break_minute"]
    counter = table.loc[table["break_class"] == "counter_trend", "first_break_minute"]

    rows = []
    for c in cutoffs:
        for name, series in [("any break", broke),
                             ("with-trend", with_t),
                             ("counter-trend", counter)]:
            k = (series <= c).sum()
            lo, hi = wilson(k, n)
            rows.append({"cutoff": c, "measure": name, "k": k, "n": n,
                         "rate": k / n, "lo": lo, "hi": hi})
    return pd.DataFrame(rows)


def distance_strata(table, cutoff="12:00"):
    """Break rate by how far price sat from the nearest reference level
    at 10:59. Stratification, used both to control for distance and to
    study it."""
    t = table.copy()
    t["min_dist"] = t[["dist_to_ref_high", "dist_to_ref_low"]].min(axis=1)
    t["min_dist_pct"] = t["min_dist"] / t["ref_range"]
    broke = t["first_break_minute"].fillna("99:99") <= cutoff

    bands = [("<= 1 pt", t["min_dist"] <= 1),
             ("1 to 2", (t["min_dist"] > 1) & (t["min_dist"] <= 2)),
             ("2 to 5", (t["min_dist"] > 2) & (t["min_dist"] <= 5)),
             ("5 to 10", (t["min_dist"] > 5) & (t["min_dist"] <= 10)),
             ("> 10 pts", t["min_dist"] > 10)]

    rows = []
    for label, mask in bands:
        n, k = mask.sum(), (mask & broke).sum()
        lo, hi = wilson(k, n)
        rows.append({"band": label, "n": n, "broke": k,
                     "rate": k / n if n else float("nan"),
                     "lo": lo, "hi": hi,
                     "median_pct_of_range": t.loc[mask, "min_dist_pct"].median()})
    return pd.DataFrame(rows)


def preregistered(table, cutoff="12:00"):
    """The two thresholds predicted before these numbers were computed."""
    t = table.copy()
    t["min_dist"] = t[["dist_to_ref_high", "dist_to_ref_low"]].min(axis=1)
    broke = t["first_break_minute"].fillna("99:99") <= cutoff

    rows = []
    for label, mask, predicted in [
            ("within 2 pts", t["min_dist"] <= 2, 0.80),
            ("more than 10 pts", t["min_dist"] > 10, 0.50)]:
        n, k = mask.sum(), (mask & broke).sum()
        lo, hi = wilson(k, n)
        rows.append({"band": label, "n": n, "rate": k / n,
                     "lo": lo, "hi": hi, "predicted_floor": predicted,
                     "verdict": "passes" if lo >= predicted
                                else ("inconclusive" if hi >= predicted else "fails")})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    table = pd.read_csv("output/session_features.csv")
    grid = minute_grid()

    print("=== headline rates (Wilson 95%) ===")
    print(summary(table).to_string(index=False))

    print("\n=== hazard rate, 5-minute blocks ===")
    print(hazard_blocks(table, grid).to_string(index=False))

    print("\n=== time to first break, minutes past 11:00 ===")
    mins = pd.to_datetime(table["first_break_minute"].dropna(), format="%H:%M")
    offs = (mins - pd.Timestamp("1900-01-01 11:00")).dt.total_seconds() / 60
    print(f"median {offs.median():.0f}   q25 {offs.quantile(.25):.0f}"
          f"   q75 {offs.quantile(.75):.0f}   censored {table['first_break_minute'].isna().sum()}")

    print("\n=== stability: first half vs second half ===")
    half = len(table) // 2
    for label, part in [("first 170", table.iloc[:half]),
                        ("last 170", table.iloc[half:])]:
        s = summary(part, cutoffs=("12:00",))
        r = s[s["measure"] == "any break"].iloc[0]
        print(f"{label}: {r['rate']:.3f}  [{r['lo']:.3f}, {r['hi']:.3f}]  n={int(r['n'])}")

    print("\n=== break rate by distance to nearest level at 10:59 ===")
    print(distance_strata(table).to_string(index=False))

    print("\n=== pre-registered thresholds ===")
    print(preregistered(table).to_string(index=False))

    distance_strata(table).to_csv("output/distance_strata.csv", index=False)
    preregistered(table).to_csv("output/preregistered.csv", index=False)

    cumulative_incidence(table, grid).to_csv("output/cumulative_incidence.csv", index=False)
    hazard_blocks(table, grid).to_csv("output/hazard_blocks.csv", index=False)
    summary(table).to_csv("output/summary_rates.csv", index=False)
    print("\nwrote 3 CSVs to output/")