# arXiv submission, step by step

Everything below assumes you are the submitting author. Nothing here needs a
LaTeX installation.

---

## 0. Get the files

CI builds both on every push. Two ways to fetch them.

**From a release** (easiest): open
[Releases](https://github.com/farukciftler/forecast-discipline-ledger/releases),
pick the newest, download `main.pdf` and `arxiv-submission.tar.gz`.

**From the latest build** (has the newest commits, may be ahead of the release):

```bash
gh run download "$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')" \
   -n manuscript       -D ~/Desktop/arxiv-gonderim
gh run download "$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')" \
   -n arxiv-submission -D ~/Desktop/arxiv-gonderim
```

Or in the browser: **Actions → newest run → Artifacts**.

`main.pdf` is for you to read. `arxiv-submission.tar.gz` is what you upload.

---

## 1. Why you upload source, not the PDF

arXiv prefers LaTeX source and compiles it on their servers. A PDF-only
submission is accepted but flagged and cannot be re-rendered later.

**arXiv does not run BibTeX.** If you upload only `main.tex`, the reference
list comes out empty on their servers and the build gives you no useful error.
`main.bbl` has to be in the package. It is, and CI fails if it ever is not:

```
numbers.tex   every figure the manuscript quotes
main.tex      the manuscript
refs.bib      the bibliography source
main.bbl      the compiled bibliography  <- the one people forget
```

No `.aux`, `.log`, `.out`. CI checks for those too.

---

## 2. Account and endorsement

1. Register at [arxiv.org/user/register](https://arxiv.org/user/register).
   **Use an institutional address if you have one** — it usually grants
   automatic endorsement. A personal address usually does not.
2. Link your ORCID (`0009-0001-9310-3812`) in account settings. Submissions
   then appear on your ORCID record automatically.
3. **Endorsement.** A first submission to `cs.SE` or `cs.AI` normally needs an
   endorsement from someone who has already published in that category. After
   step 4 arXiv shows you an endorsement code and a link to send to a
   colleague. **Start this early: it depends on someone else replying.**

---

## 3. Submit

[arxiv.org/submit](https://arxiv.org/submit) → **Start New Submission**.

| Field | What to enter |
|---|---|
| Archive | **Computer Science** |
| Primary category | **cs.SE** (Software Engineering) |
| Cross-list | **cs.AI** |
| Licence | **CC BY 4.0** — matches the dataset |
| Title | copy from the compiled PDF |
| Authors | `Ciftler, Abdullah Faruk` |
| Abstract | copy from the PDF, **plain text** |
| Comments | e.g. `Interim report. Data and code: https://doi.org/10.5281/zenodo.22643370` |
| ACM class | `D.2.5` (Testing and Debugging), optional |

### The abstract field

Paste plain text, not LaTeX. Strip `\emph{}`, `\%`, `\S`, `---`. Keep the
numbers as they appear in the PDF, since the macros are already expanded there.
arXiv rejects abstracts over 1920 characters.

### Upload

Upload `arxiv-submission.tar.gz` as-is. arXiv unpacks it and runs LaTeX.

---

## 4. Check the generated PDF before you commit

arXiv shows you its own build. Do not skip this.

- Does the reference list have **six** entries? Empty means `main.bbl` did not
  make it into the package.
- Does the title page say `Figures generated <date>, <n> values`? That line is
  a deliberate staleness check.
- Any `??` in the text means an unresolved cross-reference.

If it looks right: **Submit**.

---

## 5. After submitting

- Announcement is next business day, 20:00 ET, weekdays only.
- You get `arXiv:26XX.XXXXX`. That identifier is permanent.
- **`v1` cannot be deleted.** Later versions are `v2`, `v3`, and all remain
  visible and separately citable.

### Close the loop

1. Add the arXiv ID to `CITATION.cff` and to the repository README.
2. Add it to the Zenodo record as a related identifier
   (`isSupplementTo`), so dataset and paper point at each other.
3. Cut a release so the change is archived and gets its own DOI.

---

## 6. Updating later

Upload a new source package on the abstract page: **Replace**. It becomes `v2`
in minutes; the identifier does not change and endorsement is not needed again.

Regenerate first, or the new version ships stale numbers:

```bash
python3 paper/compute_numbers.py --latex
python3 paper/check_paper.py     # must exit 0
```

Then push, let CI build, and download the new `arxiv-submission.tar.gz`.

**Note on versions.** Strengthening a claim between `v1` and `v2` is normal.
Retracting one is a permanent public record. This paper's central claim rests
on two clear instances today; if you would rather it rested on more, the honest
move is to wait rather than to publish and walk back.
