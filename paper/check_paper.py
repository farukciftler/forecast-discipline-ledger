#!/usr/bin/env python3
"""Guard: the manuscript must not contain hand-typed data numbers.

Two checks, both failing loudly:

  1. Every \\Macro used in main.tex is defined in numbers.tex.
  2. numbers.tex is not stale — regenerating it from the data produces the
     same file.

This exists because the paper argues that a rule which lives only in prose is
a rule contingent on someone remembering it. A paper whose numbers are typed
by hand goes stale silently the moment the ledger grows by one day.
"""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "main.tex")
NUMS = os.path.join(HERE, "numbers.tex")

# Macros provided by LaTeX itself or defined inline in main.tex.
BUILTIN = re.compile(
    r"^(begin|end|documentclass|usepackage|title|author|date|maketitle|section|"
    r"subsection|paragraph|newcommand|input|texttt|textbf|emph|href|footnote|"
    r"item|toprule|midrule|bottomrule|centering|small|caption|label|ref|quad|"
    r"geq|leq|times|cdot|,|;|%|&|\\|_|\$|#|{|}|multicolumn|hline|noindent|"
    r"today|hspace|vspace|par|left|right|frac|mathrm|text|url|and|approx|"
    r"S|P|captionsetup|hidelinks|utf|T|a|newline|linewidth|textwidth|"
    r"modelA|modelB|em|it|bf|sl|tt|rm|sf|footnotesize|scriptsize|large|Large)$")


def fail(msg):
    print("FAIL: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    main_tex = open(MAIN, encoding="utf-8").read()
    if not os.path.exists(NUMS):
        fail("numbers.tex missing — run: python3 paper/compute_numbers.py --latex")
    nums_tex = open(NUMS, encoding="utf-8").read()
    defined = set(re.findall(r"\\newcommand\{\\(\w+)\}", nums_tex))
    defined |= set(re.findall(r"\\newcommand\{\\(\w+)\}", main_tex))

    used = {m for m in re.findall(r"\\([A-Za-z]+)", main_tex)
            if not BUILTIN.match(m)}
    missing = sorted(used - defined)
    if missing:
        fail("undefined macros in main.tex: " + ", ".join(missing))
    print(f"ok: {len(used & defined)} generated macros used, all defined")

    unused = sorted(defined - used - {"modelA", "modelB"})
    if unused:
        print(f"note: {len(unused)} generated macros unused "
              f"({', '.join(unused[:8])}{' ...' if len(unused) > 8 else ''})")

    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "numbers.tex")
        r = subprocess.run([sys.executable, os.path.join(HERE, "compute_numbers.py"),
                            "--latex", tmp], capture_output=True, text=True)
        if r.returncode:
            fail("compute_numbers.py failed:\n" + r.stderr)
        if open(tmp, encoding="utf-8").read() != nums_tex:
            fail("numbers.tex is STALE — the data moved but the manuscript did "
                 "not.\n      Run: python3 paper/compute_numbers.py --latex")
    print("ok: numbers.tex is current")


if __name__ == "__main__":
    main()
