# Paper

Manuscript for the dataset in this repository.

| file | what it is |
|---|---|
| `main.tex` | the manuscript, plain `article` class, no external figures |
| `compute_numbers.py` | regenerates **every number in the manuscript** from `../data/*.csv` |

## Reproducing the numbers

```bash
python3 paper/compute_numbers.py
```

Standard library only — no dependencies, no network. Each section of the output
is labelled with the manuscript section it feeds (`S1`, `S3`, `S4`, …), so the
two can be diffed line by line.

## Building the PDF

No local LaTeX is required. The manuscript uses only `article` plus
`geometry`, `booktabs`, `amsmath`, `hyperref`, `xcolor` and `caption` — all
present in any standard distribution and on Overleaf.

```bash
pdflatex main.tex && pdflatex main.tex   # twice, for cross-references
```

Or upload `main.tex` to [Overleaf](https://overleaf.com), which is also the
usual route to an arXiv submission.

## Before submitting

1. **Decide on model disclosure.** The released data pseudonymises the
   forecasting model as `model_A` / `model_B`. The manuscript follows that
   convention through the `\modelA` / `\modelB` macros at the top of
   `main.tex`. If you name the model family in the paper, redefine those two
   macros and add a sentence to *Data availability*; leaving them as-is keeps
   manuscript and data consistent.
2. **Re-run `compute_numbers.py`** and check the manuscript against it. The
   ledger is ongoing, so every number moves as data accumulates.
3. **Update the abstract's day count and record counts** if time has passed.
4. **arXiv category:** `cs.SE` primary, `cs.AI` cross-list.
5. **arXiv licence:** CC BY 4.0, to match the dataset.
6. **Endorsement:** a first submission to `cs.SE` or `cs.AI` may require
   endorsement from an established author in that category. arXiv shows who
   can endorse once an account exists.

## Honest scope

This is an **interim report**. 38 forecast days with roughly three effectively
independent observations per day is thin for any forecasting claim, and the
manuscript says so rather than hedging. The forecasting section exists to be
null and to show that the null was pre-registered; the contribution is the
error telemetry in §4 and the failure mode named in §5.

Three months of additional data would cross several pre-registered thresholds
that are currently unmet. arXiv versioning (v2, v3) is the normal way to handle
that.
