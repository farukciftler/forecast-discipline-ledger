#!/usr/bin/env python3
"""Every number that appears in the paper, computed from ../data/*.csv.

NB: this file must not be called `numbers.py` -- that shadows the standard
library module `numbers`, which `decimal` (and therefore `statistics`) imports.

Standard library only. Run from the repository root or from paper/.
Output is deliberately plain text so it can be diffed against the manuscript.

Pools follow PREREGISTRATION.md, not convenience:

  * rows from different protocol versions are never pooled (pooling rule 1);
  * one-month outputs are projections and enter no skill claim (H5/H6);
  * unresolved rows and flagged substitutions enter no test (rules 2 and 3).

The PRIMARY pool is therefore: resolved, not a flagged substitution, forecast
horizons only (1d, 1w), latest protocol version. An earlier draft pooled
everything and quoted the result as the headline. That contradicted the
pre-registration the same draft cited, and nobody noticed because the script
and the document were never checked against each other.
"""
import argparse, csv, math, os, statistics as st
from collections import Counter, defaultdict

# Every value the manuscript quotes is registered here as it is computed, then
# emitted as LaTeX macros. The manuscript must never contain a literal number
# that came from the data: that is the failure mode this paper is about.
MACROS = {}

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}


def reg(name, value, fmt="{}"):
    """Record a value for \\newcommand emission and return it unchanged."""
    assert name.isalpha(), f"macro names are letters only: {name}"
    MACROS[name] = fmt.format(value)
    return value


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


def log_pmf(i, n, p):
    """log P(X = i), X ~ Bin(n, p). Log-space: math.comb overflows a float
    once n passes about a thousand, and the pool is now larger than that."""
    return (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + i * math.log(p) + (n - i) * math.log(1 - p))


def binom_tail(k, n, p=0.5):
    """P(X >= k). Exact up to floating point, no scipy."""
    if n == 0:
        return 1.0
    return min(1.0, sum(math.exp(log_pmf(i, n, p)) for i in range(k, n + 1)))


def binom_two_sided(k, n, p):
    """Exact two-sided binomial: total mass of outcomes no likelier than k."""
    if n == 0:
        return 1.0
    obs = log_pmf(k, n, p)
    return min(1.0, sum(math.exp(lp) for lp in
                        (log_pmf(i, n, p) for i in range(n + 1))
                        if lp <= obs + 1e-9))


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


