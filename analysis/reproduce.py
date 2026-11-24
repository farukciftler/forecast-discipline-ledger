#!/usr/bin/env python3
"""Regenerates every number quoted in FINDINGS.md from data/ alone.

The release is a FROZEN study window (see data/study_window.csv). Pools follow
PREREGISTRATION.md: rows from different protocol versions are never pooled and
one-month projections enter no skill claim, so every forecast figure below is
computed on the PRIMARY pool: resolved, not a flagged substitution, 1-day and
1-week horizons, latest protocol version.

Standard library only. Run from the research-paper/ directory:

    python3 analysis/reproduce.py

If a figure in the prose disagrees with this script's output, the script is
right and the prose is stale.
"""
import csv, math, os, statistics as st
from collections import defaultdict

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p, d = k / n, 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((c - s) / d, 3), round((c + s) / d, 3)


def log_pmf(i, n, p0):
    # Log-space. math.comb overflows a float once n passes about a thousand.
    return (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + i * math.log(p0) + (n - i) * math.log(1 - p0))


def binom_two_sided(k, n, p0):
    if not n:
        return None
    obs = log_pmf(k, n, p0)
    return min(1.0, sum(math.exp(lp) for lp in
                        (log_pmf(i, n, p0) for i in range(n + 1))
                        if lp <= obs + 1e-9))


def binom_one_sided(k, n, p0=0.5):
    if not n:
        return None
    return min(1.0, sum(math.exp(log_pmf(i, n, p0)) for i in range(k, n + 1)))


def spearman(x, y):
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
    mx, my = st.mean(rx), st.mean(ry)
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else 0.0


def h(t):
    print("\n" + t + "\n" + "-" * len(t))


