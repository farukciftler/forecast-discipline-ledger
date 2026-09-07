# Forecast Discipline Ledger

A 20-day (and continuing) record of an LLM agent making dated, scored,
pre-registered predictions about six financial assets — and, separately, a
structured log of every operational error the agent made while doing it.

This directory is **fully anonymized** and contains no personal information.
See [Privacy](#privacy-and-anonymization) below.

---

## What this is

Two datasets that happen to be produced by the same daily process:

**1. A forecast calibration ledger.** Every trading day the agent writes a
point forecast, an 80% interval, and a probability of an up-move, for each of
six assets at 1-day, 1-week and 1-month horizons — *before* the outcome is
known. Forecasts are sealed, then scored automatically against the realized
value and against three baselines (naive / drift / momentum).

**2. An agent error log.** Every operational mistake — a mis-read number, a
wrong model assumption, an engine bug, a process failure — is recorded with
structured fields: what class of error, which mechanism caught it, **who**
caught it (the agent or the human), and **how many days it stayed hidden**.

The second dataset is the more unusual one. Agent evaluation is normally
*episodic* — one task, pass or fail. This is longitudinal operational failure
telemetry from a single continuing task with real consequences and a human in
the loop.

## What this is **not**

- **Not an investment strategy, and not investment advice.** No position
  sizes, no holdings, and no trading decisions appear anywhere in this
  dataset. The forecasts were never used to trade.
- **Not a claim that LLMs can forecast prices.** The headline result so far
  is the opposite (see [FINDINGS.md](FINDINGS.md)).
- **Not a controlled study.** n=1 agent, n=1 operator, n=1 domain, and — so
  far — n=1 volatility regime. See *Limitations*.

## Headline results so far (n=148 scored forecasts, 20 days)

| Question | Result |
|---|---|
| Does the point forecast reduce error spread vs. knowing only the mean? | **No** — 5 of 6 assets show ≤0 gain, 3 are negative |
| Do forecasts beat all three baselines? | **No** — 39.1% [31.0–47.7], p=0.99 |
| Does `p_up` beat the running base rate (Brier skill score)? | **No** — BSS = −0.25 |
| Are the 80% intervals calibrated? | **No, too wide** — 87.2% coverage, p=0.030 |
| Median days for the agent to detect its own error | **1** (mean 2.6, max 15) |
| Share of errors that were repeats of a prior recorded error | **27%** |

These are all *negative or diagnostic* results, and they are reported as the
primary findings rather than buried. The design reason is in
[PREREGISTRATION.md](PREREGISTRATION.md): the analysis plan was fixed before
the data existed, so there is no subgroup to retreat into.

## Files

| Path | Contents |
|---|---|
| [METHODS.md](METHODS.md) | Protocol, scoring rules, baselines, band construction |
| [PREREGISTRATION.md](PREREGISTRATION.md) | Hypotheses, tests, minimum n, thresholds — fixed in advance |
| [FINDINGS.md](FINDINGS.md) | Results to date, with caveats |
| [CASES.md](CASES.md) | Anonymized case studies — how the failures actually looked |
| [CODEBOOK.md](CODEBOOK.md) | Column definitions and category-label translations |
| `data/*.csv` | The datasets |
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

Assets appear only as `A1`…`A6` with a generic descriptor (asset class,
rough composition, pricing mechanics). The pseudonym mapping lives only in
the private repository and is **not** in this directory.

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
   so the 27% repeat rate has nothing to be compared against.
2. **Unknown denominator.** The error log contains only *detected* errors.
   Detection latency is measurable; the error *rate* is not. This is classic
   under-ascertainment and it biases every rate-like quantity.
3. **One regime.** The entire sample sits in a single, unusually calm and
   directional market window. Four of six assets traded at 60–73% of their
   250-day volatility. Any interval-calibration conclusion is conditional on
   that.
4. **Self-reported.** The agent classifies its own errors. Hypothesis H9 in
   the pre-registration exists precisely to test whether that self-assessment
   is biased in its own favor — and a *significant* result there is bad news,
   not good.
5. **n is small.** 20 days, 148 scored rows, ~3 effectively independent
   observations per day. Nothing here is statistically settled.

## Author

Abdullah Faruk Ciftler — [@farukciftler](https://github.com/farukciftler)

The ledger is maintained by a language-model agent under human supervision;
the agent writes the forecasts and the error records, the human reviews them,
and roughly one in five errors in the log was caught by the human rather than
the agent (see `detected_by` in `data/error_log.csv`).

## License and citation

- **Data and documentation:** [CC BY 4.0](LICENSE)
- **Code in `analysis/`:** MIT

Cite via [`CITATION.cff`](CITATION.cff).

## Anonymization

This repository is generated by an export step that operates on a **whitelist**:
a column is published only if it is named explicitly in the exporter. A separate,
independently-run audit script must pass before release; it checks for forbidden
terms, amount-shaped columns, free text, non-English residue, vendor/model names
and country markers.

Neither the exporter nor the auditor is published here — the exporter carries the
alias mapping and the auditor carries the forbidden-term list, so publishing
either would defeat the anonymization.

What is removed: amounts, balances, unit counts, price **levels**, institution,
instrument, vendor and person names, free-text notes, and any non-English text.
What is kept: percentage returns, forecast/interval/probability structure,
scoring outcomes, error-log categories with detection latency, and public market
variables.

**Pseudonyms.** Assets appear as `A1`…`A7`. The forecasting model appears as
`model_A` / `model_B` — the distinction matters analytically (different models
are not pooled) but the vendor is not named. Country-specific market variables
are renamed to role labels (`domestic_equity_index`, `usd_local_fx`,
`domestic_policy_rate`); global public benchmarks keep their usual names.

**Accepted residual risk.** A fund's return series could in principle be matched
against public NAV series and the instrument identified. That reveals nothing
about any person: no amount, no holding size, no account, no location.
