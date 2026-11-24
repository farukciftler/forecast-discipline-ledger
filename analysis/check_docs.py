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
    F = load("forecasts.csv")
    # Use the SAME population the other two scripts use: resolved, not a
    # flagged substitution, forecast horizons only, latest protocol version.
    # A checker with its own definitions produces false alarms, and an audit
    # that cries wolf gets ignored the one time it is right.
    ALL = [r for r in load("resolutions.csv")
           if r["status"] == "resolved" and r.get("dirty_substitution") != "yes"]
    latest = max(r["protocol_version"] for r in ALL if r["protocol_version"])
    R = [r for r in ALL
         if r["horizon_kind"] == "forecast" and r["protocol_version"] == latest]
    lat = [int(r["latency_days"]) for r in E
           if r["latency_days"].strip().lstrip("-").isdigit()]
    rep = sum(1 for r in E if r["is_repeat"] == "yes")
    lo, hi = wilson(rep, len(E))
    days = len({r["as_of"] for r in F if r.get("as_of")})
    allk = sum(1 for r in R if r["beat_all_three"] == "True")
    alln = sum(1 for r in R if r["beat_all_three"] in ("True", "False"))
    covk = sum(1 for r in R if r["in_band"] == "1")
    covn = sum(1 for r in R if r["in_band"] in ("0", "1"))
    W = load("study_window.csv")[0]
    both = ["FINDINGS.md", "README.md"]

    # (label, expected substring, which files must carry it)
    checks = [
        ("window", f"{W['window_start']} to {W['window_end']}", both),
        ("forecast days", f"{days} forecast days", both),
        ("forecasts written", f"{len(F)} forecasts written", ["FINDINGS.md"]),
        ("primary pool size", f"{len(R)} scored forecasts", both),
        ("error record count", f"{len(E)} error records", ["FINDINGS.md"]),
        ("joint baseline rows", f"{allk}/{alln}", both),
        ("coverage rows", f"{covk}/{covn}", both),
        ("mean latency", f"mean {st.mean(lat):.1f}", both),
        ("max latency", f"max {max(lat)}", both),
        ("repeat count", f"{rep}/{len(E)} = {rep / len(E) * 100:.1f}%", ["FINDINGS.md"]),
        ("repeat rate", f"{rep / len(E) * 100:.1f}%", ["README.md"]),
        ("repeat CI", f"[{lo * 100:.1f}\u2013{hi * 100:.1f}]", both),
    ]

    bad = []
    for label, want, files in checks:
        for fn in files:
            text = open(os.path.join(ROOT, fn), encoding="utf-8").read()
            if want not in text:
                bad.append(f"{fn}: {label} -- expected to find {want!r}")

    # A frozen release must not describe itself as unfinished. This is the
    # wording that got the first manuscript returned, and nothing was checking
    # the documents for it.
    stale = re.compile(r"\b(interim|so far|to date|and continuing|ongoing)\b", re.I)
    for fn in both:
        text = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        for m in sorted(set(x.group(0).lower() for x in stale.finditer(text))):
            bad.append(f"{fn}: describes a frozen release as unfinished -- {m!r}")

    if bad:
        print("DOCS OUT OF STEP WITH data/:\n")
        for b in bad:
            print("  " + b)
        print("\nRegenerate the prose figures from analysis/reproduce.py and edit "
              "the markdown to match. The numbers moved; the sentences did not.")
        return 1
    print(f"ok: README.md and FINDINGS.md agree with data/ "
          f"({len(E)} error records, {len(R)} primary-pool rows, {days} forecast days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
