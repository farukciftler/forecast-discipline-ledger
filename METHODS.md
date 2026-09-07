# Methods

## 1. Design

Every trading day, a single LLM agent executes a fixed sequence:

1. **Sync** — pull the ledger; refuse to score anything from a stale copy
2. **Collect prices** — from machine-readable, *dated* sources only
3. **Score** — resolve every forecast whose target date has arrived
4. **Scan the news** — write a dated evidence file (mandatory, see §6)
5. **Forecast** — point + 80% interval + `p_up` + rationale + invalidator
6. **Derive** — regenerate exports and charts
7. **Commit** — append-only, timestamped

Order matters and is enforced by a driver script. Scoring (step 3) never runs
before sync (step 1), because scoring seals results permanently.

## 2. Separation of concerns

The design's central constraint is that **no single component both fetches
data and interprets it**:

| Component | Does | Never does |
|---|---|---|
| Data fetcher | Pulls dated series from public APIs, cross-checks | Interprets, writes files, fills gaps |
| LLM agent | Searches news, forms judgements, writes prose | **Arithmetic**, schema invention, **reading numbers out of search snippets** |
| Ledger engine | Stores, matches, scores | Touches the network, produces forecasts |

The third row of prohibitions was added after five separate incidents in which
the agent read a number out of a search-engine summary and got it wrong by
40bp, 675 index points, ~$95/oz, and — twice — four days of staleness. News
prose carries a number **without its date**; a time series API cannot.

The arithmetic prohibition is the same idea in the other direction: the
calculator must never hallucinate, so the calculator is not a language model.

## 3. Assets

Six forecastable assets (`data/assets.csv`). Two additional accrual accounts
in the source ledger are excluded here — they are not forecast, and they are
balances.

| id | class | pricing mechanics |
|---|---|---|
| A1 | spot | near-continuous, morning quote |
| A2–A5 | fund_daily | **NAV published T+1, business days only** |
| A6 | fx_deposit | managed-crawl exchange rate |

The T+1 lag for funds is load-bearing: a NAV dated *T* prices the market
session of *T−1*. This is measured, not assumed (§7).

## 4. Forecast format

Each forecast carries:

- `point_pct` — point estimate, percent change from the last observed price
- `low_pct` / `high_pct` — **80% interval**, mandatory; a point estimate is
  never recorded alone
- `p_up` — probability of an up-move, recorded to two decimals (rounding to
  0.05 costs measurable accuracy)
- `confidence` ∈ {low, medium, high}
- a written rationale and an **invalidator** (what would falsify it)
- `day_type` ∈ {data, calm, holiday, weekend}
- `protocol_version`

Free text is not exported (see README privacy section), but its *presence* is
part of the protocol: an unwritten rationale cannot be audited later.

### Target-date rule

**The target date is the first day the asset is actually priced.** A 1-day
forecast made on Friday targets Monday, not Saturday; a target landing on a
market holiday rolls to the next session.

This is not cosmetic. A closed day's snapshot carries the *previous* day's
price, so such a forecast resolves at a guaranteed 0% change: the interval
always holds, the direction is always "flat", and mean absolute error shrinks
artificially. That is not a missing observation, it is a **contaminated** one,
and it is not randomly distributed — it strikes only Fridays and pre-holiday
forecasts. Rows with closed-day targets are excluded from the scoring pool
and counted separately.

## 5. Baselines

A forecast is compared against three baselines, all using only information
available at forecast time:

| Baseline | Definition |
|---|---|
| `naive` | 0% change |
| `drift` | mean of the last 5 observed changes × horizon steps |
| `momentum` | last observed change × horizon steps |

**Beating the naive baseline alone is not reported as a headline.** In a
one-directional market it is mechanically easy: at one point 100% of realized
1-week changes were positive, so any small positive point estimate wins. The
reported statistic is the share of rows beating **all three**.

Every MAE comparison runs on **matched (day, asset, horizon) triples**. An
earlier unmatched pooled comparison produced a spurious "drift beats the
agent" headline that vanished under matching.

## 6. Evidence collection

