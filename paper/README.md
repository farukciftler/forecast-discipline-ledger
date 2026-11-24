# Paper

Manuscript for the dataset in this repository. It analyses a frozen study
window, 2026-08-01 to 2026-10-31.

| file | what it is |
|---|---|
| `main.tex` | the manuscript; **contains no hand-typed data numbers** |
| `numbers.tex` | **generated**; one `\newcommand` for every quoted figure |
| `compute_numbers.py` | recomputes all of them from `../data/*.csv` |
| `check_paper.py` | guard: fails if a number was typed by hand or has gone stale |
| `ALLOWED_LITERALS` in `check_paper.py` | the short list of numbers that are legitimately not data, each with a reason |
| `refs.bib` | bibliography, every entry verified against the publisher record |

## The workflow

The paper argues that a rule which lives only in prose is a rule contingent on
someone remembering it. Applied to the paper itself: a manuscript with
hand-typed numbers is wrong the moment the data changes and nobody notices.
So it has none.

```
data/*.csv
    │
    ├─ compute_numbers.py --latex ─→ numbers.tex
    │                                    │
    └──────────────────────────── main.tex \input{numbers}
                                         │
                          check_paper.py ─┴─→ CI
```

`main.tex` writes `\CovRate` and `\ErrN`, never the figures themselves.

```bash
python3 paper/compute_numbers.py --latex   # regenerate
python3 paper/check_paper.py               # verify before committing
```

The data is a frozen release, so `numbers.tex` is deterministic: regenerating
it on any day reproduces it byte for byte.

## What `compute_numbers.py` counts

Pools follow `PREREGISTRATION.md`, not convenience:

- rows from different protocol versions are never pooled;
- one-month outputs are projections and enter no skill claim;
- unresolved rows and flagged substitutions enter no test.

The **primary pool** is therefore: resolved, not a flagged substitution, 1-day
and 1-week horizons, latest protocol version. An earlier draft pooled
everything and quoted that as the headline, which contradicted the
pre-registration the same draft cited. `analysis/reproduce.py` and
`analysis/check_docs.py` use the same definition.

## What `check_paper.py` checks

1. **An undefined macro in `main.tex`.**
2. **A bare numeric literal in the body.** Literals must either be generated
   or added to `ALLOWED_LITERALS` with a reason: the DOI prefix, `CC BY 4.0`,
   subscript labels, and thresholds fixed by the pre-registration are there.
3. **A stale `numbers.tex`.** It regenerates into a temporary file and
   byte-compares.
4. **Machine-generated prose tells.** Em-dashes, the standard vocabulary,
   filler openers, connective filler, generic closers, and unverified
   time-span phrases.

All four were tested by deliberately breaking them.

## CI

`.github/workflows/ci.yml` runs on every push, pull request and release:

| job | checks |
|---|---|
| `data` | `reproduce.py` runs · `check_docs.py` and `check_paper.py` pass · no non-English residue · no vendor or institution identifiers in `data/` · `CITATION.cff` has required keys |
| `paper` | regenerates `numbers.tex` and fails if the committed copy differs · compiles the PDF · assembles the arXiv source package · attaches both to releases |

The PDF is never committed; it is built from source every time.

## Building locally

No local LaTeX is required to work on the numbers. To build the PDF you need
`article` plus `geometry`, `booktabs`, `amsmath`, `hyperref`, `xcolor` and
`caption`, all present in any standard distribution and on Overleaf.

The manuscript has a bibliography, so a single `pdflatex` pass is not enough:

```bash
cd paper && latexmk -pdf main.tex
```

By hand, all four passes are required; skipping `bibtex` gives a PDF with an
empty references section and no error:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

The simplest way to get a correct PDF without installing anything is to take
the one CI built: open the latest run under **Actions** and download the
`manuscript` artifact, or take the PDF attached to the most recent release.

## Citations

Every entry in `refs.bib` was checked against the publisher or conference
record for author list, venue, year, volume and pages before being written
down; none was reconstructed from memory. Re-verify before submission anyway.

The related-work section ends with a statement that we did not find prior work
releasing longitudinal agent error telemetry. That is a claim about our
search, not about the literature, and it is phrased that way on purpose.

## Submitting to arXiv

Step by step: **[ARXIV.md](ARXIV.md)**.

## Scope

The paper reports a completed three-month window. Its forecasting section
exists to be null and to show that the null was pre-registered; the
contribution is the operational error telemetry and the failure mode named in
§6. One agent family, one task, one supervisor: the manuscript says what that
sample cannot support.

The source ledger kept running after the window closed. Later data is not in
this release and is not described in the paper. A later study would be a new
window with its own release, not an edit to this one.