def main():
    # K113: rows whose target day was an open market day but whose snapshot was
    # never taken were resolved against a LATER day's price. What they measure
    # is no longer a one-day change, so they are excluded from every figure
    # here, exactly as they are in the source ledger's calibration. They stay
    # in the CSV, flagged, because deleting a row is not the same as declining
    # to score it.
    W = load("study_window.csv")[0]
    F = load("forecasts.csv")
    ALL = [r for r in load("resolutions.csv")
           if r["status"] == "resolved" and r.get("dirty_substitution") != "yes"]
    latest = max(r["protocol_version"] for r in ALL if r["protocol_version"])
    FC = [r for r in ALL if r["horizon_kind"] == "forecast"]
    R = [r for r in FC if r["protocol_version"] == latest]
    h("0. Study window and pools")
    print(f"  window {W['window_start']} .. {W['window_end']}  "
          f"({W['calendar_days']} calendar days)")
    print(f"  market-open days {W['market_open_days']}: routine ran on "
          f"{W['open_days_with_forecast']}, missed {W['open_days_missed']} "
          f"(longest run {W['longest_missed_run']}, at window end "
          f"{W['missed_run_at_window_end']}); ran on "
          f"{W['closed_days_with_forecast']} closed days")
    print(f"  forecast days {len({r['as_of'] for r in F})}, forecasts written {len(F)}")
    print(f"  scored rows {len(ALL)} = projections {len(ALL) - len(FC)} + earlier "
          f"protocols {len(FC) - len(R)} + primary {len(R)}")
    print(f"primary pool: {len(R)} scored forecasts "
          f"(protocol v{latest}, 1d + 1w, {len({r['as_of'] for r in R})} forecast days)")

    # --- 1. interval coverage ------------------------------------------
    h("1. Interval coverage (target 0.80)")
    ib = [r for r in R if r["in_band"] in ("0", "1")]
    k = sum(1 for r in ib if r["in_band"] == "1")
    print(f"  coverage = {k}/{len(ib)} = {k/len(ib):.3f}  CI95 {wilson(k, len(ib))}"
          f"  p(=0.80) = {binom_two_sided(k, len(ib), 0.80):.2g}")
    fx = {a["asset_id"] for a in load("assets.csv") if a["asset_class"] == "fx_deposit"}
    nf = [r for r in ib if r["asset_id"] not in fx]
    kn = sum(1 for r in nf if r["in_band"] == "1")
    print(f"  excluding the managed-rate asset: {kn}/{len(nf)} = {kn/len(nf):.3f}")
    # Shadow interval (PREREGISTRATION H14): written beside 1-day forecasts,
    # never scored. Compared on matched rows only.
    sh = {(r["as_of"], r["asset_id"], r["horizon"]):
          (num(r["band_shadow_low"]), num(r["band_shadow_high"]))
          for r in F if num(r["band_shadow_low"]) is not None}
    m = [(r, sh[(r["as_of"], r["asset_id"], r["horizon"])]) for r in ib
         if r["horizon"] == "1d" and (r["as_of"], r["asset_id"], r["horizon"]) in sh
         and num(r["actual_pct"]) is not None]
    s_in = sum(1 for r, (lo, hi) in m if lo <= num(r["actual_pct"]) <= hi)
    t_in = sum(1 for r, _ in m if r["in_band"] == "1")
    print(f"  shadow interval, {len(m)} matched 1-day rows: shadow "
          f"{s_in/len(m):.3f}  standing {t_in/len(m):.3f}")

    # --- 2. baselines ---------------------------------------------------
    h("2. Baselines")
    for col, label in [("beat_naive", "naive"), ("beat_drift", "drift"),
                       ("beat_momentum", "momentum"), ("beat_all_three", "ALL THREE")]:
        v = [r for r in R if r[col] in ("True", "False")]
        if not v:
            continue
        kk = sum(1 for r in v if r[col] == "True")
        per = defaultdict(list)
        for r in v:
            per[r["as_of"]].append(r[col] == "True")
        won = sum(1 for x in per.values() if sum(x) * 2 > len(x))
        lost = sum(1 for x in per.values() if sum(x) * 2 < len(x))
        print(f"  {label:10s} {kk:3d}/{len(v):3d} = {kk/len(v):.3f}"
              f"  CI95 {wilson(kk, len(v))}  p = {binom_one_sided(kk, len(v)):.2g}"
              f"   | days won {won}/{won + lost}  p = {binom_one_sided(won, won + lost):.2g}")
    h3 = [r for r in R if r["confidence"] in ("medium", "high")
          and r["beat_all_three"] in ("True", "False")]
    print(f"  H3 subgroup (confidence medium/high): n = {len(h3)}, beat all three "
          f"{sum(1 for r in h3 if r['beat_all_three'] == 'True')}  (minimum n 100)")

    # --- 3. directional accuracy (diagnostic) ---------------------------
    h("3. Directional accuracy (DIAGNOSTIC, not a headline)")
    dh = [r for r in R if r["direction_hit"] in ("0", "1")]
    kd = sum(1 for r in dh if r["direction_hit"] == "1")
    print(f"  {kd}/{len(dh)} = {kd/len(dh):.3f}  CI95 {wilson(kd, len(dh))}")

    # --- 4. Brier vs climatology ----------------------------------------
    h("4. Brier score vs running climatology")
    rows = sorted([r for r in R if num(r["brier"]) is not None and r["direction_hit"] in ("0", "1")],
                  key=lambda r: r["target_date"])
    llm, clim, ups, n = [], [], 0, 0
    for r in rows:
        outcome = 1 if r["direction_hit"] == "1" and num(r["p_up"]) >= 0.5 else (
            0 if r["direction_hit"] == "1" else (1 if num(r["p_up"]) < 0.5 else 0))
        base = ups / n if n else 0.5
        clim.append((base - outcome) ** 2)
        llm.append((num(r["p_up"]) - outcome) ** 2)
        ups += outcome
        n += 1
    bss = 1 - st.mean(llm) / st.mean(clim)
    print(f"  n = {len(llm)}   agent = {st.mean(llm):.4f}   climatology = {st.mean(clim):.4f}"
          f"   BSS = {bss:+.3f}")
    # The verdict is COMPUTED, not typed. It used to be a fixed string reading
    # "BSS < 0 => p_up loses"; the sign later flipped and the line kept saying
    # the opposite of what the number above it showed.
    print("  BSS < 0  =>  p_up loses to simply tracking the base rate."
          if bss < 0 else
          "  BSS > 0  =>  p_up edges out the running base rate, by a small margin.")
    # Why a positive score is not read as skill: one asset moves in one
    # direction by policy. Exploratory, not pre-registered.
    up = lambda r: 1 if (num(r["actual_pct"]) or 0) > 0 else 0
    pb = [r for r in R if num(r["brier"]) is not None]
    fxr = [r for r in pb if r["asset_id"] in fx]
    rest = [r for r in pb if r["asset_id"] not in fx]
    b_all = st.mean(up(r) for r in pb)
    print(f"  full-sample base rate {b_all:.3f}: BSS = "
          f"{1 - st.mean(num(r['brier']) for r in pb) / st.mean((b_all - up(r)) ** 2 for r in pb):+.3f}")
    print(f"  managed-rate asset rose on {sum(up(r) for r in fxr)} of {len(fxr)} scored rows")
    b0 = st.mean(up(r) for r in rest)
    print(f"  excluding it: BSS = "
          f"{1 - st.mean(num(r['brier']) for r in rest) / st.mean((b0 - up(r)) ** 2 for r in rest):+.3f}")
    grp = defaultdict(list)
    for r in pb:
        grp[r["asset_id"]].append(r)
    own = sum((st.mean(up(x) for x in v) - up(r)) ** 2 for v in grp.values() for r in v)
    print(f"  against each asset's own base rate: BSS = "
          f"{1 - sum(num(r['brier']) for r in pb) / own:+.3f}")
    # NOTE: this climatology is WALK-FORWARD (base rate from rows seen so far).
    # paper/compute_numbers.py uses the FULL-SAMPLE base rate, which is a
    # look-ahead baseline and therefore a harder one. The two BSS figures are
    # not interchangeable; see FINDINGS.md.

    # --- 5. does the point forecast reduce spread? ----------------------
    h("5. Does the point forecast reduce error spread? (1-day)")
    by = defaultdict(list)
    for r in R:
        if r["horizon"] == "1d" and num(r["actual_pct"]) is not None:
            by[r["asset_id"]].append(r)
    print(f"  {'id':4s} {'n':>3s} {'with forecast':>14s} {'mean only':>11s} {'gain':>8s}")
    gains = []
    for a in sorted(by):
        v = by[a]
        act = [num(r["actual_pct"]) for r in v]
        res = [num(r["signed_err"]) for r in v]
        s_pred = st.pstdev(res)
        m = st.mean(act)
        s_mean = st.pstdev([x - m for x in act])
        g = (1 - s_pred / s_mean) * 100
        gains.append(g)
        print(f"  {a:4s} {len(v):3d} {s_pred:13.3f}pp {s_mean:10.3f}pp {g:+7.1f}%")
    # COUNTED, not typed. This line was a fixed "Five of six are <= 0" and
    # stayed frozen while the underlying tally changed with the data.
    neg = sum(1 for g in gains if g <= 0)
    print(f"  Positive gain = the forecast helped. {neg} of {len(gains)} are <= 0.")

    # --- 6. error log ----------------------------------------------------
    h("6. Error log")
    E = load("error_log.csv")
    lat = [int(r["latency_days"]) for r in E if r["latency_days"].strip().lstrip("-").isdigit()]
    lat.sort()
    who = defaultdict(int)
    for r in E:
        who[r["detected_by"]] += 1
    rep = sum(1 for r in E if r["is_repeat"] == "yes")
    print(f"  records = {len(E)}")
    print(f"  detection latency (days): median {lat[len(lat)//2]}  mean {st.mean(lat):.1f}  max {max(lat)}")
    print(f"  detected by: {dict(who)}")
    print(f"  repeats of a prior record: {rep}/{len(E)} = {rep/len(E):.3f}  CI95 {wilson(rep, len(E))}")
    seq = [int(r["latency_days"]) for r in E if r["latency_days"].strip().lstrip("-").isdigit()]
    print(f"  H7 Spearman(record order, latency) = {spearman(list(range(len(seq))), seq):+.3f}"
          f"  n = {len(seq)}  (predicted negative; minimum n 120)")
    # Controlled vocabulary only. The free-text `class` / `subclass` columns
    # are NOT published: they were the reason the controlled columns exist
    # (75 records produced 36 distinct free-text classes and no test could be
    # run on them). Qualitative depth lives in CASES.md instead.
    for col, ad in (("class_k", "class"), ("mechanism_k", "detection mechanism")):
        c = defaultdict(int)
        for r in E:
            if r.get(col):
                c[r[col]] += 1
        print(f"  {ad}: " + ", ".join(f"{k}={v}" for k, v in
                                      sorted(c.items(), key=lambda kv: -kv[1])))
    eff = defaultdict(int)
    for r in E:
        if r.get("score_effect"):
            eff[r["score_effect"]] += 1
    n_eff = sum(eff.values())
    if n_eff:
        fav, unf = eff.get("favorable", 0), eff.get("unfavorable", 0)
        print(f"  self-correction direction (H9): favorable {fav}, unfavorable {unf}, "
              f"neutral {eff.get('neutral', 0)}  (n={n_eff})")
        print(f"    a significant skew toward 'favorable' would be BAD news: it would "
              f"mean\n    corrections are chosen after seeing which way they cut.")

    # --- 7. regime check -------------------------------------------------
    h("7. Regime check (sample vs. long-run volatility)")
    ret = defaultdict(list)
    for r in load("returns.csv"):
        v = num(r["return_pct"])
        if v is not None:
            ret[r["asset_id"]].append(v)
    print(f"  {'id':4s} {'n':>3s} {'sample std':>11s}")
    for a in sorted(ret):
        print(f"  {a:4s} {len(ret[a]):3d} {st.pstdev(ret[a]):10.3f}pp")
    print("  Long-run (250d) comparison requires the source price series and is")
    print("  reported in FINDINGS.md; only percentage returns are published here.")

    h("Note")
    print("  ~3 effectively independent series (assets are correlated in blocks).")
    print("  Nominal n overstates statistical power; prefer the day-level tests.")


if __name__ == "__main__":
    main()
