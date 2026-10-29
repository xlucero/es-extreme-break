# Project Map

ES New-Extreme Probability Study

---

## The question

How often does ES make a new session extreme between 11:00 and 12:00 Eastern, relative to the extreme already set between 09:30 and 10:59? And does the side the market has most recently been pushing matter?

---

## Methods and process

**Discrete-time survival analysis.** Each session either experiences an event
(a break) at a known minute or reaches the end of the window without one. The
99 non-breaking sessions are right-censored and remain in every denominator.
The cumulative break curve is a cumulative incidence function; the five-minute
block chart is a discrete-time hazard rate. The hazard calculation was derived
here by reasoning about a shrinking pool of unbroken sessions, which turned out
to be the standard definition.

**Event study design.** The 09:30–10:59 reference window is an estimation
window and the 11:00–12:00 test window is an event window. This is the standard
two-window structure in empirical finance research.

**CRISP-DM.** Project process: business understanding (scoping), data
understanding (the validation pass), data preparation (`load`, `sessions`,
`features`), modeling (`stats`), evaluation (hand-validation, stability check,
the confound), deployment (README, figures, writeup).

**Pre-registration.** Thresholds and predicted rates committed to
`notes/prediction.md` before any statistics were computed.

**Stratification.** Distance is a confounder of the direction result and a
predictor in its own right. It is held constant for the first question and
varied for the second.

---

## Data

|  |  |
| :---- | :---- |
| Instrument | ES (CME), 1-minute bars, RTH only |
| Source | Sierra Chart export, 500 calendar days |
| Range | 2025-06-02 to 2026-10-14 |
| Raw sessions | 342 |
| Analysed sessions | 340 |
| Timestamps | Eastern wall-clock, DST already applied by Sierra |
| Bar convention | Start-stamped (the 11:30 bar covers 11:30:00-11:30:59) |

**Exclusions**

- `2025-07-03` — half day, closes 13:14. Dropped.  
- `2026-10-14` — partial session, ends 15:51. Dropped.

**Kept, with reason**

- `2025-08-29` missing 11:16, `2026-06-12` missing 09:43. Both are zero-trade minutes that Sierra omits. A minute with no trades cannot contain a new extreme, so dropping these sessions would remove information for nothing.

**Known data hazard (does not affect this study)**

The IB columns carry the *completed* initial-balance values on every bar of the session, including bars before 10:30. Safe here, because every window starts at or after 10:30. Dangerous in the opening-type project if IB levels are read at pre-10:30 timestamps.

---

## Definitions (locked)

| Term | Definition |
| :---- | :---- |
| Reference window | 09:30 through 10:59 inclusive |
| Reference high | Max of bar `High` over the reference window |
| Reference low | Min of bar `Low` over the reference window |
| Prevailing direction | Side whose extreme was set *later* in the reference window |
| Test window | 11:00 through 12:00 inclusive |
| Break | Bar `High` \>= reference high, or bar `Low` \<= reference low |
| Event | First break only. One per session. |
| Break class | `none`, `with_trend`, or `counter_trend` |
| Named cutoffs | 11:30, 11:45, 12:00 — fixed before running |

Verified: zero sessions where the reference high and low were set in the same minute. Code asserts against it anyway, since the same code will run on NQ.

**Direction balance:** 180 up / 162 down. No structural lean.

---

## Pre-registered priors

Logged 2026-10-27, before any statistics were computed.

| Outcome, 11:00-12:00 | Predicted |
| :---- | :---- |
| With-trend break | 50% |
| No break | 30% |
| Counter-trend break | 20% |

---

## Phase 1 — the shippable project

**The per-session table is the product.** Charts and statistics are computed from it. One row per session:

session\_date

ref\_high, ref\_high\_minute

ref\_low,  ref\_low\_minute

prevailing\_direction

close\_1059

dist\_to\_ref\_high, dist\_to\_ref\_low

first\_break\_minute, first\_break\_side, break\_class

window\_high, window\_high\_minute

window\_low,  window\_low\_minute

