# Pre-registration

**Purpose.** This document fixes the analysis plan *before* the data exists.
Any result not specified here is labelled **exploratory** and does not count
as evidence.

This is the only mechanism that prevents the obvious failure mode: looking at
the outcomes and then deciding which subgroup to report. It matters more than
usual here, because the analyst and the forecaster are **the same agent**.
An agent that both makes predictions and chooses how to score them can
improve its own record without improving anything real.

Amendments are dated and additive. Nothing is deleted.

---

## Reporting order

Results are reported H1 → H2 → H3, then exploratory. Reordering to lead with
whatever came out best is not permitted.

## Pooling rules

1. **Rows with different `protocol_version` are never pooled.** A rule change
   restarts the count; the old version is reported separately.
2. Rows with `status != resolved` enter no test.
3. Rows whose target date fell on a closed market day are excluded and
   counted separately (METHODS §4).
4. Superseded forecasts are not scored; only the standing record is.
5. **Different horizons of the same asset on the same day are not
   independent.** Correlation blocks: {A1, A4} · {A2, A3} · {A5} · {A6}
   → roughly **3 effectively independent observations per day**, not 6–18.

---

## H1 — Primary hypothesis

> Agent forecasts carry information beyond the baselines.

- **Test:** paired sign test on matched (day, asset, horizon) triples,
  agent absolute error vs. baseline absolute error.
- **Primary statistic:** share of rows beating **all three** baselines.
  Beating the naive baseline alone is *not* a headline (METHODS §5).
- **Minimum n:** 100 resolved rows.
- **Threshold:** one-sided p < 0.05.
- **Why a sign test rather than directional accuracy:** binarizing discards
  what `p_up` encodes (0.54 and 0.80 score identically) and requires 3–6×
  more observations for equivalent power.

## H2 — Interval width

> The 80% intervals cover 80%.

- **Test:** two-sided exact binomial, `H0: coverage = 0.80`.
- **Minimum n:** 100.
- **Threshold:** p < 0.05 ⇒ the interval rule is wrong and **is corrected**.
- **Note:** this is the fastest-converging metric and the most likely concrete
  output of the project. A correction **increments `protocol_version`.**

## H3 — Confidence split (the only pre-registered subgroup)

> If any edge exists, it is in the `confidence ∈ {medium, high}` subset.

- **Rationale:** most `low`-confidence forecasts are explicit records of
  *"I have no directional signal"*. They dilute any edge.
- **Test:** H1, restricted to that subset.
- **Minimum n:** 100.
- **Warning:** this is the **only** pre-registered subgroup. Any other
  subgroup analysis is exploratory.

## H4 — Surprise matters, events do not

> Price responds to the *surprise* (actual − consensus), not to the event.

- **Requires:** consensus and actual stored in separate fields, consensus
  recorded before release.
- **Minimum n:** 30 scheduled numeric releases (≈1 year).

## H5 / H6 — One-month horizons

One-month outputs are labelled **projections**, not forecasts, and are
excluded from skill claims. A 1-month horizon yields ~12 non-overlapping
observations per year; detecting a 55% edge would take ~21 years. Producing
them is useful; scoring them as if they were measurable is not.

---

## H7–H9 — Second hypothesis family: error detection and self-correction

Consumes `error_log.csv`. Pooling for this family is independent of
`protocol_version`.

### H7 — Detection latency falls over time

- **Test:** Spearman rank correlation between `record_id` order and
  `latency_days`.
- **Minimum n:** 120 records.
- **Caveat that cannot be removed:** the log contains only *detected* errors.
  Latency is measurable; the error **rate** is not. Under-ascertainment
  biases every rate-like quantity, and no amount of additional data fixes it
  without an independent audit.

### H8 — Mechanisms beat chance

> Some detection mechanisms find error classes that others systematically miss.

- **Test:** χ² on the mechanism × class contingency table.
- **Minimum n:** 120, and ≥5 expected per cell after grouping (CODEBOOK).

### H9 — Self-correction is directionally unbiased

> Corrections do not systematically favour the agent's own scorecard.

- **Test:** sign test on the effect of each correction on the headline
  metrics — does it improve or worsen the agent's record?
- **Minimum n:** 40 corrections with a measurable metric effect.
- **A significant result is BAD NEWS.** If corrections systematically flatter
  the agent, the correction decision is being made after seeing the outcome.
- **Standing safeguard:** whenever a correction turns out to favour the agent,
  its justification must have been **written before the outcome was known**,
  and that ordering must be visible in the commit history.

---

