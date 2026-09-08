# Forecast Discipline Ledger

A 39-day (and continuing) record of an LLM agent making dated, scored,
pre-registered predictions about seven financial assets — and, separately, a
structured log of every operational error the agent made while doing it.

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
telemetry from a single continuing task with real consequences and a human in
the loop.

## What this is **not**

- **Not an investment strategy, and not investment advice.** No position
  sizes, no holdings, and no trading decisions appear anywhere in this
  dataset. The forecasts were never used to trade.
- **Not a claim that LLMs can forecast prices.** The headline result so far
  is the opposite (see [FINDINGS.md](FINDINGS.md)).
- **Not a controlled study.** n=1 agent, n=1 operator, n=1 domain and, so
  far, n=1 volatility regime. See *Limitations*.

## Headline results so far (n=405 scored forecasts, 39 days)

| Question | Result |
|---|---|
| Does the point forecast reduce error spread vs. knowing only the mean? | **Mostly no** — 3 of 6 assets show ≤0 gain; only one (A4, +14.4%) is clearly positive |
| Do forecasts beat all three baselines at once? | **No** — 33.4% [28.8–38.4], p=1.0 |
| Do they beat each baseline taken alone? | Yes: naive 63.0%, drift 64.7%, momentum 75.7% (all p<0.001) |
| Does `p_up` beat the running base rate (Brier skill score)? | **Barely** — BSS = +0.020 walk-forward; −0.000 against a full-sample base rate |
| Are the 80% intervals calibrated? | **No, too wide** — 87.7% coverage [84.1–90.5], p=0.0001 |
| Median days for the agent to detect its own error | **1** (mean 5.9, max 37) |
| Share of errors that were repeats of a prior recorded error | **40.8%** [31.8–50.4] |

Note the gap between rows two and three: the agent clears each baseline
individually and fails to clear all three simultaneously. That gap is the
result. Beating a single baseline in a one-directional market is cheap.

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

Assets appear only as `A1`…`A7` with a generic descriptor (asset class,
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
   so the 40.8% repeat rate has nothing to be compared against.
2. **Unknown denominator.** The error log contains only *detected* errors.
   Detection latency is measurable; the error *rate* is not. This is classic
   under-ascertainment and it biases every rate-like quantity.
3. **One regime.** The entire sample sits in a single, unusually calm and
   directional market window; realized volatility ran below the 250-day
   figure for most assets. Any interval-calibration conclusion is conditional
   on that, and the excess interval coverage is at least partly a regime
   artifact rather than a pure band-width error.
4. **Self-reported.** The agent classifies its own errors. Hypothesis H9 in
   the pre-registration exists precisely to test whether that self-assessment
   is biased in its own favor — and a *significant* result there is bad news,
   not good.
5. **n is small.** 39 days, 405 scored rows, ~3 effectively independent
   observations per day once the correlation between assets is accounted for.
   Nothing here is statistically settled.
6. **Two Brier baselines, two answers.** `analysis/reproduce.py` scores `p_up`
   against a *walk-forward* base rate (only rows already seen); the manuscript
   scores it against the *full-sample* base rate, which is a look-ahead and
   therefore harder baseline. BSS is +0.020 under the first and −0.000 under
   the second. Neither is a skill claim; both round to nothing.

## License and citation

Data and documentation released for research and educational use. If you use
the dataset, please cite it as an anonymized single-agent forecast and error
ledger and link back to this repository.