The distance and window-extreme columns are not analysed in Phase 1\. They are captured now so Phase 2 is arithmetic on an existing table rather than a re-run.

**Modules**

| File | Does |
| :---- | :---- |
| `src/load.py` | Parse export, build timestamp and session-date columns |
| `src/sessions.py` | Apply exclusions, emit a dropped-sessions log |
| `src/features.py` | Build the per-session table |
| `src/stats.py` | Rates, Wilson intervals, hazard rates, stability split |
| `src/chart.py` | The three charts |

Times and file paths are function arguments, never typed inside a function body. This is what makes the 10:30 variant and the NQ run one line each instead of a second copy of the code.

**Outputs**

1. **Cumulative break curve** — 11:00 to 12:00, every minute. Three lines: any break, with-trend, counter-trend. Markers at the three named cutoffs.  
2. **Hazard rate** — 5-minute blocks, bar chart.  
3. **Stability check** — first 170 sessions vs last 170, cumulative, overlaid.  
4. **Results table** — named cutoffs with Wilson intervals; median time to break with quartiles.

Plus the 09:30-10:29 reference variant, which measures how often price breaks the initial balance in the following hour.

**Validation**

Ten randomly chosen sessions checked by hand against the Sierra chart. Comparison committed as a file.

**Done when**

Working code, README (question / method / definitions / results / limitations), data dictionary, hand-validation file, and a plain-language writeup.

---

## Phase 2 — after Phase 1 ships

Ordered by value.

1. **NQ replication.** Code is free; the hand-validation is not. First item after publishing.  
2. **Distance-controlled comparison.** The confound test. Compare break rates among sessions where the distance to each extreme is similar.  
3. **Extension and fade.** Conditional on a break: how far past the reference extreme, how many minutes to the furthest point, how much retraced by window end. Feeds R-multiple sizing and the expectancy model.  
4. **11:31-12:30 continuation.** New event definition.  
5. **Re-export with all studies on** — VWAP and bands, prior day high/low/close, prior value area, POC. One careful export, not five rushed ones.

Deferred: day-of-week splits. 340 sessions is about 68 per weekday, intervals too wide to say anything.

---

## Glossary

**Cumulative rate** — of all sessions, the fraction that have broken by minute T.

**Marginal rate** — of all sessions, the fraction that broke during one block. Always sags late, because the pool of unbroken sessions is shrinking.

**Hazard rate** — of sessions *not yet broken* at the start of a block, the fraction that broke during it. Strips out the shrinking-pool effect. This is the number that answers "is waiting past 11:30 still worth it."

**Wilson interval** — a confidence interval for a proportion that behaves correctly near 0% and 100%, where the textbook normal interval does not. At n=340 a 65% result carries roughly \+/- 5 points.

**Confound** — a second explanation sitting underneath a result. Here: the more-recently-set extreme is usually the *nearer* one, so with-trend breaks are mechanically easier regardless of direction. In 43% of sessions the later extreme was set in the final 15 minutes before 11:00.

**Pre-registration** — writing predictions and cutoffs down before running the analysis, so the result cannot be quietly reshaped to fit.

**Data snooping** — scanning many cutoffs and reporting the best one as the finding. Reporting the full curve is the opposite of this and is good practice. The failure is only in which numbers get called conclusions.

**Prevailing direction** — which side the session is extended on at 11:00, defined as whichever extreme was set later.

---

## Finance vocabulary, where the translation is honest

| This work | Finance term |
| :---- | :---- |
| Break rate with confidence interval | Conditional probability estimation |
| First half vs second half | Variance analysis against a baseline |
| Grouping sessions by distance, comparing outcomes | Cohort analysis |
| Stressing assumptions, mapping break-even boundaries | Sensitivity analysis |
| Expectancy | Expected value modelling |

**Disclosure:** This is probability estimation on self-exported market data.  
It demonstrates Python, pandas, statistical reasoning, validation and  
technical writing. It is not financial advice and not a recommendation to  
trade. Historical frequencies are not predictions.  
