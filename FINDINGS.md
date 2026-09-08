# Findings to date

**Sample:** 39 calendar days · 405 scored forecasts · 102 error records ·
7 assets · one volatility regime.

Every number below is printed by `analysis/reproduce.py` from `data/` alone.
Where prose and script disagree, the script is right.

**Read this first:** at ~3 effectively independent observations per day,
39 days is ~120 independent observations. Nothing here is settled. These are
reported because *reporting negative results early* is the point of the
design, not because they are conclusive.

---

## 1. The point forecast does not reduce error spread

The sharpest result, and the one that constrains everything else.

For each asset, compare the spread of forecast errors against the spread you
would get from knowing only that asset's sample mean:

| id | n | with forecast | mean only | gain |
|---|---|---|---|---|
| A1 | 38 | 1.337 pp | 1.335 pp | −0.2% |
| A2 | 33 | 1.385 pp | 1.356 pp | **−2.1%** |
| A3 | 33 | 1.855 pp | 1.862 pp | +0.4% |
| A4 | 33 | 1.277 pp | 1.493 pp | **+14.4%** |
| A5 | 30 | 1.002 pp | 1.012 pp | +1.0% |
| A6 | 35 | 0.088 pp | 0.079 pp | **−11.5%** |

Three of six are negative; of the three positive, two are under half a
percent, which at this sample size is indistinguishable from zero. Only A4
stands out.

**Consequence for intervals:** the floor on interval width is the asset's own
volatility, not the agent's ignorance. More data cannot narrow it. This is
the quantitative form of the project's first stated principle — *one-day
price forecasting is effectively random* — and it was written into the
protocol before it was measured.

A4's +14.4% is the one exception. It has now survived from n=14 to n=33 at
much the same size, which is longer than noise usually lasts but still short
of the pre-registered reading threshold (CASES §3). A4 is the asset whose
main driver trades continuously while its own price is struck once a day, so
part of the day's move is arithmetic rather than forecast. That is the
leading explanation and it is not yet tested.

## 2. "Beat the baseline" depends entirely on which baseline

| baseline | beaten | rate | CI95 | p (one-sided) |
|---|---|---|---|---|
| naive (0% change) | 255/405 | 0.630 | 0.582–0.675 | <0.001 |
| drift (mean of last 5) | 242/374 | 0.647 | 0.597–0.694 | <0.001 |
| momentum (last change) | 283/374 | 0.757 | 0.711–0.797 | <0.001 |
| **all three** | **125/374** | **0.334** | **0.288–0.384** | **1.0** |

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
| coverage | **0.877** (355/405) |
| CI95 | 0.841 – 0.905 |
| target | 0.80 |
| p (two-sided exact binomial) | **0.0001** |

Significant over-coverage. Per pre-registration H2, that triggers a
correction. The correction was **not** applied; a shadow measurement was
started instead (METHODS §7, PREREGISTRATION H14).

The reason is in the regime data. Comparing each asset's sample volatility to
its 250-trading-day volatility:

| id | sample | 250-day | ratio |
|---|---|---|---|
| A1 | 1.223 | 1.870 | **0.65×** |
| A4 | 1.683 | 2.162 | 0.78× |
| A3 | 1.023 | 1.196 | 0.86× |
| A2 | 1.354 | 1.508 | 0.90× |
| A6 | 0.088 | 0.097 | 0.91× |
| A5 | 1.209 | 1.291 | 0.94× |

**Every asset traded below its long-run volatility**, from 0.65× to 0.94×.
Intervals sized for the long run *should* over-cover in such a window.
Recalibrating to it would leave them too narrow when volatility normalizes.

This table has also moved a lot since the first release, when two assets sat
above 1.0× and the spread ran from 0.60× to 2.15×. The convergence is what a
short sample looks like when it stops being short, and it is a reason to
treat any single reading of this table as provisional.

(The 250-day column needs price levels and is therefore computed in the
private source, not reproducible from `data/`. The sample column is
reproducible; `reproduce.py` prints slightly different values because it
treats multi-day gaps differently.)

A second contributor is distributional shape: **all six assets have
`std / sigma_MAD` between 1.12 and 1.66**, i.e. fat tails. A Gaussian
`1.2816 × std` interval over-covers a fat-tailed distribution by
construction.

## 4. `p_up` is indistinguishable from the base rate

