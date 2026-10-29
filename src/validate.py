"""Pull 10 random sessions for manual checking against the chart."""

import pandas as pd

SEED = 42


def sample_sessions(table, n=10, seed=SEED):
    """Reproducible random sample. The seed is why anyone can re-run this."""
    return table.sample(n=n, random_state=seed).sort_values("session_date")


def to_markdown(sample, path):
    lines = ["# Hand-validation", "",
             f"Ten sessions drawn at random (seed={SEED}) and checked by eye",
             "against the Sierra Chart display. Fill the Agrees column yourself.",
             "", "| Session | Ref high | at | Ref low | at | Dir | First break | Side | Agrees |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, r in sample.iterrows():
        brk = r["first_break_minute"] if pd.notna(r["first_break_minute"]) else "none"
        side = r["first_break_side"] if pd.notna(r["first_break_side"]) else "-"
        lines.append(f"| {r['session_date']} | {r['ref_high']} | {r['ref_high_minute']} "
                     f"| {r['ref_low']} | {r['ref_low_minute']} | {r['prevailing_direction']} "
                     f"| {brk} | {side} | |")
    lines += ["", "## Result", "", "Checked: 10. Agreed: __. Disagreed: __.", ""]
    open(path, "w").write("\n".join(lines))


if __name__ == "__main__":
    table = pd.read_csv("output/session_features.csv")
    s = sample_sessions(table)
    to_markdown(s, "output/hand_validation.md")
    print(s[["session_date", "ref_high", "ref_high_minute", "ref_low",
             "ref_low_minute", "prevailing_direction", "first_break_minute",
             "first_break_side"]].to_string(index=False))
    print("\nwrote output/hand_validation.md")