## H10–H13 — Signal and baseline hypotheses (added 2026-08-13)

Added after a literature review. The review's honest summary: **no signal
predicting 1-day direction was found.** That did not refute the project's
first principle, it confirmed it. Whatever value the review had was on the
**interval** side, not the direction side.

- **H10 — implied-volatility intervals beat a fixed table.** Under
  measurement; currently in tension with H2's finding that intervals are too
  wide.
- **H11 — horizons scale in trading days, not calendar days.** Adopted;
  calendar scaling made intervals ~17–20% too wide.
- **H12 — daily fund forecasts are delayed accounting, not forecasting.**
  A T+1 NAV mostly re-prices an already-observed session. If true, fund rows
  should be scored in a separate pool from the spot asset.
- **H13-c — the primary `p_up` statistic is the Brier skill score against
  running climatology**, not against a fixed 0.25. A fixed reference is
  flattered by any directional regime.

**Explicitly excluded, with documented failure:** technical analysis ·
analyst targets · trend following · pre-FOMC drift · post-earnings drift ·
gold/silver ratio · sentiment surveys · earnings-revision momentum.

**Down-weighted:** real interest rates as a driver of precious metals — the
correlation fell from ~84% to ~3% after 2022 as the marginal buyer changed.

---

## H14 — Interval rule v5, measured by shadow band (added 2026-08-20)

H2's threshold has been met (coverage 87.7%, p = 0.0001), so a correction is
due. But the correction itself creates a measurement problem: incrementing
`protocol_version` splits the pool, so the new rule's coverage could only be
learned ~2 months *after* committing to it.

**Shadow bands resolve this** (METHODS §7). The switch decision will be made
on a number observed before the switch.

### H14-a — Empirical-quantile intervals calibrate better than Gaussian scaling

- **Rationale (measured over 250 trading days):** all six assets have
  `std / sigma_MAD` between 1.15 and 1.54 — fat tails. A `1.2816 × std` band
  over-covers such a distribution.
- **v5 rule (fixed now):** `band = point + [p10 − mean, p90 − mean]` over 250
  trading days, refreshed monthly. **1-day horizon only for now.**
- **Test:** two-sided exact binomial on shadow coverage; plus a matched
  comparison against the standing interval on identical (day, asset) pairs.
- **Minimum n:** 100 matched 1-day shadow observations.
- **Decision rule:** switch only if the shadow coverage's distance from 0.80
  is **smaller** than the standing rule's.

### H14-b — Switching requires n **and** a second regime

Both conditions, not either:

1. n ≥ 100 matched 1-day shadow observations
2. **A second volatility regime has been observed** — concretely: at least one
   daily decline of ≤ −3% in A1, **or** at least 5 trading days with gold
   implied volatility above 30.

The second condition is a measurement, not a preference. The sample window is
regimewise unrepresentative and inconsistent across assets: four of six assets
traded at **60–73% of their 250-day volatility**, while one traded at 215%.
Part of the "intervals are too wide" finding is therefore **calm regime, not
rule error**. Narrowing to this window would leave the intervals *too narrow*
when volatility normalizes — and that error points toward breaches, which is
worse than the current one.

### H14-c — Pre-registered prediction of the effect size

Recorded now, before the data:

| | standing | shadow (v5) | ratio |
|---|---|---|---|
| mean across six assets | — | — | **≈ 0.92×** |

**Predicted outcome: switching to v5 moves coverage from 87% to roughly
84–85%, and does *not* reach 80%.** In other words the shadow measurement is
expected to show that *the rule change does not fix the problem*, and the real
cause is regime.

An earlier estimate of "20–25% narrowing", derived from the 14-observation
forecast log, was **too optimistic**; a standard-deviation estimate at n=14
carries roughly ±19% relative error. The 250-day measurement supersedes it.
This paragraph exists so that the earlier, wrong estimate stays on the record.

### H14-d — A6 as a separate pool — **EXPLORATORY, not evidence**

A6 is reported separately from the main interval pool.

**This decision was made after looking at the data** (16/16 inside the
interval, with a realized standard deviation an order of magnitude below the
interval width). Under the pooling rules above, that makes it **post-hoc pool
selection and not evidence** for existing rows. The headline coverage
statistic continues to be reported **including** A6.

The separation is confirmatory only for rows created **after 2026-08-20**.

Rationale: under a managed-crawl exchange-rate regime, an interval that is
never breached is **a warning, not a success** — the interval is carrying no
information. Scoring such an asset in the same pool as equity and commodity
forecasts inflates the record with easy wins.
