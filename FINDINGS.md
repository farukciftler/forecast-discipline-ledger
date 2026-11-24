# Findings

**Study window:** 2026-08-01 to 2026-10-31 · 92 calendar days ·
77 forecast days · 1361 forecasts written ·
706 scored forecasts in the primary pool · 146 error records ·
8 assets, 6 of them forecast.

Every number below is printed by `analysis/reproduce.py` from `data/` alone.
Where prose and script disagree, the script is right, and
`analysis/check_docs.py` fails the build when they do.

The release is a **frozen window**, not a running tally. A row is included
only if the forecast was written, its target date fell, and its outcome was
observed inside the window. The end date is the last day of the third calendar
month and was not chosen by looking at results.

---

## 0. Pools

The pre-registration forbids pooling rows from different protocol versions
and excludes one-month projections from any skill claim. The figures in §1–§4
therefore use the **primary pool** only.

| | rows |
|---|---|
| forecasts written | 1361 |
| resolved inside the window | 1111 |
| flagged substitutions, excluded | 24 |
| scored | 1087 |
| of which one-month projections | 273 |
| of which earlier protocol versions (v1–v3) | 108 |
| **primary pool** (v4, 1-day and 1-week) | **706**, on 62 forecast days |

The routine ran on 58 of the 64 days the local market was open and on 19 days
when it was closed. It did not run on 6 market days, 4 of them consecutive at
the very end of the window.

## 1. H1: all three baselines are not beaten

| baseline | rows beaten | rate | CI95 | p | days won | p |
|---|---|---|---|---|---|---|
| naive (0% change) | 385/706 | 0.545 | 0.508–0.582 | 0.009 | 35/56 | 0.041 |
| drift (mean of last 5) | 441/706 | 0.625 | 0.588–0.660 | <0.001 | 44/54 | <0.001 |
| momentum (last change) | 552/706 | 0.782 | 0.750–0.811 | <0.001 | 54/55 | <0.001 |
| **all three** | **217/706** | **0.307** | **0.274–0.342** | **1.0** | **9/58** | **1.0** |

Each baseline is beaten on its own. All three together are not, and the joint
rate sits on the wrong side of one half.

Rows written on the same day are not independent, so the right-hand columns
give each forecast day one vote: a day is won when more than half of its rows
beat the baseline. That test is the more honest of the two.

**A baseline you can beat by accident is not a baseline.** The joint criterion
was fixed in advance for that reason.

## 2. H2: intervals are too wide

| | value |
|---|---|
| coverage | **0.888** (627/706) |
| CI95 | 0.863 – 0.909 |
| target | 0.80 |
| p (two-sided exact binomial) | <0.0001 |
| excluding the managed-rate asset | 0.877 (515/587) |

Significant over-coverage. H2 says that triggers a correction. The
pre-registration was amended on 2026-08-20, before any correction, to measure
the candidate rule first (H14): a **shadow interval** from empirical quantiles
of the past 250 trading days is written beside 1-day forecasts and never
scored.

| 283 matched 1-day rows | coverage |
|---|---|
| standing interval | 0.890 |
| shadow interval | 0.859 |

The amendment predicted, before any shadow data existed, that the new rule
would lower coverage to about 0.84–0.85 and would not reach 0.80. The
direction and the failure to reach target both held; the level came out
slightly above the predicted range.

The amendment's second condition for switching, that a more volatile regime be
observed first, was not met inside the window. The standing rule was kept.

## 3. H3: one row short

The only pre-registered subgroup (confidence medium or high) holds **99** rows
against a minimum of 100. It is not tested. Descriptively, 38 of the 99 beat
all three baselines.

## 4. `p_up`: a positive score that is not skill

| | value |
|---|---|
| agent mean Brier (walk-forward rows, n = 617) | 0.2163 |
| walk-forward base-rate Brier | 0.2464 |
| **Brier skill score, walk-forward** (pre-registered) | **+0.122** |
| Brier skill score, full-sample base rate | +0.114 |

