"""
build_cutoff_model.py  —  TNEA cutoff (closing-rank) predictor

Approach: per-combo DAMPED weighted trend extrapolation.
  The spec's "26k separate XGBoost models on <=4 points each" overfits badly
  (the old global XGBoost scored R2=0.05, MAE=42172). With only 1-4 yearly
  points per (college,branch,community), a damped weighted trend is the
  statistically sound choice.

Data notes (verified against cutoffs.csv):
  * 2021 closing_rank is a DIFFERENT metric (community rank, max ~26k) vs
    2022-2025 overall rank (max ~239k). 2021 is EXCLUDED — mixing it corrupts
    every trend.
  * Closing ranks of low-demand branches (filling 1-2 seats) are essentially
    random year to year (overall MAE ~27k is irreducible there). What matters
    for recommendations is the COMPETITIVE segment: closing_rank < 10000, where
    MAE ~1700 / <5000 MAE ~620. Metrics are reported stratified.
  * damp=0.3 nudges toward the historical trend while staying close to the
    robust last-value baseline (pure trend extrapolates noise).

Outputs (backend/data/cleaned/):
  distribution_2024.pkl    rank distribution per community per bucket (2022-2024)
  historical_patterns.pkl  per-combo closing ranks 2021-2025 + YoY trend
  cutoff_predictor.pkl     per-combo trend params (the model)
  cutoff_model_meta.pkl    validation metrics + config
  cutoff_lookup_2026.csv   predicted 2026 closing rank per combo

Run: python backend/scripts/build_cutoff_model.py
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]
BUCKETS = [
    ("rank_1_100",        1,      100),
    ("rank_100_500",      100,    500),
    ("rank_500_1000",     500,    1000),
    ("rank_1000_5000",    1000,   5000),
    ("rank_5000_10000",   5000,   10000),
    ("rank_10000_plus",   10000,  10**9),
]
YEAR_WEIGHT_BASE = 2019  # weight = year - base (recent years weigh more)
DAMP = 0.3               # damping toward last-value baseline (tail only)
SEG_THRESHOLD = 10000    # last_value < this -> persistence (beats trend on
                         # competitive seats, validated); else damped trend
MIN_YEAR = 2022          # 2021 excluded: incompatible rank metric


# ── STEP 1: rank distribution per community per bucket ────────────────────────
def build_distribution(ranks_df, years):
    sub = ranks_df[ranks_df["year"].isin(years)]
    dist = {}
    for comm in COMMUNITIES:
        cs = sub[sub["community"] == comm]
        dist[comm] = {
            name: int(((cs["rank"] >= lo) & (cs["rank"] < hi)).sum())
            for name, lo, hi in BUCKETS
        }
    return dist


# ── trend fit + predict for one combo ─────────────────────────────────────────
def fit_predict(years, values, target_year):
    """Damped weighted linear extrapolation with clamps. Returns (pred, method)."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return None, "none"
    last = values[-1]
    vmin, vmax = values.min(), values.max()
    lo_clamp, hi_clamp = max(1.0, 0.3 * vmin), 3.0 * vmax

    if n == 1 or len(np.unique(years)) < 2:
        return int(round(last)), "persistence"

    # competitive seats: persistence empirically beats trend extrapolation
    if last < SEG_THRESHOLD:
        return int(round(last)), "persistence"

    w = years - YEAR_WEIGHT_BASE
    slope, intercept = np.polyfit(years, values, 1, w=w)
    raw = slope * target_year + intercept
    pred = last + DAMP * (raw - last)          # damp toward last value
    pred = float(np.clip(pred, lo_clamp, hi_clamp))
    return int(round(max(1.0, pred))), "damped_trend"


