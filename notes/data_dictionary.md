# Data dictionary

## output/session_features.csv

One row per session. 340 rows after exclusions.

| Column | Type | Units | Definition |
|---|---|---|---|
| session_date | date | YYYY-MM-DD | Calendar date of the RTH session |
| ref_high | float | index points | Highest `High` among bars 09:30–10:59 inclusive |
| ref_high_minute | time | HH:MM | Start-stamp of the bar that set `ref_high`; first occurrence if tied |
| ref_low | float | index points | Lowest `Low` among bars 09:30–10:59 inclusive |
| ref_low_minute | time | HH:MM | Start-stamp of the bar that set `ref_low`; first occurrence if tied |
| ref_range | float | index points | `ref_high` − `ref_low` |
| prevailing_direction | category | up / down | `up` if `ref_high_minute` is later than `ref_low_minute`, `down` otherwise. The extreme set later defines the side price was working toward at the end of the reference window |
| ref_close | float | index points | `Last` of the 10:59 bar |
| dist_to_ref_high | float | index points | `ref_high` − `ref_close`. Zero or positive by construction |
| dist_to_ref_low | float | index points | `ref_close` − `ref_low`. Zero or positive by construction |
| first_break_minute | time | HH:MM | Start-stamp of the first bar in 11:00–12:00 inclusive where `High` >= `ref_high` or `Low` <= `ref_low`. Empty if no break |
| first_break_side | category | up / down / empty | Which extreme was exceeded first. Empty if no break |
| break_class | category | none / with_trend / counter_trend / ambiguous | `with_trend` if `first_break_side` equals `prevailing_direction`; `counter_trend` if opposite; `none` if no break; `ambiguous` if both extremes exceeded within the same bar |
| window_high | float | index points | Highest `High` among bars 11:00–12:00 inclusive |
| window_high_minute | time | HH:MM | Start-stamp of the bar that set `window_high` |
| window_low | float | index points | Lowest `Low` among bars 11:00–12:00 inclusive |
| window_low_minute | time | HH:MM | Start-stamp of the bar that set `window_low` |

## Conventions

**Bar timestamps are start-stamps.** The bar labeled 09:30 covers 09:30:00 through 09:30:59. A reference window of 09:30–10:59 inclusive therefore spans the first ninety minutes of the session and ends the instant the 11:00 bar opens.

**Breaks use `>=` and `<=`, not strict inequality.** Trading exactly at the prior extreme counts as a touch. This is a definitional choice made before results were examined; the strict-inequality variant was not tested.

**One event per session.** Only the first break is recorded. A session that breaks the high at 11:04 and the low at 11:40 appears once, as an up break at 11:04.

**Sessions with no break are censored, not missing.** They are retained in every denominator. `first_break_minute` empty means the session reached 12:00 without a break, which is an observed outcome, not absent data.

**Daylight saving.** Session times are local exchange time as exported. Every session in the file opens at 09:30, so no timezone conversion is applied and timestamps are parsed as naive.

## Source data

ES continuous futures, 1-minute bars, regular trading hours only, exported from Sierra Chart. 138,304 rows covering 2025-06-02 through 2026-10-14. Raw price data is not included in this repository because exchange licensing restricts redistribution. The code expects a file at `data/raw/ES_1min_RTH_500d.txt` with columns matching the Sierra Chart export format.

## Exclusions

| Session | Reason |
|---|---|
| 2025-07-03 | Early close at 13:14; test window present but session structure differs |
| 2026-10-14 | Partial session, data ends 15:51 |

Two sessions with single missing minutes were retained: 2025-08-29 (no 11:16 bar) and 2026-06-12 (no 09:43 bar). Both are zero-trade minutes, not data gaps.