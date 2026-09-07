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
| `asset_id` | Pseudonym `A1`…`A6`. Mapping to real instruments is not published |
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

### `class` — top-level error taxonomy

| label | translation |
|---|---|
| `olcum_kirliligi` | measurement contamination — a scored observation that should not count |
| `olcum_hatasi` | measurement error — computed the wrong quantity |
| `olcum_eksigi` | measurement gap — a quantity that should have been recorded was not |
| `motor_hatasi` | engine bug — the deterministic ledger code behaved wrongly |
| `model_hatasi` | model error — a wrong assumption about how an asset behaves |
| `model_belirsizligi` | model uncertainty — competing models, not yet resolved |
| `kurumsal_mekanik` | institutional mechanics — wrong assumption about how a product settles/pays |
| `surec_hatasi` | process error — a required step was skipped |
| `muhasebe` | accounting — double counting or mis-attribution |
| `tarihsiz_sayi` | undated number — a value used without knowing which day it belonged to |
| `veri_hatasi` / `veri_kaynagi` / `veri_kalitesi` | data error / source failure / quality |
| `n1_iddiasi` | n=1 claim — a conclusion drawn from a single observation |
| `kalibrasyon` | calibration — scoring or interval rule wrong |
| `protokol` / `tahmin_politikasi` | protocol or forecasting-policy error |
| `gerekce_hatasi` / `cikarim_hatasi` | faulty rationale / faulty inference |
| `kaynak_celiskisi` | source conflict resolved incorrectly |
| `kanit_agirligi` | evidence weighting error |
| `dogrulama` | verification step failed or was skipped |
| `kok_neden` | root-cause misattribution |
| `oturmamis_veri` | unsettled data — a value read before it was final |
| `tahmin_hatasi` | forecast construction error |

### `detection_mechanism`

Grouped, since the raw vocabulary is long-tailed (see caveat below):

| group | raw labels |
|---|---|
| **Agent reasoning** | `akil_yurutme`, `ikinci_okuma`, `surucu_kontrolu`, `kok_neden` |
| **Cross-check** | `capraz_kontrol`, `kaynak_capraz_kontrol`, `ucgenleme`, `cift_kaynak_nav`, `kumulatif_uyum` |
| **External ground truth** | `custodian_statement`, `custodian_total`, `fund_composition_source`, `fund_source_dated_api`, `makine_okunur_kaynak` |
| **Routine process** | `rutin_akis`, `rutin_denetim`, `cozumleme`, `acik_is_listesi`, `sistemi_calistirmak`, `altyapi_kurulumu` |
| **Engine warning** | `motor_uyarisi` |
| **Human** | `kullanici_bildirimi`, `kullanici_sorusu` |
| **Literature / research** | `literatur_taramasi`, `derin_arastirma`, `web_arastirmasi` |
| **Later observation** | `ertesi_gun_gozlemi`, `ikinci_gozlem`, `alternatif_baseline`, `elle_dogrulama` |

### Caveat: the taxonomy is agent-generated and long-tailed

`class` has 25 values across 52 records; `subclass` has **50 values across 52
records** — effectively free text. `impact` and `fix_type` are similar.

This is itself a finding rather than a defect to hide. An agent asked to
classify its own failures **invents a new category almost every time** unless
constrained to a closed vocabulary. Only `class`, `detected_by`,
`latency_days`, and `is_repeat` are reliable for aggregation; `subclass`
should be treated as a label, not a variable.

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
