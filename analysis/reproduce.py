#!/usr/bin/env python3
"""Regenerates every number quoted in FINDINGS.md from data/ alone.

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


def binom_two_sided(k, n, p0):
    if not n:
        return None
    pmf = lambda i: math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i)
    obs = pmf(k)
    return round(min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-9))), 4)


def binom_one_sided(k, n, p0=0.5):
    if not n:
        return None
    return round(sum(math.comb(n, i) * p0 ** n for i in range(k, n + 1)), 4)


def h(t):
    print("\n" + t + "\n" + "-" * len(t))


def main():
    R = [r for r in load("resolutions.csv") if r["status"] == "resolved"]
    print(f"scored rows: {len(R)}")

    # --- 1. interval coverage ------------------------------------------
    h("1. Interval coverage (target 0.80)")
    ib = [r for r in R if r["in_band"] in ("0", "1")]
    k = sum(1 for r in ib if r["in_band"] == "1")
    print(f"  coverage = {k}/{len(ib)} = {k/len(ib):.3f}  CI95 {wilson(k, len(ib))}"
          f"  p(=0.80) = {binom_two_sided(k, len(ib), 0.80)}")

    # --- 2. baselines ---------------------------------------------------
    h("2. Baselines")
    for col, label in [("beat_naive", "naive"), ("beat_drift", "drift"),
                       ("beat_momentum", "momentum"), ("beat_all_three", "ALL THREE")]:
        v = [r for r in R if r[col] in ("True", "False")]
        if not v:
            continue
        kk = sum(1 for r in v if r[col] == "True")
        print(f"  {label:10s} {kk:3d}/{len(v):3d} = {kk/len(v):.3f}"
              f"  CI95 {wilson(kk, len(v))}  p(one-sided, >0.5) = {binom_one_sided(kk, len(v))}")

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
    print(f"  n = {len(llm)}   agent = {st.mean(llm):.4f}   climatology = {st.mean(clim):.4f}"
          f"   BSS = {1 - st.mean(llm)/st.mean(clim):+.3f}")
    print("  BSS < 0  =>  p_up loses to simply tracking the base rate.")

    # --- 5. does the point forecast reduce spread? ----------------------
    h("5. Does the point forecast reduce error spread? (1-day)")
    by = defaultdict(list)
    for r in R:
        if r["horizon"] == "1d" and num(r["actual_pct"]) is not None:
            by[r["asset_id"]].append(r)
    print(f"  {'id':4s} {'n':>3s} {'with forecast':>14s} {'mean only':>11s} {'gain':>8s}")
    for a in sorted(by):
        v = by[a]
        act = [num(r["actual_pct"]) for r in v]
        res = [num(r["signed_err"]) for r in v]
        s_pred = st.pstdev(res)
        m = st.mean(act)
        s_mean = st.pstdev([x - m for x in act])
        print(f"  {a:4s} {len(v):3d} {s_pred:13.3f}pp {s_mean:10.3f}pp {(1-s_pred/s_mean)*100:+7.1f}%")
    print("  Positive gain = the forecast helped. Five of six are <= 0.")

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
    print("  ~3 effectively independent observations per day (assets are correlated")
    print("  in blocks). Nominal n overstates statistical power accordingly.")


if __name__ == "__main__":
    main()
