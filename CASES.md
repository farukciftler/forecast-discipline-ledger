# Case studies

Five anonymized cases. Each is drawn from the error log and contains no
identifying information. They are here because the structured fields in
`error_log.csv` record *that* something failed, not *how* it looked — and the
"how" is what transfers to other agent systems.

---

## 1. The same scenario, three fields, three different wrong behaviours

**Class:** engine bug · **Latency:** 0 days · **Detected by:** agent

A daily record file holds three top-level structures: a list of forecasts, a
list of evidence items, and a snapshot of market variables. On a day when the
file legitimately needed to be resubmitted — to add one field to existing
forecasts — each of the three behaved differently:

| structure | behaviour on resubmission | correct? |
|---|---|---|
| forecasts | matched on `(asset, horizon)`, replaced | **yes** |
| market variables | **overwritten** — 62 fields collapsed to 5 | no |
| evidence | **duplicated** — 9 items became 18 | no |

Both bugs were silent. The overwrite was caught only because a *different*
validator happened to fire ("market state incomplete"); the duplication was
caught only because an unrelated field count was being inspected.

The instructive part is not that there were bugs. It is that **the correct
pattern already existed in the same file** — the forecast list did the right
thing — and had simply not been applied to the other two structures. The
failure was not missing knowledge; it was **inconsistent application of
knowledge already present in the codebase.**

Why the duplication mattered beyond tidiness: evidence count is the
denominator of a pre-registered hypothesis about scheduled-event surprises.
A doubled denominator corrupts that analysis invisibly. This is the same
argument the project uses for mandatory evidence collection — *a gap in a
price series is visible on a chart, a gap in an evidence series is visible
nowhere* — except in the surplus direction.

## 2. A correct prediction of the event, a wrong prediction of the price

**Class:** model error · **Latency:** 1 day

The previous day's forecast carried an explicit invalidator: *"if the central
bank minutes read clearly hawkish, the metal falls."*

The minutes read clearly hawkish — three officials dissented in favour of a
hike. The metal rose 3.5%, breaching the 80% interval.

The cause was a second, stronger driver arriving the same day: the treasury
announced a doubling of its long-dated debt buyback capacity, long yields
fell sharply, and the dollar weakened. The event was called correctly; the
*mapping from event to price* was not.

Recorded lesson: **single-variable invalidators are weak.** They encode "if X
then Y" in a system where the realized outcome is the sum of several X's.
Subsequent invalidators are written as three independent channels rather than
one condition.

## 3. A disagreement between two models, written as a test rather than a guess

**Class:** model uncertainty · **Latency:** 0 days

On one day, three funds' residuals against their measured regression models
did not scatter randomly — they **split by geography**:

| fund | assets | model input | predicted | actual | residual | z |
|---|---|---|---|---|---|---|
| domestic equity | domestic | +2.34% | +1.93% | **+2.81%** | +0.88 pp | +1.7 |
| foreign equity | foreign | +0.16% | +0.29% | **−0.94%** | −1.22 pp | −0.93 |
| commodity | foreign | +2.83% | +2.33% | **−1.11%** | −3.44 pp | −2.13 |

Hypothesis: the domestic exchange closes *inside* the fund valuation window;
the foreign session closes mostly *outside* it. So a NAV dated *T* may price
the domestic session of *T−1* fully but the foreign session only partially.

That day was unusually good for testing it, because more than half of the
metal's move happened after the valuation window closed — and this is
measurable: at the afternoon benchmark fixing the move was +1.30%, at the
futures settlement +2.83%.

**The hypothesis explains about a third of the residual, and a 251-observation
regression contradicts it.** So it was not adopted. Three things were done
instead:

1. The point estimates for the affected funds were placed **between** the two
   alignments; intervals were widened by the size of the disagreement.
2. The unaffected domestic fund's interval was **not** widened — the
   hypothesis says it should not be, and its residual agreed.
3. The next day's forecast for the most-affected fund was made **deliberately
   discriminating**: the two alignments implied +1.20% and +2.87%. The point
   was set between them and **the reading rule was written down in advance**:
   above +2.5% supports the window hypothesis · around +1.2% preserves the
   established model · negative again means both are inadequate and daily
   forecasting for that asset should stop.

The bias check was written into the record at the same time: widening
intervals *worsens* the already-significant over-coverage, so this correction
cannot be flattering the agent's scorecard.

Postscript: the reason the regression could not simply be rerun that day is
itself a case — see §5.

## 4. A deviation flagged for its direction, not its size

**Class:** faulty inference · **Latency:** 5 days

A "sharp divergence" between two funds was recorded and then used for two
days as a reason to lower confidence and widen an interval.

When the deviation was finally *measured*, it sat at the 87th of 246
historical observations — the top 35%, an event seen roughly every third day.
The decisive evidence was not the percentile: it was that **the previous day
had produced a larger deviation in the opposite direction and had not been
flagged at all.**

What triggered the flag was the deviation's sign, not its magnitude.

Resulting hard rule, now in METHODS §10: *a deviation is not recorded as an
anomaly until its percentile in that asset's own historical deviation
distribution has been computed. Outside the top 10% → no record.*

## 5. A tool that answered a smaller question than it was asked

**Class:** data source · **Latency:** unknown (present from the start)

The fund price fetcher accepted a period parameter — 1, 3, 12, 36 months. It
was called with a 12-month period in order to measure a beta relationship.

It returned **10 observations.**

The API had honoured the parameter and returned a year of data; the
*formatter* truncated the output to the last ten rows before printing. The
parameter was accepted, the request was correct, and the answer was silently
a hundredth of what was asked for.

The consequence was not a wrong number — it was a **question that could not be
asked**. A 251-observation model could not be re-tested, so the model
uncertainty in §3 stayed unresolved for longer than it needed to.

Two failure modes worth separating:

- A source that *breaks* announces itself.
- A source that *narrows* does not. It keeps returning well-formed, correct,
  current data — just not enough of it.

The second is the dangerous one, and it will not show up in a health check
that only asks "did the fetch succeed?". After the fix the same call returns
252 observations.

---

## What these have in common

Four of the five were **silent**: nothing failed, nothing errored, and the
output looked well-formed. They were found by a cross-check, an inconsistency
in a count, a percentile computed late, and an unrelated field inspection.

That is the practical argument for the whole apparatus. The errors that a
test suite catches are not the ones that damage a long-running measurement.
The damaging ones produce plausible output — and the only defence is a
recorded expectation to compare against.
