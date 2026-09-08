#!/usr/bin/env python3
"""Check that the numbers written into README.md and FINDINGS.md still match
the data in data/.

The manuscript is protected: every figure in main.tex comes from numbers.tex,
which is generated, and check_paper.py fails the build if it falls behind. The
markdown had no such guard, and it drifted four separate times in one working
day. Each time the figures were correct when typed and wrong a few hours later,
which is the failure mode this project is about: a rule ("keep the docs in
step") that lives only in prose is a rule nobody enforces.

So this file does the enforcing. It recomputes the headline figures from the
CSVs and checks that each one appears verbatim in the prose. It cannot verify
that a sentence is *true*, only that the number it names is current. That is
the part that kept going wrong.

Standard library only. Exit 1 on the first drift.
"""
import csv
import os
import re
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return round((c - m) / d, 3), round((c + m) / d, 3)


def main():
    E = load("error_log.csv")
    # Use the SAME filters the other two scripts use. A checker with its own
    # definitions produces false alarms, and an audit that cries wolf gets
    # ignored the one time it is right.
    #   reproduce.py:        status == "resolved"
    #   compute_numbers.py:  distinct as_of days in forecasts.csv
    R = [r for r in load("resolutions.csv") if r["status"] == "resolved"]
    F = load("forecasts.csv")
    lat = [int(r["latency_days"]) for r in E
           if r["latency_days"].strip().lstrip("-").isdigit()]
    rep = sum(1 for r in E if r["is_repeat"] == "yes")
    lo, hi = wilson(rep, len(E))
    days = len({r["as_of"] for r in F if r.get("as_of")})

    # (label, expected substring, which files must carry it)
    checks = [
        ("error record count", f"{len(E)} error records", ["FINDINGS.md"]),
        ("error record count", f"{len(E)} in {days} days", ["FINDINGS.md"]),
        ("scored rows", f"{len(R)} scored forecasts", ["FINDINGS.md", "README.md"]),
        ("mean latency", f"mean {st.mean(lat):.1f}", ["FINDINGS.md", "README.md"]),
        ("max latency", f"max {max(lat)}", ["FINDINGS.md", "README.md"]),
        ("repeat count", f"{rep}/{len(E)} = {rep / len(E) * 100:.1f}%", ["FINDINGS.md"]),
        ("repeat rate", f"{rep / len(E) * 100:.1f}%", ["README.md"]),
        ("repeat CI", f"[{lo * 100:.1f}–{hi * 100:.1f}]", ["FINDINGS.md", "README.md"]),
    ]

    bad = []
    for label, want, files in checks:
        for fn in files:
            text = open(os.path.join(ROOT, fn), encoding="utf-8").read()
            if want not in text:
                bad.append(f"{fn}: {label} -- expected to find {want!r}")

    # The day count is written into the first line of both files as "N-day" or
    # "N calendar days"; check whichever form each file uses.
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    if f"A {days}-day" not in readme:
        bad.append(f"README.md: day count -- expected 'A {days}-day'")
    findings = open(os.path.join(ROOT, "FINDINGS.md"), encoding="utf-8").read()
    if f"{days} calendar days" not in findings:
        bad.append(f"FINDINGS.md: day count -- expected '{days} calendar days'")

    if bad:
        print("DOCS OUT OF STEP WITH data/:\n")
        for b in bad:
            print("  " + b)
        print("\nRegenerate the prose figures from analysis/reproduce.py and edit "
              "the markdown to match. The numbers moved; the sentences did not.")
        return 1
    print(f"ok: README.md and FINDINGS.md agree with data/ "
          f"({len(E)} error records, {len(R)} scored rows, {days} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