Both are positive. Neither is read as skill, and the reason is visible in the
data: the managed-rate asset rose on **84 of 84** scored rows. A pooled base
rate does not know which asset a row belongs to, so simply knowing that one
asset drifts upward by policy beats it.

Two checks remove that information. They were not pre-registered and are
**exploratory**:

| | BSS |
|---|---|
| excluding the managed-rate asset | +0.047 |
| every row against its own asset's base rate | −0.019 |

Directional accuracy over the same pool is 376/617 = 60.9%. It is a diagnostic
and not a headline, for the same reason.

## 5. Point forecasts and error spread

For each asset, the spread of 1-day forecast errors against the spread from
knowing only that asset's sample mean:

| id | n | with forecast | mean only | gain |
|---|---|---|---|---|
| A1 | 61 | 1.226 pp | 1.231 pp | +0.4% |
| A2 | 60 | 1.046 pp | 1.181 pp | +11.4% |
| A3 | 60 | 0.958 pp | 1.075 pp | +10.8% |
| A4 | 60 | 1.234 pp | 1.486 pp | +17.0% |
| A5 | 60 | 1.479 pp | 1.605 pp | +7.9% |
| A6 | 61 | 0.084 pp | 0.111 pp | +24.1% |

The spot asset (A1) gains nothing. The four funds (A2–A5) gain 8 to 17
percent. **This is not read as forecasting skill.** The funds publish their
price one day late, so a 1-day fund forecast is written after the session it
will be priced on has partly or wholly traded. The pre-registration calls this
delayed accounting (H12). A6 is the managed-rate asset. The pools were not
separated in this release, so no conclusion is drawn beyond §1.

## 6. Error log

| | value |
|---|---|
| records | 146 error records |
| detection latency | median **1 day**, mean 6.0, max 60 |
| detected by agent / human | **116 / 30** |
| repeats of a prior record | **71/146 = 48.6%** [40.7–56.7] |

Classes: measurement 35, model 26, data 21, process 20, engine 14,
verification 11, institution 10, accounting 9.

Detection mechanisms: routine flow 39, cross-check 23, reasoning 15, human 15,
custodian statement 14, pre-registered test 14, next-day observation 12,
engine warning 7, adversarial review 5, reconciliation 2.

**H7 (latency falls over time): not supported.** Spearman correlation between
record order and latency is +0.122 over 146 records; the prediction was a
negative value. One bias runs against the hypothesis: an early record cannot
have a long latency because the ledger was young.

**H8 (mechanisms differ by class): not run.** The pre-registration requires at
least five expected records per cell after grouping and does not say which
grouping. Choosing one now would be choosing it after seeing the table.

**H9 (self-correction is unbiased): below minimum n.** Favorable 11,
unfavorable 20, neutral 64. That is 31 directional corrections against a
minimum of 40. A skew toward *favorable* would be bad news; the observed
imbalance leans the other way.

**The repeat rate is the most decision-relevant number here** for anyone
building agent memory: it asks whether writing a failure down prevents its
recurrence. Close to half of the records say it did not. There is no control
arm, so the rate has nothing to be compared against.

**The daily routine is the most persistent failure.** Records K122 to K145
form a chain of six, each logging a skipped day and each a repeat of the one
before. All six were found by the agent on a later run, within two days, and
none led to a trigger being added. See CASES §6.

**The taxonomy degraded until a closed vocabulary was imposed.** Asked to
classify its own failures in free text, the agent invented a fresh category
almost every time. The published `class_k` and `mechanism_k` columns use a
controlled vocabulary added afterwards; the free-text originals are not
published. Records before K78 were mapped to the vocabulary after the data was
visible, so they are exploratory; the confirmatory pool starts at K78.

---

## What would change these conclusions

| Finding | What would overturn it |
|---|---|
| All three baselines not beaten | A joint rate significantly above 0.5 on days, not rows |
| Intervals too wide | A volatility regime in which coverage falls below 0.80 |
| `p_up` has no skill | A positive score against each asset's own base rate |
| Fund gains are accounting | Gains that survive scoring only rows written before the priced session opened |
| Repeat rate meaningful | A control arm: the same task run without an error log |
