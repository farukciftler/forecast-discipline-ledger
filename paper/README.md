# Paper

Manuscript for the dataset in this repository.

| file | what it is |
|---|---|
| `main.tex` | the manuscript — **contains no hand-typed data numbers** |
| `numbers.tex` | **generated**; `\newcommand` for every quoted figure |
| `compute_numbers.py` | recomputes all of them from `../data/*.csv` |
| `check_paper.py` | guard: fails if a number was typed by hand or has gone stale |

## The workflow

The paper argues that a rule which lives only in prose is a rule contingent on
someone remembering it. Applying that to the paper itself: **a manuscript with
hand-typed numbers goes stale silently the moment the ledger grows by one day.**
So it does not have any.

```
data/*.csv
    │
    ├─ compute_numbers.py --latex ─→ numbers.tex   (68 \newcommand definitions)
    │                                    │
    └──────────────────────────── main.tex \input{numbers}
                                         │
                          check_paper.py ─┴─→ CI
```

`main.tex` writes `\CovRate` and `\ErrN`, never `0.869` and `97`.

### Day to day

```bash
python3 paper/compute_numbers.py --latex   # regenerate after the data moves
python3 paper/check_paper.py               # verify before committing
```

`check_paper.py` fails on two things, and both are tested to actually fire:

1. **An undefined macro in `main.tex`** — catches a number typed by hand, since
   any hand-typed figure would either be a bare literal (caught in review) or a
   macro that does not exist.
2. **A stale `numbers.tex`** — it regenerates into a temporary file and
   byte-compares. If the data moved and nobody re-ran the generator, this fails.

### CI

`.github/workflows/ci.yml` runs on every push, pull request and release:

| job | checks |
|---|---|
| `data` | `reproduce.py` runs · `check_paper.py` passes · no non-English residue · no vendor/institution identifiers in `data/` · `CITATION.cff` has required keys |
| `paper` | regenerates `numbers.tex` and **fails if the committed copy differs** · compiles the PDF · uploads it as an artifact · attaches it to releases |

The PDF is never committed; it is built from source every time.

## Building locally

No local LaTeX is required to work on the numbers. To build the PDF you need
`article` plus `geometry`, `booktabs`, `amsmath`, `hyperref`, `xcolor` and
`caption` — all present in any standard distribution and on Overleaf.

```bash
cd paper && pdflatex main.tex && pdflatex main.tex   # twice, for references
```

Or upload `main.tex` and `numbers.tex` to [Overleaf](https://overleaf.com),
which is also the usual route to an arXiv submission.

## Before submitting

1. **Decide on model disclosure.** The released data pseudonymises the
   forecasting model as `model_A` / `model_B`, and the manuscript follows suit
   through the `\modelA` / `\modelB` macros at the top of `main.tex`. If you
   name the model family, redefine those two macros and add a sentence to
   *Data availability*.
2. **Re-run the generator**, then read the abstract: the day count, record
   counts and every rate update themselves, but the *prose* around them
   ("more than a third", "roughly three per day") does not. Those are the
   sentences to re-check.
3. **arXiv category:** `cs.SE` primary, `cs.AI` cross-list.
4. **arXiv licence:** CC BY 4.0, matching the dataset.
5. **Endorsement:** a first submission to `cs.SE` or `cs.AI` may require
   endorsement from an established author in that category.

## Honest scope

This is an **interim report**. 38 forecast days with roughly three effectively
independent observations per day is thin for any forecasting claim, and the
manuscript says so rather than hedging. The forecasting section exists to be
null and to show the null was pre-registered; the contribution is the
operational error telemetry and the failure mode named in §5.

Three months of additional data would cross several pre-registered thresholds
that are currently unmet. arXiv versioning (v2, v3) is the normal way to handle
that, and the workflow above means a new version is a regeneration, not a
retyping.
