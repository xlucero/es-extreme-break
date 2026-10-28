"""Build the per-session feature table: one row per trading session."""

import pandas as pd


def session_features(session, ref_start, ref_end, test_start, test_end):
    """Compute all features for a single session. Returns a dict."""
    ref = session[(session["tod"] >= ref_start) & (session["tod"] <= ref_end)]
    test = session[(session["tod"] >= test_start) & (session["tod"] <= test_end)]

    if len(ref) == 0 or len(test) == 0:
        return None

    ref_high = ref["High"].max()
    ref_low = ref["Low"].min()
    ref_high_minute = ref.loc[ref["High"].idxmax(), "tod"]
    ref_low_minute = ref.loc[ref["Low"].idxmin(), "tod"]

    assert ref_high_minute != ref_low_minute, (
        f"{session['session_date'].iloc[0]}: both extremes in one minute"
    )

    direction = "up" if ref_high_minute > ref_low_minute else "down"
    ref_close = ref["Last"].iloc[-1]

    break_minute, break_side = None, None
    for row in test.itertuples():
        hit_high = row.High >= ref_high
        hit_low = row.Low <= ref_low
        if hit_high or hit_low:
            break_minute = row.tod
            if hit_high and hit_low:
                break_side = "both"
            elif hit_high:
                break_side = "up"
            else:
                break_side = "down"
            break

    if break_side is None:
        break_class = "none"
    elif break_side == "both":
        break_class = "ambiguous"
    elif break_side == direction:
        break_class = "with_trend"
    else:
        break_class = "counter_trend"

    return {
        "session_date": session["session_date"].iloc[0],
        "ref_high": ref_high,
        "ref_high_minute": ref_high_minute,
        "ref_low": ref_low,
        "ref_low_minute": ref_low_minute,
        "ref_range": ref_high - ref_low,
        "prevailing_direction": direction,
        "ref_close": ref_close,
        "dist_to_ref_high": ref_high - ref_close,
        "dist_to_ref_low": ref_close - ref_low,
        "first_break_minute": break_minute,
        "first_break_side": break_side,
        "break_class": break_class,
        "window_high": test["High"].max(),
        "window_high_minute": test.loc[test["High"].idxmax(), "tod"],
        "window_low": test["Low"].min(),
        "window_low_minute": test.loc[test["Low"].idxmin(), "tod"],
    }


def build_table(df, ref_start="09:30", ref_end="10:59",
                test_start="11:00", test_end="12:00"):
    rows = []
    for _, session in df.groupby("session_date"):
        f = session_features(session, ref_start, ref_end, test_start, test_end)
        if f is not None:
            rows.append(f)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    from load import load_bars
    from sessions import filter_sessions

    bars, _ = filter_sessions(load_bars(sys.argv[1]))
    table = build_table(bars)

    print("sessions:", len(table))
    print("\nbreak_class counts:")
    print(table["break_class"].value_counts())
    print("\nprevailing_direction counts:")
    print(table["prevailing_direction"].value_counts())
    print("\nfirst 3 rows:")
    print(table.head(3).to_string())

    table.to_csv("output/session_features.csv", index=False)
    print("\nwrote output/session_features.csv")