**Hard rule: if a price snapshot was taken for a day, an evidence file is
written for that day.** No exceptions, including days when the operator asked
for something narrow.

The reason is measurement integrity, not completeness. Evidence files cannot
be back-filled and their absence is invisible: a gap in a price series shows
up on a chart, a gap in an evidence series shows up nowhere. Worse, the
missing days are not random — they are *rushed* days, which makes the gap
systematic and contaminates any later "which kind of news moved the price"
analysis with selection bias.

A scan may be small; it may not be zero. "Checked, nothing relevant" is a
data point and is recorded as such.

For scheduled numeric releases, **consensus and actual are stored in separate
fields**, never narrated in prose, so that surprise can be derived
mechanically. A consensus recorded *before* the release is legitimate and
expected — it is the anchor. An actual without a consensus is rejected by the
engine: if surprise cannot be measured, neither can whether the event was
already priced.

## 7. Interval construction

Two rules have been used.

**v4 (in force).** Width derived from option-implied volatility for the
matching underlying, scaled to the horizon in **trading days**:

```
sigma_daily = (IV_annual / 100) / sqrt(252)
sigma_h     = sigma_daily * sqrt(trading_days)      # 1d=1, 1w=5, 1m=21
band_80     = ± 1.2816 * sigma_h * VRP              # VRP = 0.85
```

`VRP` corrects for implied volatility systematically exceeding realized.
Calendar-day scaling was used earlier and made intervals ~17–20% too wide.

**v5 (shadow, not in force).** Empirical p10/p90 of the asset's own 250
trading-day return distribution, de-meaned and centred on the point estimate.

Motivation: all six assets have `std / sigma_MAD` between **1.15 and 1.54**,
i.e. fat tails. A Gaussian `1.2816 × std` band over-covers such a
distribution — which is one direct cause of the observed 87% coverage.

### Shadow bands

Changing the band rule bumps `protocol_version`, which **splits the scoring
pool**: learning whether the new rule is better would take ~150 fresh
observations, i.e. the answer arrives two months *after* committing to it.

Instead, the candidate band is written alongside each forecast as
`band_shadow_low` / `band_shadow_high` and is **never scored**. A separate
script measures its coverage. The switch decision is therefore made on a
number observed *before* the switch, with no pool contamination.

## 8. Scoring

Automatic, on the first day the target price exists:

- `in_band`, `direction_hit` (with a dead zone for flat outcomes), `brier`
- `abs_err`, `signed_err`, `paired_gain_pp` vs. each baseline
- `status = pending` if no price yet (weekend, holiday, T+1 lag) — retried
  for up to 6 days. Pending is not an error.

Primary statistic is a **paired sign test** against baselines, not directional
accuracy. Directional accuracy is a diagnostic: binarizing discards the
information in `p_up` (0.54 and 0.80 score identically) and needs 3–6× more
observations for the same power.

For `p_up`, the reference is the **climatological Brier score** (running base
rate), not 0.25. A fixed 0.25 reference is flattered by any directional
regime.

## 9. Error log

Every operational error gets a row (`data/error_log.csv`) with:

`record_id, logged_date, event_date, class, subclass, detection_mechanism,
detected_by, latency_days, impact, fix_type, is_repeat, prior_record`

- `latency_days = logged_date − event_date`. **Never revised downward.**
- `detected_by` ∈ {agent, human}. Errors the human caught do not count toward
  the agent's self-detection performance.
- The file is **append-only**. Reclassification adds a column, never edits a
  row.

The prose narrative for each record lives in the private repository and is
not exported; the structured fields are what the pre-registered hypotheses
(H7–H9) actually consume.

## 10. Anomaly threshold

A deviation is not logged as an anomaly until its **percentile within that
asset's own historical deviation distribution** has been computed. Outside
the top 10% → no record; it is noise.

This rule was itself added after an error. A "sharp divergence" was recorded
and then used as a forecasting rationale for two days. When finally measured,
it sat at the 87th of 246 observations — an event seen roughly every third
day. The decisive evidence: the *previous* day had produced a larger
deviation and had not been flagged. What triggered the flag was not the
signal's size but its **direction**.