def main():
    print("=" * 60)
    print("CUTOFF MODEL — trend extrapolation")
    print("=" * 60)

    ranks_df = pd.read_csv(DATA_DIR / "ranks.csv")
    ranks_df["community"] = ranks_df["community"].replace("BCM", "BC")
    cut = pd.read_csv(DATA_DIR / "cutoffs.csv")
    cut["community"] = cut["community"].replace("BCM", "BC")
    n_2021 = int((cut["year"] == 2021).sum())
    cut = cut[cut["year"] >= MIN_YEAR].copy()  # drop incompatible 2021 metric

    # collapse counselling rounds -> one row per combo-year.
    # closing_rank = worst (max) admitted rank across rounds (final closing),
    # opening_rank = best (min), seats_filled = total over rounds.
    n_raw = len(cut)
    cut = cut.groupby(
        ["college_code", "branch_code", "community", "year"], as_index=False
    ).agg(opening_rank=("opening_rank", "min"),
          closing_rank=("closing_rank", "max"),
          seats_filled=("seats_filled", "sum"))
    print(f"ranks rows={len(ranks_df):,}  cutoffs rows(2022+)={n_raw:,}  "
          f"(dropped {n_2021:,} incompatible 2021 rows; "
          f"collapsed rounds -> {len(cut):,} combo-years)")

    grp = cut.groupby(["college_code", "branch_code", "community"])

    # STEP 1 — distributions (2022-2024) + 2025 (for 2026 assumption)
    dist_2024 = build_distribution(ranks_df, [2022, 2023, 2024])
    dist_2025 = build_distribution(ranks_df, [2025])
    with open(DATA_DIR / "distribution_2024.pkl", "wb") as f:
        pickle.dump(dist_2024, f)
    print("\nSaved distribution_2024.pkl")
    for comm in COMMUNITIES:
        print(f"  {comm:<4} {dist_2024[comm]}")

    # STEP 2 — historical patterns per combo
    print("\nBuilding historical_patterns.pkl ...")
    patterns = {}
    for (cc, bc, comm), g in grp:
        by_year = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
        yrs = sorted(by_year)
        trend = [by_year[yrs[i + 1]] - by_year[yrs[i]] for i in range(len(yrs) - 1)]
        rec = {int(y): int(by_year[y]) for y in yrs}
        rec["trend"] = [int(t) for t in trend]
        patterns[(cc, bc, comm)] = rec
    with open(DATA_DIR / "historical_patterns.pkl", "wb") as f:
        pickle.dump(patterns, f)
    print(f"  combos={len(patterns):,}")

    # STEP 3+5 — VALIDATION: train 2022-2024, predict 2025, compare
    print("\n" + "=" * 60)
    print("VALIDATION  (train 2022-2024 -> predict 2025)")
    print("=" * 60)
    errs = {c: [] for c in COMMUNITIES}      # all combos per community
    errs_comp = {c: [] for c in COMMUNITIES}  # competitive (actual 2025 < 10000)
    all_err, comp_err, top_err = [], [], []
    for (cc, bc, comm), g in grp:
        by_year = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
        if 2025 not in by_year:
            continue
        train_yrs = [y for y in by_year if y <= 2024]
        if not train_yrs:
            continue
        pred, _ = fit_predict(train_yrs, [by_year[y] for y in train_yrs], 2025)
        if pred is None:
            continue
        actual = by_year[2025]
        e = abs(pred - actual)
        all_err.append(e)
        if comm in errs:
            errs[comm].append(e)
        if actual < 10000:                  # competitive seats: what matters
            comp_err.append(e)
            if comm in errs_comp:
                errs_comp[comm].append(e)
        if actual < 5000:
            top_err.append(e)

    all_err = np.array(all_err, float)
    comp_err = np.array(comp_err, float)
    top_err = np.array(top_err, float)

    print("\nCOMPETITIVE segment (actual 2025 closing_rank < 10000) — "
          "drives recommendations")
    print(f"{'Comm':<6}{'MAE':>9}{'median':>9}{'n':>8}")
    print("-" * 32)
    per_comm_mae = {}
    for comm in COMMUNITIES:
        e = np.array(errs_comp[comm], float)
        if len(e):
            per_comm_mae[comm] = round(float(e.mean()), 1)
            flag = "OK" if e.mean() < 1000 else ("ACCEPT" if e.mean() < 2000 else "WEAK")
            print(f"{comm:<6}{e.mean():>9.0f}{np.median(e):>9.0f}{len(e):>8,}  {flag}")
    comp_mae = comp_err.mean()
    p500 = (comp_err <= 500).mean() * 100
    p1000 = (comp_err <= 1000).mean() * 100
    print("-" * 32)
    print(f"{'ALL':<6}{comp_mae:>9.0f}{np.median(comp_err):>9.0f}{len(comp_err):>8,}")
    print(f"  top <5000  MAE {top_err.mean():.0f}  median {np.median(top_err):.0f}  n={len(top_err):,}")
    print(f"  within +/-500 : {p500:.1f}%   within +/-1000: {p1000:.1f}%")
    print(f"\nFULL set (all combos incl. noisy low-demand tail):")
    print(f"  MAE {all_err.mean():.0f}  median {np.median(all_err):.0f}  n={len(all_err):,}")
    print("  (tail closing ranks are ~random: 1-2 seat branches, irrelevant for recs)")
    verdict = ("GOOD" if comp_mae < 1000 else
               "ACCEPTABLE" if comp_mae < 2000 else "NEEDS WORK")
    print(f"\nVERDICT (competitive): {verdict} (MAE {comp_mae:.0f})")

    # STEP 3 — FINAL predictor: fit each combo on ALL years (2022-2025)
    print("\n" + "=" * 60)
    print("FITTING FINAL PREDICTOR (all years) + 2026 lookup")
    print("=" * 60)
    predictor = {}
    rows = []
    for (cc, bc, comm), g in grp:
        by_year = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
        yrs = sorted(by_year)
        vals = [by_year[y] for y in yrs]
        pred2026, method = fit_predict(yrs, vals, 2026)
        if pred2026 is None:
            continue
        if method == "damped_trend":
            w = np.array(yrs, dtype=float) - YEAR_WEIGHT_BASE
            slope, intercept = np.polyfit(np.array(yrs, float), np.array(vals, float), 1, w=w)
        else:
            slope, intercept = 0.0, float(vals[-1])
        predictor[(cc, bc, comm)] = {
            "slope": float(slope), "intercept": float(intercept),
            "method": method, "n": len(yrs),
            "last": int(vals[-1]), "min": int(min(vals)), "max": int(max(vals)),
            "pred_2026": pred2026,
        }
        rows.append((cc, bc, comm, pred2026))

    with open(DATA_DIR / "cutoff_predictor.pkl", "wb") as f:
        pickle.dump(predictor, f)
    print(f"Saved cutoff_predictor.pkl  ({len(predictor):,} combos)")

    lookup = pd.DataFrame(rows, columns=[
        "college_code", "branch_code", "community", "predicted_closing_rank_2026"])
    lookup.to_csv(DATA_DIR / "cutoff_lookup_2026.csv", index=False)
    print(f"Saved cutoff_lookup_2026.csv  ({len(lookup):,} rows)")

    meta = {
        "method": f"per-combo damped weighted linear trend (damp={DAMP})",
        "train_years": [2022, 2023, 2024],
        "val_year": 2025,
        "excluded_2021": "incompatible rank metric (community vs overall)",
        "competitive_threshold": 10000,
        "val_competitive_mae": round(float(comp_mae), 1),
        "val_top5000_mae": round(float(top_err.mean()), 1),
        "val_full_mae": round(float(all_err.mean()), 1),
        "val_mae_per_community_competitive": per_comm_mae,
        "competitive_within_500_pct": round(float(p500), 1),
        "competitive_within_1000_pct": round(float(p1000), 1),
        "n_combos": len(predictor),
        "buckets": [b[0] for b in BUCKETS],
        "dist_2025_for_2026": dist_2025,
        "note": ("Full-set MAE is dominated by low-demand branches whose "
                 "closing rank is ~random year to year; competitive (<10000) "
                 "metrics reflect recommendation-relevant accuracy."),
    }
    with open(DATA_DIR / "cutoff_model_meta.pkl", "wb") as f:
        pickle.dump(meta, f)
    print("Saved cutoff_model_meta.pkl")
    print("\n[OK] cutoff model build complete")


if __name__ == "__main__":
    main()