| | value |
|---|---|
| agent mean Brier | 0.2131 |
| walk-forward climatology Brier | 0.2176 |
| **Brier skill score** | **+0.020** |

The sign flipped since the first release, when BSS was −0.08. It is now
positive and small enough that it is not a skill claim: a skill score of
0.020 means the agent's stated probabilities and a running tally of how often
prices went up score about the same.

**Two baselines, two answers.** `reproduce.py` uses a *walk-forward* base rate
built only from rows already resolved. The manuscript uses the *full-sample*
base rate, which is a look-ahead and therefore a harder baseline, and gives
BSS = −0.000. Both round to nothing, but they are not interchangeable and the
difference is stated rather than resolved by picking the friendlier one.

Directional accuracy over the same rows is **258/380 = 67.9%**
[63.0–72.4]. This looks impressive and **is not reported as a headline**,
because it is measuring the regime: in a window where most days were up,
predicting "up" scores well while carrying no information. The BSS is the
statistic that removes exactly that flattery, and it removes essentially all
of it.

Detecting a genuine 52% edge would need ~3,900 independent observations
(≈6 years at this rate).

## 5. Error log

| | value |
|---|---|
| records | 102 in 39 days (≈2.6/day) |
| detection latency | median **1 day**, mean 5.8, max 37 |
| detected by agent / human | **80 / 22** |
| repeats of a prior record | **41/102 = 40.2%** [31.2–49.9] |

Classes: measurement 30, model 14, data 14, engine 11, verification 11,
process 10, institution 8, accounting 4.

Detection mechanisms: routine flow 30, cross-check 18, reasoning 14, human 12,
custodian statement 8, next-day observation 6, pre-registered test 5, engine
warning 4, adversarial review 3, reconciliation 2.

The mean latency (5.8 days) is nearly six times the median (1 day). Most errors are
caught the next morning; a long tail is not caught for weeks, and that tail is
where the interesting records are.

**H9 has its first reading.** Of the corrections with a recorded direction:
favorable 9, unfavorable 11, neutral 31 (n=51). A significant skew toward
*favorable* would be bad news, since it would mean corrections get chosen
after seeing which way they cut. No skew is detected, which is the outcome the
test was designed to be able to refuse.

Four observations:

**The error log accumulates ~2.6× faster than useful forecast observations**,
and it measures a question that is answerable on a much shorter timescale.
Pre-registered hypotheses H7–H9 need ~120 records — roughly two more months,
not the ~6 years the forecasting question needs.

**The 40.2% repeat rate is the most decision-relevant number in the dataset**
for anyone building agent memory: it asks whether writing a failure down
prevents its recurrence. It currently has nothing to be compared against —
there is no control arm (README, *Limitations*).

**The repeat rate rose from 28.8% to 40.2% as the log grew.** Writing a
failure down is doing less to prevent its recurrence than the first release
suggested. There is still nothing to compare it against.

**The taxonomy degraded until a closed vocabulary was imposed.** In the source
ledger the free-text `class` field reached 25 values over 52 records and
`subclass` reached 50 over 52: asked to classify its own failures, the agent
invented a fresh category almost every time. A controlled vocabulary was added
afterwards, and the published `class_k` and `mechanism_k` columns use it. The
free-text originals are **not published**, because they are not analysable and
translating them would only launder that. This is a design lesson rather than
a data-cleaning nuisance: **agent-generated taxonomies need a closed
vocabulary imposed up front**, or they become free text wearing a column
header. Note also that the rows classified before the vocabulary existed were
mapped to it *after* the data was visible, so they are exploratory; only
records from the freeze point onward count as confirmatory.

---

## What would change these conclusions

| Finding | What would overturn it |
|---|---|
| Point forecasts add nothing | A sustained positive gain across ≥4 assets over ≥100 observations |
| All-three-baselines not beaten | Rate significantly above 0.5 at n ≥ 300 (n is now 374 and the rate is 0.334) |
| Intervals too wide | A volatility regime in which coverage falls below 0.80 |
| `p_up` has no skill | BSS staying clear of zero, in either direction, in a two-sided regime |
| Repeat rate meaningful | A control arm — the same task run without an error log |

## Standing prediction

Recorded before the data exists (PREREGISTRATION H14-c): switching to the v5
interval rule will move coverage from 87% to roughly **84–85%** and will
**not** reach 80%, because the dominant cause is regime rather than rule.

If that prediction is wrong, this line stays here.
