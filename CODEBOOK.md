# Codebook

Category labels in `error_log.csv` are kept in their **original language**
rather than machine-translated. Translating a 25-value taxonomy risks
collapsing distinctions that the original coder intended, and a mis-mapped
category silently corrupts every aggregate built on it. Two-valued enums
(`detected_by`, `is_repeat`, `status`, `confidence`, `day_type`,
`horizon_kind`) *are* translated in the export, because there is nothing to
collapse.

---

## `assets.csv`

| column | meaning |
|---|---|
| `asset_id` | Pseudonym `A1`…`A7`. Mapping to real instruments is not published |
| `asset_class` | `spot` · `fund_daily` (NAV published T+1, business days only) · `fx_deposit` |
| `description` | Composition and pricing mechanics, no identifiers |

## `returns.csv`

| column | meaning |
|---|---|
| `date` | Observation date |
| `dow` | Day of week, 0 = Monday |
| `return_pct` | Percent change from the previous observed price. **Price levels are not published** |
| `gap_days` | Calendar days since the previous observation (>1 across weekends/holidays) |
| `stale_flag` | 1 if the price was carried forward rather than newly observed |

## `forecasts.csv`

| column | meaning |
|---|---|
| `as_of` | Date the forecast was sealed |
| `horizon` | `1d` · `1w` · `1m` |
| `target_date` | First day the asset is actually priced at that horizon (see METHODS §4) |
| `point_pct` | Point estimate, percent change |
| `low_pct` / `high_pct` | 80% interval bounds |
| `band_width_pct` | `high − low` |
| `band_skew` | Asymmetry: `(high + low) / 2 − point` |
| `p_up` | Probability of an up-move, 2 decimals |
| `confidence` | `low` · `medium` · `high` (agent's self-assessment) |
| `n_drivers` | Count of evidence items cited |
| `driver_max_weight` | Highest evidence weight cited: `low` · `medium` · `high` |
| `is_mechanical` | 1 if the forecast was a deterministic accrual calculation, not a judgement |
| `band_shadow_low` / `_high` | Candidate v5 interval. **Never scored** (METHODS §7) |
| `band_shadow_rule` | Identifier of the candidate rule |

## `resolutions.csv`

| column | meaning |
|---|---|
| `status` | `resolved` · `pending` · `no_data` |
| `actual_pct` | Realized percent change |
| `abs_err` / `signed_err` | `|point − actual|` and `point − actual` |
| `in_band` | 1 if the realized value fell inside the 80% interval |
| `direction_hit` | 1 if the sign matched; blank if the outcome was inside the flat dead zone |
| `brier` | `(p_up − outcome)²` |
| `paired_gain_pp` | Baseline absolute error minus agent absolute error, same row |
| `baseline_*_pct` | Each baseline's prediction (METHODS §5) |
| `beat_*` | Whether the agent's absolute error was lower |
| `beat_all_three` | **The headline statistic** |
| `horizon_kind` | `forecast` (1d, 1w) · `projection` (1m). Projections are excluded from skill claims — ~12 non-overlapping observations per year makes them unmeasurable |
| `day_type` | `data` (a scheduled numeric release lands) · `calm` · `holiday` · `weekend` |

## `error_log.csv`

| column | meaning |
|---|---|
| `record_id` | Sequential, `K1`… |
| `logged_date` / `event_date` | When recorded / when the error actually occurred |
| `latency_days` | `logged − event`. **Never revised downward** |
| `detected_by` | `agent` · `human` |
| `is_repeat` | `yes` if it recurred after a prior record covering the same failure |
| `prior_record` | The earlier `record_id`, when `is_repeat = yes` |
| `class_k` | Closed error taxonomy, eight values (below) |
| `mechanism_k` | What caught it, ten values (below) |
| `score_effect` | `favorable` · `unfavorable` · `neutral`, or blank when unknown. Whether the correction moved a reported number in the agent's own favour. A skew toward `favorable` would be bad news, and testing for it is the point of the field |

### `class_k` — top-level error taxonomy

A closed vocabulary of eight values. Counts over the current sample are in
[FINDINGS.md](FINDINGS.md).

| label | meaning |
|---|---|
| `measurement` | a scored observation was computed wrongly, or should not have counted |
| `model` | a wrong assumption about how an asset behaves |
| `data` | a source failed, returned a stale value, or was read without its date |
| `engine` | the deterministic ledger code behaved wrongly |
| `verification` | a checking step failed or was skipped |
| `process` | a required step of the daily routine was skipped |
| `institution` | a wrong assumption about how a product settles or pays |
| `accounting` | double counting or mis-attribution between holdings |

An earlier free-text `class` field is **not published**. It reached 25 values
over the first 52 records and its `subclass` companion reached 50, which is to
say the agent invented a fresh category almost every time it was asked to
classify itself. That field is the evidence for the design lesson in
FINDINGS.md rather than a usable variable, and translating it would have
dressed unusable data in a second language.

### `mechanism_k` — what caught the error

A closed vocabulary of ten values.

| label | meaning |
|---|---|
| `routine_flow` | the ordinary daily sequence surfaced it, without anyone looking for it |
| `cross_check` | two sources of the same quantity disagreed |
| `reasoning` | the agent noticed it while thinking about something else |
| `human` | the operator noticed it |
| `custodian_statement` | an external account statement contradicted the ledger |
| `reconciliation` | a total was matched against an independent total |
| `next_day_observation` | the following day's data made it visible |
| `preregistered_test` | a test written in advance failed |
| `engine_warning` | the deterministic code refused or warned |
| `adversarial_review` | a scheduled review pass looking specifically for it |

Two of these deserve comment. `routine_flow` is the largest single category,
which says that most errors are caught by the process running at all rather
than by anyone checking. `preregistered_test` is among the smallest, and its
denominator is short: tests can only catch what someone thought to write a
test for.

### Caveat: the closed vocabulary was imposed late

The published `class_k` and `mechanism_k` columns are closed vocabularies, but
they were not there from the start. The original free-text fields reached 25
values across the first 52 records, and their `subclass` companion reached 50
across the same 52. An agent asked to classify its own failures invents a new
category almost every time unless it is constrained to a fixed list.

This matters for how the columns should be read. Records logged before the
vocabulary existed were mapped onto it **after** the data was visible, so those
rows are exploratory. Only records from the freeze point onward count as
confirmatory, and the two pools are reported separately rather than pooled.

## `market_state.csv`

Long format: `date, variable, value`. Public market variables only — yields,
index levels, implied volatilities, credit spreads, policy rates, FX and
commodity quotes. Every value is sourced from a dated public series
(central-bank statistical releases, exchange data, benchmark fixings).
Free-text annotations attached to these variables in the source ledger are
not exported.

## `exposure.csv`

Look-through exposure of the whole portfolio by underlying asset class, **as
percentages only**. `holdings_age_days` is the age of the fund-composition
data used; composition is refreshed roughly monthly, so a large value means
the breakdown is stale.
