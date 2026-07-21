"""
validate_seat_adjustment_full.py — full-dataset sanity check for the seat-matrix
post-hoc adjustment layer (seat_adjustment.py + predict_colleges.py _load()).

Diagnostic only — reads the same enriched lookup ml_service.py serves from,
independently re-derives each pipeline stage (exclude / impute / drop
zero-seat) from the raw source files to cross-check the real output, flags
anomalies across the WHOLE dataset (not a hand-picked sample), and reports
in detail on the imputed (brand-new 2026 offering) and dropped (absent from
2026 matrix) combos. Does not change any prediction logic.

Run: python backend/validate_seat_adjustment_full.py
Writes: backend/data/validation/seat_adjustment_full_report.txt (mirrors stdout)
"""

import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "utils"))

from predict_colleges import _load, _match_confidence, _status  # noqa: E402
import seat_adjustment as sa  # noqa: E402

DATA_DIR = BASE_DIR / "data" / "cleaned"
OUT_DIR = BASE_DIR / "data" / "validation"
OUT_PATH = OUT_DIR / "seat_adjustment_full_report.txt"

RNG_SEED = 42
TEST_RANK = 20000        # fixed test student, used to derive a probability
TEST_RANK_CONF = 70      # for every combo so the whole dataset is comparable

_LOG = []


def out(line=""):
    print(line)
    _LOG.append(str(line))


def safe_num(x):
    """NaN/inf -> None, same pattern ml_service._json_safe uses."""
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, (np.floating,)) and (np.isnan(x) or np.isinf(x)):
        return None
    return x


def fmt(x, nd=2):
    x = safe_num(x)
    return "N/A" if x is None else (f"{x:,.{nd}f}" if isinstance(x, float) else f"{x:,}")


def probability_for(closing_rank):
    closing_rank = safe_num(closing_rank)
    if closing_rank is None:
        return None
    margin = closing_rank - TEST_RANK
    status = _status(margin)
    return _match_confidence(TEST_RANK_CONF, status, margin, closing_rank)


def section(title):
    out()
    out("=" * 100)
    out(title)
    out("=" * 100)


