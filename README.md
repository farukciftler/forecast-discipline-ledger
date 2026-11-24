# Forecast Discipline Ledger

A three-month record (77 forecast days) of an LLM agent making dated, scored,
pre-registered predictions about six financial assets — and, separately, a
structured log of every operational error the agent made while doing it.

**This release is a frozen study window: 2026-08-01 to 2026-10-31.** A row is
included only if the forecast was written, its target date fell, and its
outcome was observed inside the window. The end date is the last day of the
third calendar month and was not chosen by looking at results.

This directory is **fully anonymized** and contains no personal information.
See [Privacy](#privacy-and-anonymization) below.

---

## What this is

Two datasets that happen to be produced by the same daily process:

**1. A forecast calibration ledger.** Every trading day the agent writes a
point forecast, an 80% interval, and a probability of an up-move, for each
tradeable asset at 1-day, 1-week and 1-month horizons — *before* the outcome is
known. Forecasts are sealed, then scored automatically against the realized
value and against three baselines (naive / drift / momentum).

**2. An agent error log.** Every operational mistake — a mis-read number, a
wrong model assumption, an engine bug, a process failure — is recorded with
structured fields: what class of error, which mechanism caught it, **who**
caught it (the agent or the human), and **how many days it stayed hidden**.

The second dataset is the more unusual one. Agent evaluation is normally
*episodic* — one task, pass or fail. This is longitudinal operational failure
telemetry from a single long-running task with real consequences and a human in
the loop.

## What this is **not**

- **Not an investment strategy, and not investment advice.** No position
  sizes, no holdings, and no trading decisions appear anywhere in this
  dataset. The forecasts were never used to trade.
- **Not a claim that LLMs can forecast prices.** The headline result is the
  opposite (see [FINDINGS.md](FINDINGS.md)).
- **Not a controlled study.** One agent family, one operator, one domain, one
  three-month window. See *Limitations*.

## Headline results (primary pool: 706 scored forecasts on 62 forecast days)

| Question | Result |
|---|---|
| Do forecasts beat all three baselines at once? (H1) | **No** — 217/706 = 30.7% of rows [27.4–34.2], and 9 of 58 forecast days |
| Do they beat each baseline taken alone? | Yes: naive 54.5%, drift 62.5%, momentum 78.2% |
| Are the 80% intervals calibrated? (H2) | **No, too wide** — 627/706 = 88.8% coverage [86.3–90.9], p<0.0001 |
| Does `p_up` beat the running base rate? | Pooled Brier skill score +0.122, **entirely from one managed-rate asset**; −0.019 against each asset's own base rate |
| Does detection latency fall over time? (H7) | **No** — Spearman +0.122 over 146 records |
| Days for the agent to detect its own error | median **1**, mean 6.0, max 60 |
| Share of errors that repeat a prior recorded error | **48.6%** [40.7–56.7] |

Note the gap between the first two rows: the agent clears each baseline
individually and fails to clear all three simultaneously. That gap is the
result. A baseline that can be beaten by accident is not a baseline.

These are *negative or diagnostic* results, and they are reported as the
primary findings. The design reason is in
[PREREGISTRATION.md](PREREGISTRATION.md): the analysis plan was fixed before
the data existed, so there is no subgroup to retreat into. Pre-registered
hypotheses that did not reach their minimum sample (H3, H9) or could not be
run as specified (H8) are reported as such in [FINDINGS.md](FINDINGS.md).

## Files

| Path | Contents |
|---|---|
| [METHODS.md](METHODS.md) | Protocol, scoring rules, baselines, band construction |
| [PREREGISTRATION.md](PREREGISTRATION.md) | Hypotheses, tests, minimum n, thresholds — fixed in advance |
| [FINDINGS.md](FINDINGS.md) | Results for the study window, with caveats |
| [CASES.md](CASES.md) | Anonymized case studies — how the failures actually looked |
| [CODEBOOK.md](CODEBOOK.md) | Column definitions and category-label translations |
| `data/*.csv` | The datasets, including `study_window.csv` (the window and how much of it the routine covered) |
| `analysis/reproduce.py` | Regenerates every number in FINDINGS.md from `data/` alone |

## Reproducing

```bash
python3 analysis/reproduce.py
```

Standard library only, no dependencies. Every figure quoted in FINDINGS.md is
printed by this script from the CSVs in this directory. If a number in the
prose disagrees with the script, the script is right.

---

## Privacy and anonymization

The source ledger is a private repository containing one household's actual
portfolio. **None of that crosses into this directory.** Export is
**allowlist-based**: a column is emitted only if it is explicitly named in the
exporter. The default for any new or unrecognized field is *not exported* —
the opposite of a blocklist, which leaks silently as the source schema grows.

Never exported, by rule:

- Any monetary amount, balance, portfolio total, or position size
- Any quantity or unit count
- **Price levels** — only percentage returns are exported
- Asset, fund, institution, or account identifiers of any kind
- Maturity dates, account numbers
- All free text: forecast rationales, evidence claims, notes, error summaries
- A second household ledger present in the source — never read by the exporter

Assets appear only as `A1`…`A8` with a generic descriptor (asset class,
rough composition, pricing mechanics), the forecasting models as `model_A`…
`model_D`, and allocation decisions as `D1`…. The pseudonym mappings live only
in the private repository and are **not** in this directory. The local market
calendar is not published either: holiday dates would identify the country, so
only counts appear in `study_window.csv`.

The exporter runs two independent leak audits on its own output before
writing succeeds: a **text** scan for identifying terms, and a **structural**
scan of column *names* for amount-bearing or free-text patterns. The second
exists because the first cannot catch a monetary value — `1234.56` looks
innocent in a cell but not in a column called `value_try`. A failed audit is
a non-zero exit.

**Residual re-identification risk, stated plainly:** a fund's *return series*
could in principle be matched against public NAV data to identify the fund.
That reveals nothing about a person — not how much was held, not where, not
by whom — because no amount or quantity is exported. This risk is accepted
knowingly rather than left unmentioned.

## Dates

Calendar dates are retained. They refer to public market events (central bank
minutes, treasury announcements, index closes) and are what makes the market
context verifiable. Dates alone identify no one.

## Limitations

1. **No control arm.** There is no "same agent without an error log" condition,
   so the 48.6% repeat rate has nothing to be compared against.
2. **Unknown denominator.** The error log contains only *detected* errors.
   Detection latency is measurable; the error *rate* is not. This is classic
   under-ascertainment and it biases every rate-like quantity.
3. **Self-reported and self-categorised.** The agent classifies its own
   errors, and chose the categories. Hypothesis H9 exists to test whether that
   self-assessment is biased in its own favor; it did not reach its minimum
   sample in this window.
4. **Small n, correlated rows.** 62 forecast days in the primary pool and
   about three effectively independent series once correlation between assets
   is accounted for. Prefer the day-level tests. Nothing here is statistically
   settled.
5. **Mixed models and a late-fixed window.** Four model versions wrote
   forecasts in the window and the primary pool mixes three of them; the
   pre-registration did not foresee a model change. The window's end date was
   fixed when the paper was prepared.
6. **Funds are priced one day late.** A 1-day fund forecast is written after
   the session it will be priced on has traded. Single-baseline wins and
   error-spread gains for funds are therefore not read as skill (H12).
7. **Two Brier baselines.** `analysis/reproduce.py` leads with the
   pre-registered *walk-forward* base rate and also prints the *full-sample*
   one, a look-ahead and therefore harder baseline. The two are +0.122 and
   +0.114; neither is a skill claim (FINDINGS §4).

## License and citation

Data and documentation released for research and educational use. If you use
the dataset, please cite it as an anonymized single-agent forecast and error
ledger and link back to this repository.
