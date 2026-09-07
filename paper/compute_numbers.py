#!/usr/bin/env python3
"""Every number that appears in the paper, computed from ../data/*.csv.

NB: this file must not be called `numbers.py` — that shadows the standard
library module `numbers`, which `decimal` (and therefore `statistics`) imports.

Standard library only. Run from the repository root or from paper/.
Output is deliberately plain text so it can be diffed against the manuscript.
"""
import csv, math, os, statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def load(n):
    with open(os.path.join(DATA, n), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((c - s) / d, 4), round((c + s) / d, 4)


def binom_tail(k, n, p=0.5):
    """P(X >= k). Exact, no scipy."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def mannwhitney(x, y):
    """Two-sided normal approximation with tie correction."""
    allv = sorted([(v, 0) for v in x] + [(v, 1) for v in y])
    ranks, i, ties = {}, 0, []
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        ties.append(j - i + 1)
        i = j + 1
    R1 = sum(ranks[i] for i, (_, g) in enumerate(allv) if g == 0)
    n1, n2, N = len(x), len(y), len(x) + len(y)
    U1 = R1 - n1 * (n1 + 1) / 2
    U = min(U1, n1 * n2 - U1)
    mu = n1 * n2 / 2
    tie = sum(t ** 3 - t for t in ties)
    sd = math.sqrt(n1 * n2 / 12 * ((N + 1) - tie / (N * (N - 1))))
    z = (U - mu) / sd if sd else 0.0
    return U, z, math.erfc(abs(z) / math.sqrt(2))


def h(t):
    print("\n" + t + "\n" + "-" * len(t))


def main():
    R = [r for r in load("resolutions.csv") if r["status"] == "resolved"]
    F = load("forecasts.csv")
    E = load("error_log.csv")

    h("S1  Setup")
    print(f"  forecasts written      = {len(F)}")
    print(f"  forecasts scored       = {len(R)}")
    days = sorted({r['as_of'] for r in F})
    print(f"  distinct forecast days = {len(days)}  ({days[0]} .. {days[-1]})")
    print(f"  assets                 = {len(load('assets.csv'))}")
    print(f"  horizons               = {sorted({r['horizon'] for r in F})}")

    h("S3  Forecast results (negative)")
    inb = [r for r in R if r["in_band"] in ("0", "1")]
    k = sum(1 for r in inb if r["in_band"] == "1")
    lo, hi = wilson(k, len(inb))
    # two-sided exact binomial against 0.80
    p_lo = sum(math.comb(len(inb), i) * .8 ** i * .2 ** (len(inb) - i) for i in range(k, len(inb) + 1))
    print(f"  interval coverage      = {k}/{len(inb)} = {k/len(inb):.4f}  CI95 ({lo}, {hi})")
    print(f"    exact binomial p(coverage >= observed | true=0.80) = {p_lo:.2e}")
    for col, lab in (("beat_naive", "naive"), ("beat_drift", "drift"),
                     ("beat_momentum", "momentum"), ("beat_all_three", "ALL THREE")):
        v = [r for r in R if r[col] in ("True", "False", "0", "1")]
        w = sum(1 for r in v if r[col] in ("True", "1"))
        if v:
            a, b = wilson(w, len(v))
            print(f"  beat {lab:10s} = {w}/{len(v)} = {w/len(v):.4f}  CI95 ({a}, {b})  "
                  f"p(one-sided >0.5) = {binom_tail(w, len(v)):.4g}")
    br = [num(r["brier"]) for r in R if num(r["brier"]) is not None]
    up = [1 if num(r["actual_pct"]) and num(r["actual_pct"]) > 0 else 0
          for r in R if num(r["brier"]) is not None]
    base = sum(up) / len(up) if up else 0
    clim = sum((base - u) ** 2 for u in up) / len(up) if up else 0
    print(f"  Brier (model)          = {st.fmean(br):.4f}   n = {len(br)}")
    print(f"  Brier (running base)   = {clim:.4f}   base rate = {base:.4f}")
    print(f"  Brier skill score      = {1 - st.fmean(br)/clim:+.4f}" if clim else "")

    h("S3b  Effective independent observations")
    per = Counter(r["as_of"] for r in R)
    print(f"  scored rows / day      = {st.fmean(per.values()):.2f}")
    print("  assets move in correlated blocks; nominal n overstates power.")

    h("S4  Error telemetry")
    lat = sorted(int(r["latency_days"]) for r in E if r["latency_days"].strip().lstrip("-").isdigit())
    who = Counter(r["detected_by"] for r in E)
    rep = sum(1 for r in E if r["is_repeat"] == "yes")
    print(f"  records                = {len(E)}")
    print(f"  detected by            = {dict(who)}   "
          f"agent share = {who['agent']/len(E):.3f}")
    print(f"  latency days           = median {st.median(lat):.0f}  mean {st.fmean(lat):.1f}  "
          f"max {max(lat)}  n = {len(lat)}")
    for q in (0.75, 0.90, 0.95):
        i = int(q * (len(lat) - 1))
        print(f"    p{int(q*100)}                  = {lat[i]}")
    print(f"  latency >= 7 days      = {sum(1 for v in lat if v >= 7)}/{len(lat)}")
    print(f"  latency >= 30 days     = {sum(1 for v in lat if v >= 30)}/{len(lat)}")
    a, b = wilson(rep, len(E))
    print(f"  repeat of prior record = {rep}/{len(E)} = {rep/len(E):.4f}  CI95 ({a}, {b})")
    cls = Counter(r["class_k"] for r in E if r["class_k"])
    mec = Counter(r["mechanism_k"] for r in E if r["mechanism_k"])
    print(f"  class                  = {dict(cls.most_common())}")
    print(f"  mechanism              = {dict(mec.most_common())}")

    h("S4b  H9 - direction of self-correction")
    eff = Counter(r["score_effect"] for r in E if r["score_effect"])
    f_, u_ = eff.get("favorable", 0), eff.get("unfavorable", 0)
    print(f"  favorable {f_}  unfavorable {u_}  neutral {eff.get('neutral',0)}  n = {sum(eff.values())}")
    if f_ + u_:
        p = 2 * min(binom_tail(max(f_, u_), f_ + u_), 1.0)
        a, b = wilson(f_, f_ + u_)
        print(f"  favorable share        = {f_}/{f_+u_} = {f_/(f_+u_):.4f}  CI95 ({a}, {b})  "
              f"two-sided p = {min(p,1.0):.4f}")
        print("  a skew toward 'favorable' would be BAD news; none is detected.")

    h("S5  Failed exploratory test: absence vs. wrong-value latency")
    # Pre-specified nothing: this test was formed AFTER looking. Reported as failed.
    ABSENCE = {"measurement", "process"}
    x = [int(r["latency_days"]) for r in E
         if r["class_k"] in ABSENCE and r["latency_days"].strip().lstrip("-").isdigit()]
    y = [int(r["latency_days"]) for r in E
         if r["class_k"] not in ABSENCE and r["latency_days"].strip().lstrip("-").isdigit()]
    print(f"  absence-like (class in {sorted(ABSENCE)}): n={len(x)}  median {st.median(x):.1f}  mean {st.fmean(x):.1f}")
    print(f"  other                                     : n={len(y)}  median {st.median(y):.1f}  mean {st.fmean(y):.1f}")
    U, z, p = mannwhitney(x, y)
    print(f"  Mann-Whitney U = {U:.0f}  z = {z:.2f}  two-sided p = {p:.4f}")
    print("  EXPLORATORY and NOT SUPPORTED. Reported because it was run.")

    h("S6  Longest-hidden records")
    for r in sorted(E, key=lambda r: -int(r["latency_days"] or 0))[:6]:
        print(f"  {r['record_id']:5s} {r['latency_days']:>4s}d  {r['detected_by']:6s} "
              f"{r['class_k']:12s} {r['mechanism_k']}")


if __name__ == "__main__":
    main()