def main():
    random.seed(RNG_SEED)

    section("STAGE-BY-STAGE INDEPENDENT RE-DERIVATION (cross-check against actual _load() output)")

    raw_lookup = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv")
    raw_lookup["community"] = raw_lookup["community"].replace("BCM", "BC")
    raw_lookup["college_code"] = raw_lookup["college_code"].astype(int)
    raw_lookup["branch_code"] = raw_lookup["branch_code"].astype(str)
    N0 = len(raw_lookup)

    sa_cache = sa._load()
    combos_2026 = sa_cache["combos_2026"]

    combo_key = list(zip(raw_lookup["college_code"], raw_lookup["branch_code"]))
    keep_mask = [k in combos_2026 for k in combo_key]
    kept = raw_lookup[keep_mask].copy()
    dropped = raw_lookup[[not m for m in keep_mask]].copy()
    N1 = len(kept)
    dropped_combos = sorted(set(zip(dropped["college_code"], dropped["branch_code"])))

    existing_combos = set(zip(kept["college_code"], kept["branch_code"]))
    missing_combos = combos_2026 - existing_combos

    # zero-seat rows that SHOULD be dropped from `kept` before the pipeline
    # finishes (community has 0 seats in the 2026 matrix for that combo)
    kept["seats_2026_check"] = [
        sa_cache["seats_2026"].get((r.college_code, r.branch_code, r.community), 0)
        for r in kept.itertuples()
    ]
    zero_seat_should_drop = kept[kept["seats_2026_check"] == 0]

    # the REAL pipeline output, as ml_service.py actually uses it
    lk, colleges, branches = _load()
    N_final = len(lk)

    imputed_rows = lk[lk["imputed_base"]]
    imputed_combos_actual = set(zip(imputed_rows["college_code"], imputed_rows["branch_code"]))
    combos_lost_entirely = missing_combos - imputed_combos_actual  # in matrix, in cutoff_lookup gap,
                                                                    # but produced ZERO imputed rows

    out(f"raw cutoff_lookup_2026.csv rows (community-level):        {N0:>7,}")
    out(f"rows kept after 2026-seat-matrix combo exclusion:          {N1:>7,}  "
        f"({N0 - N1:,} rows dropped, {len(dropped_combos):,} distinct combos)")
    out(f"combos in 2026 matrix with NO cutoff_lookup row at all:    {len(missing_combos):>7,}")
    out(f"  -> of those, combos that got >=1 imputed row:            {len(imputed_combos_actual):>7,}")
    out(f"  -> of those, combos that produced ZERO imputed rows:     {len(combos_lost_entirely):>7,}  "
        f"(no branch-code match anywhere else in lookup for fallback)")
    out(f"imputed rows added (seats_2026 > 0 only):                  {len(imputed_rows):>7,}")
    out(f"rows with 0 2026-seats that must be dropped pre-final:     {len(zero_seat_should_drop):>7,}")
    out(f"FINAL row count from real _load() pipeline:                {N_final:>7,}")
    expected_final = N1 - len(zero_seat_should_drop) + len(imputed_rows)
    out(f"independently re-derived expected final count:             {expected_final:>7,}  "
        f"{'MATCH' if expected_final == N_final else '*** MISMATCH ***'}")

    if combos_lost_entirely:
        out("\ncombos in 2026 matrix, absent from cutoff_lookup, that produced NO imputed row at all:")
        for ccode, bcode in sorted(combos_lost_entirely)[:15]:
            cname = colleges.get(ccode, {}).get("college_name_full", f"College {ccode}")
            bname = branches.get(bcode, f"Branch {bcode}")
            out(f"  college={ccode:<6} branch={bcode:<4} {cname[:55]:<55} {bname}")

    # ------------------------------------------------------------------ #
    section("ANOMALY CHECKS ACROSS ALL COMBOS (full dataset, not a sample)")

    # 1. predicted_closing_rank_2026 <= 0 or non-numeric
    rank_col = lk["predicted_closing_rank_2026"]
    non_numeric = (~rank_col.apply(lambda v: isinstance(v, (int, np.integer)) and not pd.isna(v)))
    non_positive = rank_col <= 0
    bad_rank_mask = non_numeric | non_positive
    out(f"[1] predicted_closing_rank_2026 <= 0 or non-numeric:  {bad_rank_mask.sum():>5} / {N_final}")
    if bad_rank_mask.any():
        out(lk[bad_rank_mask].head(10).to_string())

    # 2. probability outside 0-100
    lk["prob_new"] = lk["predicted_closing_rank_2026"].apply(probability_for)
    out_of_range = lk["prob_new"].apply(lambda p: p is not None and not (0 <= p <= 100))
    out(f"[2] match_confidence outside 0-100 range:              {out_of_range.sum():>5} / {N_final}  "
        f"(formula floors at 5 / caps at 95 by construction, so this should always be 0)")
    if out_of_range.any():
        out(lk[out_of_range].head(10).to_string())

    # 3. seat_adjustment_factor at clip boundaries
    capped_mask = (lk["seat_adjustment_factor"] == sa.FACTOR_MIN) | (lk["seat_adjustment_factor"] == sa.FACTOR_MAX)
    out(f"[3] seat_adjustment_factor hit the clip boundary "
        f"({sa.FACTOR_MIN}/{sa.FACTOR_MAX}):  {capped_mask.sum():>5} / {N_final}")

    def raw_ratio(row):
        h = row["historical_avg_seats"]
        s = row["seats_2026"]
        if pd.isna(h) or h <= 0:
            return np.nan
        return s / h

    lk["raw_ratio"] = lk.apply(raw_ratio, axis=1)
    capped = lk[capped_mask].copy()
    capped["overshoot"] = capped.apply(
        lambda r: (r["raw_ratio"] - sa.FACTOR_MAX) if r["seat_adjustment_factor"] == sa.FACTOR_MAX
        else (sa.FACTOR_MIN - r["raw_ratio"]) if not pd.isna(r["raw_ratio"]) else np.nan,
        axis=1)
    capped = capped[~capped["overshoot"].isna()].sort_values("overshoot", ascending=False)
    out("\ntop 15 by how far the raw (unclamped) ratio overshot the cap:")
    out(f"{'college':>8} {'branch':>7} {'comm':>5} {'seats_2026':>10} {'hist_avg':>10} "
        f"{'raw_ratio':>10} {'clamped_to':>11} {'overshoot':>10}")
    for r in capped.head(15).itertuples():
        out(f"{r.college_code:>8} {r.branch_code:>7} {r.community:>5} {r.seats_2026:>10} "
            f"{fmt(r.historical_avg_seats):>10} {r.raw_ratio:>10.3f} "
            f"{r.seat_adjustment_factor:>11.3f} {r.overshoot:>10.3f}")

    # 4. seats_2026 == 0 but combo wasn't dropped
    zero_seat_leaked = lk[lk["seats_2026"] == 0]
    out(f"\n[4] seats_2026 == 0 rows surviving into final lookup: {len(zero_seat_leaked):>5} / {N_final}  "
        f"(must be 0 - confirms the drop-zero-seat-rows step worked)")
    if len(zero_seat_leaked):
        out(zero_seat_leaked.head(10).to_string())

    # 5. historical_avg_seats == 0 or null -> would divide by zero if unguarded
    no_hist = lk[lk["historical_avg_seats"].isna() | (lk["historical_avg_seats"] <= 0)]
    guard_held = (no_hist["seat_adjustment_factor"] == 1.0).all() and no_hist["limited_data"].all()
    out(f"\n[5] rows with null/zero historical_avg_seats:          {len(no_hist):>5} / {N_final}")
    out(f"    divide-by-zero guard held for all of them (factor forced to 1.0, "
        f"limited_data=True): {guard_held}")
    if not guard_held:
        bad = no_hist[(no_hist["seat_adjustment_factor"] != 1.0) | (~no_hist["limited_data"])]
        out("    *** GUARD FAILURE, rows below ***")
        out(bad.head(10).to_string())

    # ------------------------------------------------------------------ #
    section(f"IMPUTED COMBOS DETAIL ({len(imputed_rows)} rows, brand-new 2026 offerings)")

    rc = imputed_rows["predicted_closing_rank_2026"]
    out(f"predicted_closing_rank_2026 distribution across imputed rows:")
    out(f"  min={fmt(rc.min())}  max={fmt(rc.max())}  "
        f"median={fmt(rc.median())}  mean={fmt(rc.mean())}")

    imputed_unique_combos = sorted(set(zip(imputed_rows["college_code"], imputed_rows["branch_code"])))
    sample_combos = random.sample(imputed_unique_combos, min(20, len(imputed_unique_combos)))

    out(f"\nrandom sample of {len(sample_combos)} imputed combos vs CSE/ECE at the same college:")
    out(f"{'college_name':<45} {'branch_name':<38} {'imputed_rank':>12} {'CSE(OC)':>10} {'ECE(OC)':>10}")
    for ccode, bcode in sample_combos:
        cname = colleges.get(ccode, {}).get("college_name_full", f"College {ccode}")[:44]
        bname = branches.get(bcode, f"Branch {bcode}")[:37]

        row = imputed_rows[(imputed_rows["college_code"] == ccode)
                            & (imputed_rows["branch_code"] == bcode)
                            & (imputed_rows["community"] == "OC")]
        if row.empty:  # this combo had no OC seats, show whichever community it does have
            row = imputed_rows[(imputed_rows["college_code"] == ccode)
                                & (imputed_rows["branch_code"] == bcode)]
        imputed_rank = int(row.iloc[0]["predicted_closing_rank_2026"]) if not row.empty else None

        cse = lk[(lk["college_code"] == ccode) & (lk["branch_code"] == "CS") & (lk["community"] == "OC")]
        ece = lk[(lk["college_code"] == ccode) & (lk["branch_code"] == "EC") & (lk["community"] == "OC")]
        cse_rank = int(cse.iloc[0]["predicted_closing_rank_2026"]) if not cse.empty else None
        ece_rank = int(ece.iloc[0]["predicted_closing_rank_2026"]) if not ece.empty else None

        out(f"{cname:<45} {bname:<38} {fmt(imputed_rank):>12} {fmt(cse_rank):>10} {fmt(ece_rank):>10}")

    # ------------------------------------------------------------------ #
    section(f"DROPPED COMBOS DETAIL ({len(dropped_combos)} combos absent from 2026 seat matrix)")

    raw_sm = pd.read_csv(DATA_DIR / "seat_matrix_2026.csv", dtype={"college_code": int, "branch_code": str})
    sample_rows = dropped.sample(min(20, len(dropped)), random_state=RNG_SEED)

    out(f"random sample of {len(sample_rows)} dropped rows, independently re-checked against "
        f"the raw seat_matrix_2026.csv (not the cached combo set):")
    out(f"{'college_name':<45} {'branch_name':<32} {'comm':>5}  verification")
    mismatches = 0
    for r in sample_rows.itertuples():
        cname = colleges.get(r.college_code, {}).get("college_name_full", f"College {r.college_code}")[:44]
        bname = branches.get(r.branch_code, f"Branch {r.branch_code}")[:31]
        match_count = len(raw_sm[(raw_sm["college_code"] == r.college_code)
                                  & (raw_sm["branch_code"] == r.branch_code)])
        if match_count == 0:
            verdict = "CONFIRMED ABSENT from 2026 matrix"
        else:
            verdict = f"*** MISMATCH: found {match_count} row(s) in seat matrix ***"
            mismatches += 1
        out(f"{cname:<45} {bname:<32} {r.community:>5}  {verdict}")
    out(f"\nmismatches found: {mismatches} / {len(sample_rows)} "
        f"(should be 0 - confirms exclusion is a real seat-matrix absence, not a code bug)")

    # ------------------------------------------------------------------ #
    section("SUMMARY")

    lk["prob_old"] = lk["closing_rank_unadjusted"].apply(probability_for)
    non_imputed = lk[~lk["imputed_base"]]

    out(f"{'stage':<55} {'rows':>10} {'distinct combos':>18}")
    out(f"{'-'*55} {'-'*10} {'-'*18}")
    out(f"{'0. raw cutoff_lookup_2026.csv':<55} {N0:>10,} {raw_lookup.groupby(['college_code','branch_code']).ngroups:>18,}")
    out(f"{'1. after 2026-seat-matrix exclusion':<55} {N1:>10,} {len(existing_combos):>18,}")
    out(f"{'2. after imputing brand-new 2026 offerings':<55} {N1 + len(imputed_rows):>10,} "
        f"{len(existing_combos) + len(imputed_combos_actual):>18,}")
    out(f"{'3. FINAL (after dropping 0-seat community rows)':<55} {N_final:>10,} "
        f"{lk.groupby(['college_code','branch_code']).ngroups:>18,}")

    out(f"\nanomaly check counts:")
    out(f"  [1] bad predicted_closing_rank_2026:        {bad_rank_mask.sum()}")
    out(f"  [2] probability outside 0-100:              {out_of_range.sum()}")
    out(f"  [3] seat_adjustment_factor at clip boundary: {capped_mask.sum()}")
    out(f"  [4] seats_2026==0 leaked into final lookup:  {len(zero_seat_leaked)}")
    out(f"  [5] null/zero historical_avg_seats rows:     {len(no_hist)}  (guard held: {guard_held})")

    def dist(series):
        s = series.dropna()
        return f"min={fmt(s.min(),1)} max={fmt(s.max(),1)} mean={fmt(s.mean(),1)} median={fmt(s.median(),1)}"

    out(f"\nprobability distribution, ALL {N_final} rows, fixed test rank={TEST_RANK:,}:")
    out(f"  BEFORE adjustment (closing_rank_unadjusted): {dist(lk['prob_old'])}")
    out(f"  AFTER  adjustment (predicted_closing_rank_2026): {dist(lk['prob_new'])}")

    out(f"\nsame distribution, {len(non_imputed)} NON-IMPUTED rows only "
        f"(closing_rank_unadjusted is a real cutoff_predictor.pkl output here, not a fallback average):")
    out(f"  BEFORE adjustment: {dist(non_imputed['prob_old'])}")
    out(f"  AFTER  adjustment: {dist(non_imputed['prob_new'])}")

    out(f"\nseat_adjustment_factor distribution, ALL {N_final} rows:")
    fac = lk["seat_adjustment_factor"]
    out(f"  min={fac.min():.3f} max={fac.max():.3f} mean={fac.mean():.3f} median={fac.median():.3f}")

    # ------------------------------------------------------------------ #
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(_LOG) + "\n", encoding="utf-8")
    print(f"\nfull report written to {OUT_PATH}")


if __name__ == "__main__":
    main()
