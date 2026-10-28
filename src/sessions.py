"""Select complete trading sessions and log what was excluded."""

import pandas as pd


def session_summary(df, window_start="09:30", window_end="11:45"):
    """One row per session: boundaries, bar count, gaps inside the window."""
    expected = pd.date_range(window_start, window_end, freq="1min").strftime("%H:%M")

    rows = []
    for date, g in df.groupby("session_date"):
        present = set(g["tod"])
        rows.append({
            "session_date": date,
            "first_bar": g["tod"].min(),
            "last_bar": g["tod"].max(),
            "n_bars": len(g),
            "window_gaps": sum(1 for t in expected if t not in present),
        })
    return pd.DataFrame(rows)


def filter_sessions(df, session_open="09:30", session_close="16:14"):
    """Keep complete sessions. Return (filtered_df, log)."""
    log = session_summary(df)

    complete = (log["first_bar"] == session_open) & (log["last_bar"] >= session_close)

    log["kept"] = complete
    log["reason"] = ""
    log.loc[log["first_bar"] != session_open, "reason"] = "late open"
    log.loc[log["last_bar"] < session_close, "reason"] = "early close or partial"

    keep_dates = log.loc[log["kept"], "session_date"]
    return df[df["session_date"].isin(keep_dates)].copy(), log


if __name__ == "__main__":
    import sys
    from load import load_bars

    bars = load_bars(sys.argv[1])
    kept, log = filter_sessions(bars)

    print("sessions in:", len(log))
    print("sessions kept:", log["kept"].sum())
    print("\ndropped:")
    print(log[~log["kept"]][["session_date", "first_bar", "last_bar", "reason"]])
    print("\nkept sessions with gaps inside 09:30-11:45:")
    print(log[log["kept"] & (log["window_gaps"] > 0)][["session_date", "window_gaps"]])

    log.to_csv("output/session_log.csv", index=False)
    print("\nwrote output/session_log.csv")