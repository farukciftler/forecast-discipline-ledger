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
    r"rho|sum|sigma|mu|alpha|beta|delta|pm|neq|infty|log|exp|min|max|"
    r"cite|bibliographystyle|bibliography|emph|"
    r"modelA|modelB|em|it|bf|sl|tt|rm|sf|footnotesize|scriptsize|large|Large)$")


# Literals that are legitimately not data. Each needs a reason.
ALLOWED_LITERALS = {
    "0.80",   # the interval's nominal target, fixed by the protocol
    "0.5",    # the null of the one-sided sign test
    "95",     # "Wilson 95% CI" -- a convention, not a measurement
    "80",     # "80% intervals" in prose
    "10",     # exponent in "$10^{-8}$"-style prose, and "10 values"
    "1.0",    # the null probability quoted as a bound
    "75", "90",   # subscripts in "$p_{75}$ / $p_{90}$ / $p_{95}$" -- labels
    "30",     # the ">= 30 days" threshold, a definition not a measurement
    "4.0",    # "CC BY 4.0"
    "10.5281",  # the DOI prefix
    "1950", "1990", "2007", "2015", "2018", "2024",  # citation years in refs
    "2310.06770",  # arXiv id
    "256",   # 2^8 groupings, stated in prose as a combinatorial fact
}


# --- Prose tells -------------------------------------------------------------
# A paper whose thesis is "a rule that lives only in prose is contingent on
# someone remembering it" should not rely on remembering how to write. These
# are the machine-generated-prose markers that were actually present in the
# first draft, plus the standard vocabulary tells. The em-dash count is the
# load-bearing one: the draft had seventeen, roughly one per paragraph.
PROSE_TELLS = [
    (r"---", "em-dash: seventeen were removed from the first draft; use a "
             "comma, colon, semicolon, or two sentences"),
    (r"\b(?:comprehensive|robust|leverage|delve|nuanced|multifaceted|holistic"
     r"|underscore[sd]?|pivotal|realm|landscape|tapestry|paradigm|myriad"
     r"|seamless|cutting-edge|game-chang\w+)\b", "machine-generated vocabulary"),
    (r"\bIt is worth noting\b|\bIt should be noted\b|\bImportantly,",
     "filler opener"),
    (r"\b(?:Moreover|Furthermore|Additionally),", "connective filler; let the "
     "idea carry the transition"),
    (r"\bnot only .{2,60}? but also\b", "not-only-but-also construction"),
    (r"\bIn conclusion\b|\bIn summary\b", "generic closer"),
    (r"\bover a (?:year|decade)\b", "unverified time-span claim; every "
     "duration in this paper must come from a macro"),
]


def check_prose(body):
    hits = []
    for pat, why in PROSE_TELLS:
        found = set(m.group(0) for m in re.finditer(pat, body))
        if found:
            hits.append(f"{why}: {', '.join(sorted(found)[:4])}")
    return hits


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

    # A hand-typed figure need not be an undefined macro -- it can simply be a
    # bare literal, which the macro check cannot see. This was a real gap: the
    # table in section 5 carried "400 d" as plain text and passed. We now flag
    # decimal literals and multi-digit integers outside the preamble, table
    # rules and section numbering, and require each to be justified.
    body = main_tex.split("\\begin{document}", 1)[-1]
    body = re.sub(r"%.*", "", body)                       # comments
    body = re.sub(r"\\(?:label|ref|input|usepackage|documentclass)\{[^}]*\}", "", body)
    lits = set()
    for m in re.finditer(r"(?<![\\\w.])(\d+\.\d+|\d{2,})(?![\w.])", body):
        v = m.group(1)
        if v in ALLOWED_LITERALS:
            continue
        lits.add(v)
    if lits:
        fail("bare numeric literals in the body -- generate them instead: "
             + ", ".join(sorted(lits))
             + "\n      (if a literal is genuinely not data, add it to "
               "ALLOWED_LITERALS with a reason)")
    print("ok: no bare numeric literals in the body")

    tells = check_prose(body)
    if tells:
        fail("prose reads as machine-generated:\n      "
             + "\n      ".join(tells))
    print("ok: no machine-generated prose tells")

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
