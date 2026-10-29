"""Median time to break, by distance band.

Reads output/session_features.csv rather than rebuilding it, so this is a
throwaway probe. Folded into stats.py only if the numbers are worth charting.
"""

import pandas as pd

BANDS = [(0, 1), (1, 2), (2, 5), (5, 10), (10, float("inf"))]
BAND_LABELS = ["<= 1 pt", "1 - 2 pt", "2 - 5 pt", "5 - 10 pt", "> 10 pt"]


def minutes_past_eleven(hhmm):
    if pd.isna(hhmm) or hhmm == "":
        return None
    hours, minutes = str(hhmm).split(":")
    return (int(hours) - 11) * 60 + int(minutes)


def band_of(distance):
    for label, (low, high) in zip(BAND_LABELS, BANDS):
        if (low == 0 and distance <= high) or (low < distance <= high):
            return label
    return None


def main(path="output/session_features.csv"):
    df = pd.read_csv(path)
    df["nearest_distance"] = df[["dist_to_ref_high", "dist_to_ref_low"]].min(axis=1)
    df["band"] = df["nearest_distance"].apply(band_of)
    df["minutes_to_break"] = df["first_break_minute"].apply(minutes_past_eleven)

    rows = []
    for label in BAND_LABELS:
        group = df[df["band"] == label]
        broke = group[group["minutes_to_break"].notna()]
        rows.append({
            "band": label,
            "n": len(group),
            "broke": len(broke),
            "median_min": broke["minutes_to_break"].median(),
            "q25_min": broke["minutes_to_break"].quantile(0.25),
            "q75_min": broke["minutes_to_break"].quantile(0.75),
        })

    table = pd.DataFrame(rows)
    print(table.to_string(index=False))
    return table


if __name__ == "__main__":
    main()