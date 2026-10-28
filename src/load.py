"""Load a Sierra Chart 1-minute bar export into a tidy DataFrame."""

import pandas as pd


def load_bars(path):
    """Read a Sierra Chart bar export and return a tidy DataFrame.

    Does no filtering. Exclusions belong in sessions.py.
    """
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]

    df["timestamp"] = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%Y-%m-%d %H:%M:%S.%f",
    )

    df["tod"] = df["timestamp"].dt.strftime("%H:%M")

    # Valid only because RTH sessions never cross midnight.
    # Overnight data (ONH/ONL) will need the session's close date instead.
    df["session_date"] = df["timestamp"].dt.date

    return df


if __name__ == "__main__":
    import sys

    df = load_bars(sys.argv[1])
    print("rows:", len(df))
    print("sessions:", df["session_date"].nunique())
    print("range:", df["session_date"].min(), "->", df["session_date"].max())
    print(df[["timestamp", "session_date", "tod", "High", "Low"]].head(3))