def spearman(x, y):
    """Spearman rank correlation with average ranks for ties."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk, i = [0.0] * len(v), 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return rk
    rx, ry = rank(x), rank(y)
    mx, my = st.fmean(rx), st.fmean(ry)
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else 0.0


def h(t):
    print("\n" + t + "\n" + "-" * len(t))


def sci(x, digits=1):
    """LaTeX scientific notation, e.g. 2.4\\times10^{-4}."""
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    return f"{m:.{digits}f}\\times10^{{{e}}}"


def fmt_p(p):
    """A p-value as the manuscript prints it."""
    return sci(p) if p < 0.001 else f"{p:.3f}"


def is_beat(r, col):
    return r[col] in ("True", "1")


def has_beat(r, col):
    return r[col] in ("True", "False", "0", "1")


def beat_all(rows):
    v = [r for r in rows if has_beat(r, "beat_all_three")]
    return sum(1 for r in v if is_beat(r, "beat_all_three")), len(v)


def coverage(rows):
    v = [r for r in rows if r["in_band"] in ("0", "1")]
    return sum(1 for r in v if r["in_band"] == "1"), len(v)


def ratio(k, n):
    return (f"{k}/{n}", f"{k / n:.3f}") if n else ("n/a", "n/a")


def main():
    RES = load("resolutions.csv")
    F = load("forecasts.csv")
    E = load("error_log.csv")
    W = load("study_window.csv")[0]

    # Same exclusion as analysis/reproduce.py and analysis/check_docs.py. The
    # three scripts have disagreed before; keeping one definition is cheaper
    # than finding out again.
    R = [r for r in RES
         if r["status"] == "resolved" and r.get("dirty_substitution") != "yes"]
    latest = max(r["protocol_version"] for r in R if r["protocol_version"])
    FC = [r for r in R if r["horizon_kind"] == "forecast"]
    P = [r for r in FC if r["protocol_version"] == latest]

    h("S1  Study window and pools")
    days = sorted({r["as_of"] for r in F})
    reg("WindowStart", W["window_start"]); reg("WindowEnd", W["window_end"])
    reg("WindowCalDays", W["calendar_days"]); reg("OpenDays", W["market_open_days"])
    reg("OpenCovered", W["open_days_with_forecast"])
    reg("OpenMissed", W["open_days_missed"])
    reg("MissRunMax", W["longest_missed_run"])
    reg("MissRunEnd", W["missed_run_at_window_end"])
    reg("ClosedCovered", W["closed_days_with_forecast"])
    reg("NumDays", len(days)); reg("FirstDay", days[0]); reg("LastDay", days[-1])
    reg("NumWritten", len(F))
    reg("NumAssets", len(load("assets.csv")))
    reg("NumForecastAssets", len({r["asset_id"] for r in F}))
    reg("NumModels", len({r["model_id"] for r in F if r["model_id"]}))
    reg("NumProtocols", len({r["protocol_version"] for r in R if r["protocol_version"]}))
    reg("LatestProtocol", latest)
    reg("NumResolved", sum(1 for r in RES if r["status"] == "resolved"))
    reg("NumDirty", sum(1 for r in RES if r["status"] == "resolved"
                        and r.get("dirty_substitution") == "yes"))
    reg("NumScoredAll", len(R))
    reg("NumNotScored", len(F) - len(R))
    reg("NumProjection", len(R) - len(FC))
    reg("NumEarlierProto", len(FC) - len(P))
    reg("PrimaryN", len(P))
    reg("PrimaryDays", len({r["as_of"] for r in P}))
    print(f"  window                 = {W['window_start']} .. {W['window_end']} "
          f"({W['calendar_days']} calendar days)")
    print(f"  market-open days       = {W['market_open_days']}, covered "
          f"{W['open_days_with_forecast']}, missed {W['open_days_missed']} "
          f"(longest run {W['longest_missed_run']}, at window end "
          f"{W['missed_run_at_window_end']})")
    print(f"  forecast days          = {len(days)}  ({days[0]} .. {days[-1]})")
    print(f"  forecasts written      = {len(F)}")
    print(f"  resolved / flagged     = {MACROS['NumResolved']} / {MACROS['NumDirty']}")
    print(f"  scored (all pools)     = {len(R)}  = projections {len(R) - len(FC)}"
          f" + earlier protocols {len(FC) - len(P)} + PRIMARY {len(P)}")
    print(f"  primary pool           = protocol v{latest}, horizons 1d+1w, "
          f"{MACROS['PrimaryDays']} forecast days")

    h("S2  H2 - interval coverage (primary pool)")
    k, n = coverage(P)
    lo, hi = wilson(k, n)
    p2 = binom_two_sided(k, n, 0.80)
    reg("CovK", k); reg("CovN", n); reg("CovRate", k / n, "{:.3f}")
    reg("CovLo", lo, "{:.3f}"); reg("CovHi", hi, "{:.3f}")
    reg("CovP", fmt_p(p2))
    print(f"  coverage               = {k}/{n} = {k/n:.4f}  CI95 ({lo}, {hi})")
    print(f"    exact two-sided binomial vs 0.80: p = {p2:.3g}")

    # H14-d: the managed-crawl asset is reported separately as well as inside
    # the headline. An interval that is never breached carries no information.
    fx = {a["asset_id"] for a in load("assets.csv") if a["asset_class"] == "fx_deposit"}
    kx, nx = coverage([r for r in P if r["asset_id"] not in fx])
    kf, nf = coverage([r for r in P if r["asset_id"] in fx])
    reg("CovExFxK", kx); reg("CovExFxN", nx); reg("CovExFxRate", kx / nx, "{:.3f}")
    reg("CovFxK", kf); reg("CovFxN", nf)
    print(f"    excluding the managed-crawl asset: {kx}/{nx} = {kx/nx:.4f};"
          f" that asset alone: {kf}/{nf}")

    h("S2b  H14 - shadow interval on matched 1-day rows (never scored)")
    fshadow = {(r["as_of"], r["asset_id"], r["horizon"]):
               (num(r["band_shadow_low"]), num(r["band_shadow_high"])) for r in F
               if num(r["band_shadow_low"]) is not None}
    m = [(r, fshadow[(r["as_of"], r["asset_id"], r["horizon"])]) for r in P
         if r["horizon"] == "1d" and r["in_band"] in ("0", "1")
         and (r["as_of"], r["asset_id"], r["horizon"]) in fshadow
         and num(r["actual_pct"]) is not None]
    sh_in = sum(1 for r, (lo_, hi_) in m if lo_ <= num(r["actual_pct"]) <= hi_)
    st_in = sum(1 for r, _ in m if r["in_band"] == "1")
    wr_ = st.fmean((hi_ - lo_) / (num(r["high_pct"]) - num(r["low_pct"]))
                   for r, (lo_, hi_) in m if num(r["high_pct"]) > num(r["low_pct"]))
    reg("ShadowN", len(m)); reg("ShadowCov", sh_in / len(m), "{:.3f}")
    reg("ShadowStandingCov", st_in / len(m), "{:.3f}")
    reg("ShadowWidthRatio", wr_, "{:.2f}")
    print(f"  matched rows           = {len(m)}")
    print(f"  shadow / standing      = {sh_in/len(m):.4f} / {st_in/len(m):.4f}"
          f"   mean width ratio {wr_:.3f}")
    # H14-b, second condition: has a second volatility regime been observed?
    a1 = [num(r["return_pct"]) for r in load("returns.csv")
          if r["asset_id"] == "A1" and num(r["return_pct"]) is not None]
    gvz = [num(r["value"]) for r in load("market_state.csv") if r["variable"] == "gvz"]
    reg("AoneMinRet", min(a1), "{:.2f}")
    reg("GvzAboveThirty", sum(1 for v in gvz if v is not None and v > 30))
    reg("GvzDays", len(gvz))
    print(f"  A1 worst daily return  = {min(a1):.2f}%   implied-vol index > 30 on "
          f"{MACROS['GvzAboveThirty']} of {len(gvz)} recorded days")

    h("S3  H1 - baselines (primary pool), by row and by forecast day")
    for col, tag in (("beat_naive", "Naive"), ("beat_drift", "Drift"),
                     ("beat_momentum", "Mom"), ("beat_all_three", "All")):
        v = [r for r in P if has_beat(r, col)]
        w = sum(1 for r in v if is_beat(r, col))
        a, b = wilson(w, len(v))
        pv = binom_tail(w, len(v))
        reg(f"Beat{tag}K", w); reg(f"Beat{tag}N", len(v))
        reg(f"Beat{tag}Rate", w / len(v), "{:.3f}")
        reg(f"Beat{tag}P", fmt_p(pv))
        if tag == "All":
            reg("BeatAllLo", a, "{:.3f}"); reg("BeatAllHi", b, "{:.3f}")
        # Rows written on the same day are not independent (pooling rule 5).
        # The day-level sign test gives each forecast day one vote: the day is
        # won if more than half of its rows beat the baseline. Ties dropped.
        per = defaultdict(list)
        for r in v:
            per[r["as_of"]].append(is_beat(r, col))
        won = sum(1 for x in per.values() if sum(x) * 2 > len(x))
        lost = sum(1 for x in per.values() if sum(x) * 2 < len(x))
        pd = binom_tail(won, won + lost)
        reg(f"Day{tag}Won", won); reg(f"Day{tag}N", won + lost)
        reg(f"Day{tag}P", fmt_p(pd))
        print(f"  beat {tag:5s} rows {w}/{len(v)} = {w/len(v):.4f}  CI95 ({a}, {b})"
              f"  p = {pv:.3g}   | days {won}/{won + lost}  p = {pd:.3g}")

    h("S3b  H3 - the one pre-registered subgroup (confidence medium/high)")
    H3 = [r for r in P if r["confidence"] in ("medium", "high")]
    k3, n3 = beat_all(H3)
    reg("HThreeN", n3); reg("HThreeK", k3)
    reg("HThreeRate", (k3 / n3) if n3 else 0, "{:.3f}")
    print(f"  n = {n3}  beat all three = {k3}  (minimum n is 100)")

    h("S3c  H13-c - up-move probability (primary pool)")
    br = [num(r["brier"]) for r in P if num(r["brier"]) is not None]
    up = [1 if (num(r["actual_pct"]) or 0) > 0 else 0
          for r in P if num(r["brier"]) is not None]
    base = sum(up) / len(up)
    clim = sum((base - u) ** 2 for u in up) / len(up)
    reg("BrierModel", st.fmean(br), "{:.4f}"); reg("BrierN", len(br))
    reg("BrierBase", clim, "{:.4f}"); reg("BaseRate", base, "{:.2f}")
    reg("BSS", 1 - st.fmean(br) / clim, "{:+.3f}")
    # WALK-FORWARD climatology, matching analysis/reproduce.py: at each row the
    # base rate uses only rows already resolved. The figure above uses the
    # full-sample rate, which is a look-ahead and therefore a harder baseline.
    # Both are reported; choosing the friendlier one would be a correction in
    # the agent's own favour.
    rows = sorted([r for r in P if num(r["brier"]) is not None
                   and r["direction_hit"] in ("0", "1")],
                  key=lambda r: r["target_date"])
    llm, cw, ups, seen = [], [], 0, 0
    for r in rows:
        out = 1 if r["direction_hit"] == "1" and num(r["p_up"]) >= 0.5 else (
            0 if r["direction_hit"] == "1" else (1 if num(r["p_up"]) < 0.5 else 0))
        cw.append(((ups / seen if seen else 0.5) - out) ** 2)
        llm.append((num(r["p_up"]) - out) ** 2)
        ups += out
        seen += 1
    reg("BSSWalk", 1 - st.fmean(llm) / st.fmean(cw), "{:+.3f}")
    print(f"  Brier (agent)          = {st.fmean(br):.4f}   n = {len(br)}")
    print(f"  Brier (full-sample)    = {clim:.4f}   base rate = {base:.4f}")
    print(f"  BSS full-sample        = {1 - st.fmean(br)/clim:+.4f}")
    print(f"  BSS walk-forward       = {1 - st.fmean(llm)/st.fmean(cw):+.4f}")
    # EXPLORATORY decomposition, reported because the pooled score is positive
    # and the reason is visible in the data: one asset moves in one direction
    # by policy, so knowing WHICH asset a row belongs to already beats a pooled
    # base rate. Against each asset's own base rate that information is gone.
    Pb = [r for r in P if num(r["brier"]) is not None]
    outc = lambda r: 1 if (num(r["actual_pct"]) or 0) > 0 else 0
    fxr = [r for r in Pb if r["asset_id"] in fx]
    reg("FxN", len(fxr)); reg("FxUp", sum(outc(r) for r in fxr))
    reg("FxMeanPup", st.fmean(num(r["p_up"]) for r in fxr), "{:.2f}")
    rest = [r for r in Pb if r["asset_id"] not in fx]
    b0 = st.fmean(outc(r) for r in rest)
    reg("BSSExFx", 1 - st.fmean(num(r["brier"]) for r in rest)
        / st.fmean((b0 - outc(r)) ** 2 for r in rest), "{:+.3f}")
    reg("BaseRateExFx", b0, "{:.2f}")
    by = defaultdict(list)
    for r in Pb:
        by[r["asset_id"]].append(r)
    agent = sum(num(r["brier"]) for r in Pb)
    own = sum((st.fmean(outc(x) for x in v) - outc(r)) ** 2
              for v in by.values() for r in v)
    reg("BSSOwnBase", 1 - agent / own, "{:+.3f}")
    # Uncertainty on both skill scores, resampling whole forecast days (rows
    # of one day are not independent). Fixed seed so numbers.tex stays
    # byte-stable. Descriptive, not a pre-registered test.
    import random
    day_rows = defaultdict(list)
    for r in Pb:
        day_rows[r["as_of"]].append((num(r["brier"]), outc(r), r["asset_id"]))
    keys = sorted(day_rows)
    rng = random.Random(20260801)
    b_pool, b_own = [], []
    for _ in range(2000):
        rows_b = [x for k in (rng.choice(keys) for _ in keys) for x in day_rows[k]]
        ag_ = st.fmean(x[0] for x in rows_b)
        base_b = st.fmean(x[1] for x in rows_b)
        cl_ = st.fmean((base_b - x[1]) ** 2 for x in rows_b)
        grp = defaultdict(list)
        for x in rows_b:
            grp[x[2]].append(x[1])
        own_ = sum((st.fmean(v) - o) ** 2 for v in grp.values() for o in v) / len(rows_b)
        if cl_ and own_:
            b_pool.append(1 - ag_ / cl_); b_own.append(1 - ag_ / own_)
    b_pool.sort(); b_own.sort()
    lo_i, hi_i = int(0.025 * len(b_pool)), int(0.975 * len(b_pool)) - 1
    reg("BSSLo", b_pool[lo_i], "{:+.3f}"); reg("BSSHi", b_pool[hi_i], "{:+.3f}")
    reg("BSSOwnLo", b_own[lo_i], "{:+.3f}"); reg("BSSOwnHi", b_own[hi_i], "{:+.3f}")
    print(f"  day-block bootstrap CI95: pooled ({b_pool[lo_i]:+.3f}, {b_pool[hi_i]:+.3f})"
          f"   own-base ({b_own[lo_i]:+.3f}, {b_own[hi_i]:+.3f})   reps {len(b_pool)}")
    print(f"  managed-crawl asset    = up on {MACROS['FxUp']} of {len(fxr)} scored rows, "
          f"mean p_up {MACROS['FxMeanPup']}")
    print(f"  BSS excluding it       = {MACROS['BSSExFx']}  (base rate {b0:.3f})")
    print(f"  BSS vs own base rates  = {MACROS['BSSOwnBase']}")

    h("S3d  Breakdowns that are reported, not pooled")
    print("  by protocol version (forecast horizons, scored rows):")
    for v in sorted({r["protocol_version"] for r in FC if r["protocol_version"]}):
        sub = [r for r in FC if r["protocol_version"] == v]
        ka, na = beat_all(sub); kc, nc = coverage(sub)
        t = WORD[int(v)]
        reg(f"Proto{t}N", len(sub))
        reg(f"Proto{t}BeatAll", ratio(ka, na)[0]); reg(f"Proto{t}BeatAllRate", ratio(ka, na)[1])
        reg(f"Proto{t}Cov", ratio(kc, nc)[1])
        print(f"    v{v}: n={len(sub):4d}  beat all {ratio(ka, na)}  coverage {ratio(kc, nc)[1]}")
    print("  by model version (all forecasts written; scored rows in primary pool):")
    for m in sorted({r["model_id"] for r in F if r["model_id"]}):
        t = m.split("_")[-1]                      # model_A -> A
        wr_ = [r for r in F if r["model_id"] == m]
        sub = [r for r in P if r["model_id"] == m]
        ka, na = beat_all(sub); kc, nc = coverage(sub)
        reg(f"Model{t}Written", len(wr_))
        reg(f"Model{t}Days", len({r["as_of"] for r in wr_}))
        reg(f"Model{t}Scored", len(sub))
        reg(f"Model{t}BeatAll", ratio(ka, na)[0]); reg(f"Model{t}BeatAllRate", ratio(ka, na)[1])
        reg(f"Model{t}Cov", ratio(kc, nc)[1])
        print(f"    {m}: written {len(wr_):4d} on {MACROS[f'Model{t}Days']:>2s} days, "
              f"primary rows {len(sub):4d}  beat all {ratio(ka, na)}  "
              f"coverage {ratio(kc, nc)[1]}")

    h("S4  Error telemetry")
    lat = sorted(int(r["latency_days"]) for r in E
                 if r["latency_days"].strip().lstrip("-").isdigit())
    who = Counter(r["detected_by"] for r in E)
    rep = sum(1 for r in E if r["is_repeat"] == "yes")
    reg("ErrN", len(E)); reg("ErrAgent", who["agent"]); reg("ErrHuman", who["human"])
    reg("ErrAgentShare", who["agent"] / len(E), "{:.3f}")
    reg("LatMedian", st.median(lat), "{:.0f}"); reg("LatMean", st.fmean(lat), "{:.1f}")
    reg("LatMax", max(lat))
    print(f"  records                = {len(E)}")
    print(f"  detected by            = {dict(who)}   "
          f"agent share = {who['agent']/len(E):.3f}")
    print(f"  latency days           = median {st.median(lat):.0f}  mean {st.fmean(lat):.1f}  "
          f"max {max(lat)}  n = {len(lat)}")
    for q in (0.75, 0.90, 0.95):
        i = int(q * (len(lat) - 1))
        reg({75: "LatPseventyfive", 90: "LatPninety",
             95: "LatPninetyfive"}[int(q * 100)], lat[i])
        print(f"    p{int(q*100)}                  = {lat[i]}")
    reg("LatGeSeven", sum(1 for v in lat if v >= 7))
    reg("LatGeThirty", sum(1 for v in lat if v >= 30))
    print(f"  latency >= 7 days      = {MACROS['LatGeSeven']}/{len(lat)}")
    print(f"  latency >= 30 days     = {MACROS['LatGeThirty']}/{len(lat)}")
    a, b = wilson(rep, len(E))
    reg("RepK", rep); reg("RepRate", rep / len(E), "{:.3f}")
    reg("RepLo", a, "{:.3f}"); reg("RepHi", b, "{:.3f}")
    print(f"  repeat of prior record = {rep}/{len(E)} = {rep/len(E):.4f}  CI95 ({a}, {b})")
    cls = Counter(r["class_k"] for r in E if r["class_k"])
    mec = Counter(r["mechanism_k"] for r in E if r["mechanism_k"])
    print(f"  class                  = {dict(cls.most_common())}")
    print(f"  mechanism              = {dict(mec.most_common())}")

    h("S4a  H7 - does detection latency fall over time?")
    seq = [int(r["latency_days"]) for r in E
           if r["latency_days"].strip().lstrip("-").isdigit()]
    rho_s = spearman(list(range(len(seq))), seq)
    t_s = rho_s * math.sqrt((len(seq) - 2) / (1 - rho_s ** 2))
    # one-sided, pre-registered direction: rho < 0. Normal approximation to t.
    p_s = 0.5 * math.erfc(-t_s / math.sqrt(2))
    reg("SpearRho", rho_s, "{:+.2f}"); reg("SpearN", len(seq)); reg("SpearP", fmt_p(p_s))
    print(f"  Spearman rho = {rho_s:+.3f}  n = {len(seq)}  one-sided p(rho<0) = {p_s:.3f}"
          f"   (minimum n is 120)")

    h("S4b  H9 - direction of self-correction")
    eff = Counter(r["score_effect"] for r in E if r["score_effect"])
    f_, u_ = eff.get("favorable", 0), eff.get("unfavorable", 0)
    reg("EffFav", f_); reg("EffUnfav", u_); reg("EffNeutral", eff.get("neutral", 0))
    p = min(1.0, 2 * binom_tail(max(f_, u_), f_ + u_))
    a, b = wilson(f_, f_ + u_)
    reg("EffN", f_ + u_); reg("EffFavShare", f_ / (f_ + u_), "{:.3f}")
    reg("EffLo", a, "{:.3f}"); reg("EffHi", b, "{:.3f}")
    reg("EffP", fmt_p(p))
    print(f"  favorable {f_}  unfavorable {u_}  neutral {eff.get('neutral', 0)}")
    print(f"  favorable share        = {f_}/{f_+u_} = {f_/(f_+u_):.4f}  CI95 ({a}, {b})  "
          f"two-sided p = {p:.4f}   (minimum n is 40)")

    h("S5  Exploratory: absence-like classes vs. the rest (NOT a test)")
    ABSENCE = {"measurement", "process"}
    x = [int(r["latency_days"]) for r in E
         if r["class_k"] in ABSENCE and r["latency_days"].strip().lstrip("-").isdigit()]
    y = [int(r["latency_days"]) for r in E
         if r["class_k"] not in ABSENCE and r["latency_days"].strip().lstrip("-").isdigit()]
    U, z, p = mannwhitney(x, y)
    reg("AbsN", len(x)); reg("AbsMedian", st.median(x), "{:.1f}")
    reg("AbsMean", st.fmean(x), "{:.1f}")
    reg("OthN", len(y)); reg("OthMedian", st.median(y), "{:.1f}")
    reg("OthMean", st.fmean(y), "{:.1f}")
    reg("MWZ", z, "{:.2f}"); reg("MWP", fmt_p(p))
    print(f"  absence-like n={len(x)}  median {st.median(x):.1f}  mean {st.fmean(x):.1f}")
    print(f"  other        n={len(y)}  median {st.median(y):.1f}  mean {st.fmean(y):.1f}")
    print(f"  Mann-Whitney z = {z:.2f}  two-sided p = {p:.4f}")

    h("S5b  Figures quoted in the mechanism section")
    by_id = {r["record_id"]: r for r in E}

    def rid(r):
        try:
            return int(r["record_id"].lstrip("Kk"))
        except ValueError:
            return None
    # Per-record latencies are their OWN macros. They were once written as
    # \LatMax because the record happened to hold the maximum at the time; when
    # its stored value was corrected the macro silently began pointing at a
    # different record, and the manuscript claimed a latency the record never
    # had. A derived aggregate is not a substitute for a specific value.
    # Which record holds the maximum latency, and when its error began. Emitted
    # as values so that the claim moves with the data instead of the prose.
    top = max(E, key=lambda r: int(r["latency_days"] or 0))
    reg("LatMaxRecord", top["record_id"]); reg("LatMaxEvent", top["event_date"])
    reg("LatMaxClass", top["class_k"])
    second = sorted(E, key=lambda r: -int(r["latency_days"] or 0))[1]
    reg("LatSecondRecord", second["record_id"]); reg("LatSecond", second["latency_days"])
    reg("LatSecondClass", second["class_k"])
    print(f"  longest-hidden         = {top['record_id']} ({top['class_k']}, "
          f"{top['latency_days']}d), then {second['record_id']} ({second['class_k']}, "
          f"{second['latency_days']}d)")
    for rec, name in (("K93", "KNineThreeLat"), ("K91", "KNineOneLat"),
                      ("K118", "KOneOneEightLat")):
        if rec in by_id:
            print(f"  {rec} latency            = {reg(name, by_id[rec]['latency_days'])}")
    # The skipped-day chain: walk `prior_record` back from the last process
    # record that the routine itself surfaced, for as long as the link stays
    # inside the same class and mechanism. The chain is in the data; the
    # manuscript quotes its length and endpoints instead of typing them.
    last = next(r for r in reversed(E) if r["class_k"] == "process"
                and r["mechanism_k"] == "routine_flow" and r["is_repeat"] == "yes")
    chain = [last]
    while True:
        prev = by_id.get(chain[-1]["prior_record"])
        if (not prev or prev["class_k"] != "process"
                or prev["mechanism_k"] != "routine_flow"):
            break
        chain.append(prev)
    reg("SkipChainN", len(chain))
    reg("SkipChainFirst", chain[-1]["record_id"])
    reg("SkipChainLast", chain[0]["record_id"])
    reg("SkipChainAgent", sum(1 for r in chain if r["detected_by"] == "agent"))
    reg("SkipChainLatMax", max(int(r["latency_days"]) for r in chain))
    print(f"  skipped-day chain      = {len(chain)} records, "
          f"{chain[-1]['record_id']} .. {chain[0]['record_id']}, "
          f"agent-detected {MACROS['SkipChainAgent']}, max latency "
          f"{MACROS['SkipChainLatMax']}")
    FREEZE = 78   # the record at which the controlled vocabulary was fixed
    conf = [r for r in E if (rid(r) or 0) >= FREEZE]
    print(f"  confirmatory pool (K{FREEZE}+) = {reg('ConfirmN', len(conf))}")
    print(f"  records before freeze  = {reg('VocabFreezeN', len(E) - len(conf))}")

    ret = defaultdict(dict)
    for r in load("returns.csv"):
        v = num(r["return_pct"])
        if v is not None:
            ret[r["date"]][r["asset_id"]] = v

    def rho(a, b):
        d = sorted(k for k, v in ret.items() if a in v and b in v)
        if len(d) < 5:
            return None
        x = [ret[k][a] for k in d]; y = [ret[k][b] for k in d]
        mx, my = st.fmean(x), st.fmean(y)
        den = math.sqrt(sum((p - mx) ** 2 for p in x) * sum((q - my) ** 2 for q in y))
        return sum((p - mx) * (q - my) for p, q in zip(x, y)) / den if den else None

    reg("CorrAtwoAthree", rho("A2", "A3"), "{:.2f}")
    print(f"  corr(A2, A3)           = {MACROS['CorrAtwoAthree']}")
    # Effective independent series per day, Kish-style: k^2 / sum(rho_ij),
    # over the assets that are actually forecast.
    ids = sorted({r["asset_id"] for r in F})
    tot = 0.0
    for i in ids:
        for j in ids:
            c = 1.0 if i == j else rho(i, j)
            if c is not None:
                tot += c
    reg("NEff", len(ids) ** 2 / tot, "{:.1f}")
    print(f"  n_eff (k={len(ids)}, rho sum {tot:.2f}) = {MACROS['NEff']}")

    appendix(RES, F, E)

    h("S6  Longest-hidden records")
    for r in sorted(E, key=lambda r: -int(r["latency_days"] or 0))[:6]:
        print(f"  {r['record_id']:5s} {r['latency_days']:>4s}d  {r['detected_by']:6s} "
              f"{r['class_k']:12s} {r['mechanism_k']}")


# Meanings are copied from CODEBOOK.md; the asserts below fail if the
# vocabulary in the data and the vocabulary described here ever part ways.
CLASS_MEANING = {
    "measurement": "a scored observation was computed wrongly, or should not have counted",
    "model": "a wrong assumption about how an asset behaves",
    "data": "a source failed, returned a stale value, or was read without its date",
    "process": "a required step of the daily routine was skipped",
    "engine": "the deterministic ledger code behaved wrongly",
    "verification": "a checking step failed or was skipped",
    "institution": "a wrong assumption about how a product settles or pays",
    "accounting": "double counting or mis-attribution between holdings",
}
MECHANISM_MEANING = {
    "routine_flow": "the ordinary daily sequence surfaced it, without anyone looking for it",
    "cross_check": "two sources of the same quantity disagreed",
    "reasoning": "the agent noticed it while thinking about something else",
    "human": "the operator noticed it",
    "custodian_statement": "an external account statement contradicted the ledger",
    "reconciliation": "a total was matched against an independent total",
    "next_day_observation": "the following day's data made it visible",
    "preregistered_test": "a test written in advance failed",
    "engine_warning": "the deterministic code refused or warned",
    "adversarial_review": "a scheduled review pass looking specifically for it",
}


def appendix(RES, F, E):
    """Counts, tables and integrity checks for the dataset appendix.

    Every claim in the appendix's validation section is RUN here. The
    manuscript prints the outcome; a check that fails prints a non-zero count
    and the text says so, because nothing here assumes a check passes.
    """
    import datetime
    h("S7  Dataset appendix: counts")
    A = load("assets.csv"); RT = load("returns.csv"); MS = load("market_state.csv")
    X = load("exposure.csv"); DC = load("decisions.csv"); W = load("study_window.csv")[0]
    tt = lambda x: "\\texttt{%s}" % x.replace("_", "\\_")
    files = [("assets.csv", len(A), "one row per asset: pseudonym, asset class, generic description"),
             ("study_window.csv", 1, "the window and how many of its days the routine covered"),
             ("forecasts.csv", len(F), "one row per forecast, as sealed"),
             ("resolutions.csv", len(RES), "outcome, scores and baseline predictions for each forecast whose target date fell in the window"),
             ("error_log.csv", len(E), "one row per operational error"),
             ("returns.csv", len(RT), "daily percentage return per asset"),
             ("market_state.csv", len(MS), "public market variables on each forecast day, long format"),
             ("exposure.csv", len(X), "portfolio exposure by underlying asset class, in per cent"),
             ("decisions.csv", len(DC), "recorded allocation decisions and the alternatives considered, as weights")]
    reg("TabFiles", " ".join(f"{tt(a)} & {n} & {d} \\\\" for a, n, d in files))
    cls = Counter(r["class_k"] for r in E)
    mec = Counter(r["mechanism_k"] for r in E)
    assert set(cls) == set(CLASS_MEANING), set(cls) ^ set(CLASS_MEANING)
    assert set(mec) == set(MECHANISM_MEANING), set(mec) ^ set(MECHANISM_MEANING)
    reg("TabClasses", " ".join(f"{tt(k)} & {CLASS_MEANING[k]} & {v} \\\\" for k, v in cls.most_common()))
    reg("TabMechanisms", " ".join(f"{tt(k)} & {MECHANISM_MEANING[k]} & {v} \\\\"
                                  for k, v in mec.most_common()))
    reg("NumFiles", len(files))
    reg("NumResolutionRows", len(RES)); reg("NumReturnRows", len(RT)); reg("NumMarketRows", len(MS))
    reg("NumExposureRows", len(X)); reg("NumDecisionRows", len(DC))
    reg("NumDecisions", len({r["decision_id"] for r in DC}))
    hz = Counter(r["horizon"] for r in F)
    reg("NumOneDay", hz["1d"]); reg("NumOneWeek", hz["1w"]); reg("NumOneMonth", hz["1m"])
    reg("NumShadowRows", sum(1 for r in F if r["band_shadow_low"]))
    reg("NumMechanical", sum(1 for r in F if r["is_mechanical"] == "1"))
    reg("NumForecastCols", len(F[0])); reg("NumResolutionCols", len(RES[0])); reg("NumErrorCols", len(E[0]))
    st_ = Counter(r["status"] for r in RES)
    reg("NumNoData", st_["no_data"]); reg("NumNoBase", st_["no_base_price"])
    reg("ErrLinked", sum(1 for r in E if r["prior_record"]))
    lat = [int(r["latency_days"]) for r in E]
    reg("LatMin", min(lat))
    reg("ErrFirst", E[0]["record_id"]); reg("ErrLast", E[-1]["record_id"])
    reg("ErrFirstDate", min(r["logged_date"] for r in E)); reg("ErrLastDate", max(r["logged_date"] for r in E))
    reg("NumClasses", len(cls)); reg("NumMechanisms", len(mec))
    reg("EffBlank", sum(1 for r in E if not r["score_effect"]))
    reg("NumVars", len({r["variable"] for r in MS})); reg("NumMarketDays", len({r["date"] for r in MS}))
    reg("NumExpClasses", len({r["exposure_class"] for r in X})); reg("NumExpDays", len({r["date"] for r in X}))
    reg("NumStale", sum(1 for r in RT if r["stale_flag"] == "1"))
    print(f"  {len(files)} files; forecasts {len(F)}, resolutions {len(RES)}, errors {len(E)}")

    h("S7b  Dataset appendix: integrity checks (each prints its exception count)")
    fk = [(r["as_of"], r["asset_id"], r["horizon"]) for r in F]
    rk = [(r["as_of"], r["asset_id"], r["horizon"]) for r in RES]
    res = [r for r in RES if r["status"] == "resolved"]
    inb = [r for r in res if r["in_band"] in ("0", "1")]
    four = ("beat_naive", "beat_drift", "beat_momentum", "beat_all_three")
    ba = [r for r in res if all(r[c] in ("True", "False") for c in four)]
    bn = [r for r in res if r["beat_naive"] in ("True", "False") and num(r["baseline_naive_pct"]) is not None]
    ag = lambda r: abs(num(r["point_pct"]) - num(r["actual_pct"]))
    nv = lambda r: abs(num(r["baseline_naive_pct"]) - num(r["actual_pct"]))
    d = datetime.date.fromisoformat
    pos = {r["record_id"]: i for i, r in enumerate(E)}
    lk = [r for r in E if r["prior_record"]]
    dated = [r.get("as_of") or r.get("logged_date") or r.get("date")
             for rows in (F, RES, E, RT, MS, X) for r in rows]
    wsum = Counter()
    for r in X:
        wsum[r["date"]] += num(r["weight_pct"])
    checks = [
        ("VDupForecastKeys", len(fk) - len(set(fk))),
        ("VDupResolutionKeys", len(rk) - len(set(rk))),
        ("VOrphanResolutions", len(set(rk) - set(fk))),
        ("VUnresolvedForecasts", len(set(fk) - set(rk))),
        ("VPointOutsideBand", sum(1 for r in F if not num(r["low_pct"]) <= num(r["point_pct"]) <= num(r["high_pct"]))),
        ("VProbOutOfRange", sum(1 for r in F if not 0 <= num(r["p_up"]) <= 1)),
        ("VTargetBeforeAsOf", sum(1 for r in F if r["target_date"] <= r["as_of"])),
        ("VBandChecked", len(inb)),
        ("VBandMismatch", sum(1 for r in inb if (num(r["low_pct"]) <= num(r["actual_pct"]) <= num(r["high_pct"]))
                              != (r["in_band"] == "1"))),
        ("VErrMismatch", sum(1 for r in res if num(r["abs_err"]) is not None
                             and abs(ag(r) - num(r["abs_err"])) > 1e-3)),
        ("VBeatChecked", len(ba)),
        ("VBeatMismatch", sum(1 for r in ba if (r["beat_all_three"] == "True")
                              != all(r[c] == "True" for c in four[:3]))),
        ("VNaiveChecked", len(bn)),
        ("VNaiveMismatch", sum(1 for r in bn if (ag(r) < nv(r)) != (r["beat_naive"] == "True"))),
        ("VNaiveTies", sum(1 for r in bn if abs(ag(r) - nv(r)) < 1e-9)),
        ("VUnflaggedNonResolved", sum(1 for r in RES if r["status"] != "resolved"
                                      and num(r["actual_pct"]) is not None)),
        ("VLatencyMismatch", sum(1 for r in E if (d(r["logged_date"]) - d(r["event_date"])).days
                                 != int(r["latency_days"]))),
        ("VPriorMissing", sum(1 for r in lk if r["prior_record"] not in pos)),
        ("VPriorNotEarlier", sum(1 for r in lk if r["prior_record"] in pos
                                 and pos[r["prior_record"]] >= pos[r["record_id"]])),
        ("VRepeatWithoutLink", sum(1 for r in E if r["is_repeat"] == "yes" and not r["prior_record"])),
        ("VLinkWithoutRepeat", sum(1 for r in E if r["is_repeat"] != "yes" and r["prior_record"])),
        ("VOutsideWindow", sum(1 for x in dated if not W["window_start"] <= x <= W["window_end"])),
        ("VTargetOutsideWindow", sum(1 for r in RES if r["target_date"] > W["window_end"])),
        ("VExposureNotHundred", sum(1 for v in wsum.values() if abs(v - 100) > 0.5)),
    ]
    for name, value in checks:
        reg(name, value)
        print(f"  {name:24s} {value}")
    reg("VRepeatWithoutLinkId", ", ".join(r["record_id"] for r in E
                                          if r["is_repeat"] == "yes" and not r["prior_record"]))


def emit_latex(path):
    """Write \\newcommand definitions consumed by main.tex."""
    lines = ["% GENERATED FILE - DO NOT EDIT.",
             "% Produced by paper/compute_numbers.py from data/*.csv.",
             "% Any manuscript number that is typed by hand is a bug.",
             "% The data is a frozen release, so this file is deterministic:",
             "% regenerating it on any day must reproduce it byte for byte.",
             ""]
    # No date in the stamp. The release is frozen; a stamp that changed with
    # the calendar made the staleness check fail on every day but the one the
    # file was generated on.
    lines.append("\\newcommand{\\NumbersStamp}{%d values, window %s to %s}"
                 % (len(MACROS), MACROS["WindowStart"], MACROS["WindowEnd"]))
    lines.append("")
    for k in sorted(MACROS):
        lines.append("\\newcommand{\\%s}{%s}" % (k, MACROS[k]))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(MACROS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--latex", metavar="PATH", nargs="?", const="numbers.tex",
                    help="also write LaTeX macro definitions (default numbers.tex)")
    args = ap.parse_args()
    main()
    if args.latex:
        out = args.latex if os.path.isabs(args.latex) else os.path.join(HERE, args.latex)
        n = emit_latex(out)
        print(f"\n[latex] {n} macros -> {out}")
