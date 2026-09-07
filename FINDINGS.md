# Findings to date

**Sample:** 20 calendar days · 148 scored forecasts · 52 error records ·
6 assets · one volatility regime.

Every number below is printed by `analysis/reproduce.py` from `data/` alone.
Where prose and script disagree, the script is right.

**Read this first:** at ~3 effectively independent observations per day,
20 days is ~60 independent observations. Nothing here is settled. These are
reported because *reporting negative results early* is the point of the
design, not because they are conclusive.

---

## 1. The point forecast does not reduce error spread

The sharpest result, and the one that constrains everything else.

For each asset, compare the spread of forecast errors against the spread you
would get from knowing only that asset's sample mean:

| id | n | with forecast | mean only | gain |
|---|---|---|---|---|
| A1 | 19 | 1.178 pp | 1.149 pp | **−2.5%** |
| A2 | 14 | 1.696 pp | 1.627 pp | **−4.3%** |
| A3 | 14 | 2.607 pp | 2.583 pp | −0.9% |
| A4 | 14 | 1.079 pp | 1.281 pp | **+15.8%** |
| A5 | 11 | 0.959 pp | 0.965 pp | +0.6% |
| A6 | 16 | 0.082 pp | 0.079 pp | −3.8% |

Five of six show no gain; three are negative, i.e. the forecast made the
spread *worse* than a constant would have.

**Consequence for intervals:** the floor on interval width is the asset's own
volatility, not the agent's ignorance. More data cannot narrow it. This is
the quantitative form of the project's first stated principle — *one-day
price forecasting is effectively random* — and it was written into the
protocol before it was measured.

A4's +15.8% is the one exception and is almost certainly noise at n=14. It is
under an explicit test (CASES §3) whose reading rule was fixed in advance.

## 2. "Beat the baseline" depends entirely on which baseline

| baseline | beaten | rate | CI95 | p (one-sided) |
|---|---|---|---|---|
| naive (0% change) | 104/148 | 0.703 | 0.625–0.770 | <0.001 |
| drift (mean of last 5) | 86/128 | 0.672 | 0.587–0.747 | 0.0001 |
| momentum (last change) | 93/128 | 0.727 | 0.644–0.796 | <0.001 |
| **all three** | **50/128** | **0.391** | **0.310–0.477** | **0.995** |

Each baseline is beaten individually. **All three together are not** — the
result is on the wrong side of chance.

Why the individual wins are not evidence: for part of this window, **100% of
realized 1-week changes were positive**. Against a 0%-change baseline, *any*
small positive point estimate wins mechanically. An earlier version of this
project reported "baseline beaten, p<0.001" as a headline. That headline was
largely a reflection of the regime, and replacing it with the all-three
statistic is the single largest correction the project has made.

This generalizes well beyond finance: **a baseline you can beat by accident
is not a baseline.**

## 3. Interval coverage: too wide, and mostly because of the regime

| | value |
|---|---|
| coverage | **0.872** (129/148) |
| CI95 | 0.808 – 0.916 |
| target | 0.80 |
| p (two-sided exact binomial) | **0.030** |

Significant over-coverage. Per pre-registration H2, that triggers a
correction. The correction was **not** applied; a shadow measurement was
started instead (METHODS §7, PREREGISTRATION H14).

The reason is in the regime data. Comparing each asset's sample volatility to
its 250-trading-day volatility:

| id | sample | 250-day | ratio |
|---|---|---|---|
| A1 | 1.142 | 1.850 | **0.62×** |
| A4 | 1.281 | 2.130 | **0.60×** |
| A5 | 0.965 | 1.314 | 0.73× |
| A6 | 0.085 | 0.092 | 0.92× |
| A2 | 1.627 | 1.504 | 1.08× |
| A3 | 2.554 | 1.187 | **2.15×** |

Four of six assets traded at 60–73% of their long-run volatility. Intervals
sized for the long run *should* over-cover in such a window. Recalibrating to
it would leave them too narrow when volatility normalizes.

(The 250-day column needs price levels and is therefore computed in the
private source, not reproducible from `data/`. The sample column is
reproducible; `reproduce.py` prints slightly different values because it
treats multi-day gaps differently.)

A second contributor is distributional shape: **all six assets have
`std / sigma_MAD` between 1.15 and 1.54**, i.e. fat tails. A Gaussian
`1.2816 × std` interval over-covers a fat-tailed distribution by
construction.

## 4. `p_up` loses to the running base rate

| | value |
|---|---|
| agent mean Brier | 0.208 |
| running-climatology Brier | 0.194 |
| **Brier skill score** | **−0.08** |

Negative skill: simply tracking the base rate of up-days would have scored
better than the agent's stated probabilities. (A shorter 30-day window gives
a more negative figure; the full-sample number is quoted because it is what
`reproduce.py` computes.)

Directional accuracy over the same rows is **102/137 = 74.5%**
[66.6–81.0]. This looks impressive and **is not reported as a headline**,
because it is measuring the regime: in a window where most days were up,
predicting "up" scores well while carrying no information. The BSS is the
statistic that removes exactly that flattery — and it is negative.

Detecting a genuine 52% edge would need ~3,900 independent observations
(≈6 years at this rate).

## 5. Error log

| | value |
|---|---|
| records | 52 in 20 days (≈2.6/day) |
| detection latency | median **1 day**, mean 2.6, max 15 |
| detected by agent / human | **42 / 10** |
| repeats of a prior record | **15/52 = 28.8%** [18.3–42.3] |

Most common classes: measurement contamination (7), engine bugs (6), model
errors (4), institutional mechanics (4).

Three observations:

**The error log accumulates ~2.6× faster than useful forecast observations**,
and it measures a question that is answerable on a much shorter timescale.
Pre-registered hypotheses H7–H9 need ~120 records — roughly two more months,
not the ~6 years the forecasting question needs.

**The 28.8% repeat rate is the most decision-relevant number in the dataset**
for anyone building agent memory: it asks whether writing a failure down
prevents its recurrence. It currently has nothing to be compared against —
there is no control arm (README, *Limitations*).

**The taxonomy degrades as it grows.** `class` has 25 values over 52 records;
`subclass` has 50 values over 52 records. Asked to classify its own failures,
the agent invents a fresh category almost every time. Only `class`,
`detected_by`, `latency_days` and `is_repeat` are usable for aggregation.
This is a design lesson, not a data-cleaning nuisance: **agent-generated
taxonomies need a closed vocabulary imposed up front**, or they become free
text wearing a column header.

---

## What would change these conclusions

| Finding | What would overturn it |
|---|---|
| Point forecasts add nothing | A sustained positive gain across ≥4 assets over ≥100 observations |
| All-three-baselines not beaten | Rate significantly above 0.5 at n ≥ 300 |
| Intervals too wide | A volatility regime in which coverage falls below 0.80 |
| `p_up` has negative skill | BSS turning positive in a two-sided regime |
| Repeat rate meaningful | A control arm — the same task run without an error log |

## Standing prediction

Recorded before the data exists (PREREGISTRATION H14-c): switching to the v5
interval rule will move coverage from 87% to roughly **84–85%** and will
**not** reach 80%, because the dominant cause is regime rather than rule.

If that prediction is wrong, this line stays here.
