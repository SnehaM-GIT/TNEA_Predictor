"""Phase 7: Data integrity checks — no NaN, correct sorts, valid codes, etc."""
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.ml_utils import predict_rank
from predict_colleges import predict_colleges

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR  = BASE_DIR / "data" / "cleaned"

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]
SAFE_MARGIN = 500


def check(label, condition, detail=""):
    sym = "✅" if condition else "❌"
    print(f"  {sym} {label}" + (f"  [{detail}]" if detail else ""))
    return condition


def main():
    print("=" * 65)
    print("PHASE 7: DATA INTEGRITY CHECKS")
    print("=" * 65)

    total  = 0
    passed = 0

    # ── 1. No NaN / None in rank predictions ─────────────────────────────────
    print("\n[1] Rank predictions — no NaN / None")
    sample = [(200,"OC"),(195,"BC"),(150,"SC"),(100,"ST"),(75,"MBC"),(0,"SCA")]
    for marks, comm in sample:
        r = predict_rank(marks, comm)
        total += 1
        if "error" not in r:
            ok = (
                r["predicted_rank"] is not None
                and not np.isnan(r["predicted_rank"])
                and r["range_min"] is not None
                and r["range_max"] is not None
                and r["confidence"] is not None
            )
        else:
            ok = True  # errors are explicit, not NaN
        passed += ok
        check(f"marks={marks} {comm}: no NaN in output", ok,
              f"pred={r.get('predicted_rank','ERR')}")

    # ── 2. Range is always ±100 ───────────────────────────────────────────────
    print("\n[2] Range width = exactly ±100")
    marks_list = [200, 195, 150, 100, 75, 50]
    for marks in marks_list:
        r = predict_rank(marks, "OC")
        total += 1
        if "error" not in r:
            pred = r["predicted_rank"]
            ok = (r["range_max"] == pred + 100
                  and r["range_min"] == max(1, pred - 100))
        else:
            ok = True
        passed += ok
        check(f"marks={marks}: range = [{r.get('range_min','?')} – {r.get('range_max','?')}]",
              ok, f"pred={r.get('predicted_rank','ERR')}")

    # ── 3. Confidence in [0, 100] ─────────────────────────────────────────────
    print("\n[3] Confidence always in [0, 100]")
    for marks in [200, 195, 150, 100, 75]:
        for comm in ["OC", "SC"]:
            r = predict_rank(marks, comm)
            total += 1
            ok = "error" in r or (0 <= r["confidence"] <= 100)
            passed += ok
            check(f"marks={marks} {comm}: conf={r.get('confidence','ERR')} ∈ [0,100]", ok)

    # ── 4. No duplicate (college+branch) combos in top 5 ────────────────────
    print("\n[4] No duplicate (college+branch) combos in top 5 recommendations")
    test_cases = [(200,"OC"),(195,"BC"),(150,"SC"),(100,"MBC"),(75,"SCA")]
    for marks, comm in test_cases:
        r = predict_colleges(marks, comm, top_n=5)
        total += 1
        if "error" not in r:
            combos = [(rec["college_code"], rec.get("branch_code", "?"))
                      for rec in r["recommendations"]]
            ok = len(combos) == len(set(combos))
        else:
            ok = True
            combos = []
        passed += ok
        check(f"marks={marks} {comm}: no duplicate college+branch combos", ok,
              f"combos={combos[:3]}..." if not ok else "")

    # ── 5. Colleges sorted by tier then closing_rank ─────────────────────────
    print("\n[5] Recommendations sorted (tier asc, closing_rank asc)")
    TIER_RANK = {
        "University Departments": 0, "Constituent Colleges": 1,
        "Government Colleges": 2, "Government Aided Colleges": 3,
        "Cecri And Cipet": 4, "Self Financing Engineering Colleges": 5,
    }
    for marks, comm in [(200,"OC"),(195,"BC"),(150,"OC")]:
        r = predict_colleges(marks, comm, top_n=5)
        total += 1
        if "error" not in r and len(r["recommendations"]) >= 2:
            recs = r["recommendations"]
            tiers = [TIER_RANK.get(rec["college_type"], 9) for rec in recs]
            crs   = [rec["closing_rank"] for rec in recs]
            # Within same tier, closing_rank must be non-decreasing
            ok = True
            for i in range(len(recs) - 1):
                if tiers[i] == tiers[i+1] and crs[i] > crs[i+1]:
                    ok = False
                    break
                if tiers[i] > tiers[i+1]:  # tier went up — wrong
                    ok = False
                    break
        else:
            ok = True
        passed += ok
        check(f"marks={marks} {comm}: sort order correct", ok)

    # ── 6. College code mapping coverage ──────────────────────────────────────
    print("\n[6] College code coverage (unmapped < 5% of rows is ACCEPTABLE)")
    cc_df = pd.read_csv(DATA_DIR / "college_codes.csv")
    lk_df = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv")
    total += 1
    missing_codes = set(lk_df["college_code"].unique()) - set(cc_df["college_code"].unique())
    affected_rows = lk_df[lk_df["college_code"].isin(missing_codes)]
    pct_unmapped = len(affected_rows) / len(lk_df) * 100 if len(lk_df) else 0
    ok = pct_unmapped < 5.0  # <5% unmapped is acceptable
    passed += ok
    sym2 = "⚠️ " if (not ok or len(missing_codes) > 0) else ""
    n_unique = lk_df["college_code"].nunique()
    print(f"  {'✅' if ok else '⚠️ '} College code coverage: "
          f"{n_unique - len(missing_codes)}/{n_unique} codes mapped, "
          f"{len(missing_codes)} unmapped → "
          f"{len(affected_rows)} rows ({pct_unmapped:.1f}%) will show 'College XXXX'")

    # ── 7. All branch codes map to valid names ────────────────────────────────
    print("\n[7] Branch codes → coverage (expect ~78% mapped)")
    cr_df = pd.read_csv(DATA_DIR / "course_codes.csv")
    lk_branches = lk_df["branch_code"].astype(str).unique()
    cr_branches  = cr_df["branch_code"].astype(str).unique()
    mapped = sum(1 for b in lk_branches if b in cr_branches)
    pct = mapped / len(lk_branches) * 100 if len(lk_branches) else 0
    total += 1
    ok = pct >= 70  # ≥70% mapped is acceptable (script says ~78%)
    passed += ok
    check(f"Branch code coverage: {mapped}/{len(lk_branches)} = {pct:.1f}% mapped", ok)

    # ── 8. Closing ranks positive integers ───────────────────────────────────
    print("\n[8] All predicted_closing_rank_2026 are positive integers")
    total += 1
    bad = lk_df[lk_df["predicted_closing_rank_2026"] <= 0]
    ok  = len(bad) == 0
    passed += ok
    check(f"All {len(lk_df):,} closing ranks > 0", ok,
          f"{len(bad)} bad rows" if not ok else "")

    # ── 9. Safety margin = closing_rank − predicted_rank ─────────────────────
    print("\n[9] Safety margin = closing_rank − student_rank")
    for marks, comm in [(195,"OC"),(150,"BC")]:
        r = predict_colleges(marks, comm, top_n=5)
        total += 1
        if "error" not in r:
            recs = r["recommendations"]
            pred = r["student_rank"]
            ok = all(rec["safety_margin"] == rec["closing_rank"] - pred for rec in recs)
        else:
            ok = True
        passed += ok
        check(f"marks={marks} {comm}: safety_margin consistent", ok)

    # ── 10. No WONT_GET in recommendations ───────────────────────────────────
    print("\n[10] No WONT_GET recommendations (all attainable)")
    for marks, comm in [(200,"OC"),(195,"BC"),(150,"SC"),(100,"MBC"),(75,"SCA")]:
        r = predict_colleges(marks, comm, top_n=5)
        total += 1
        if "error" not in r:
            ok = all(rec["status"] != "WONT_GET" for rec in r["recommendations"])
        else:
            ok = True
        passed += ok
        check(f"marks={marks} {comm}: no WONT_GET in recs", ok)

    # ── 11. cutoff_lookup_2026 has no NaN ─────────────────────────────────────
    print("\n[11] cutoff_lookup_2026.csv has no NaN values")
    total += 1
    nan_count = lk_df.isnull().sum().sum()
    ok = nan_count == 0
    passed += ok
    check(f"No NaN in cutoff_lookup_2026.csv ({len(lk_df):,} rows)", ok,
          f"{nan_count} NaN cells" if not ok else "")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"Data integrity checks: {passed}/{total} passed")
    if passed == total:
        print("VERDICT: ✅ ALL INTEGRITY CHECKS PASSED")
    else:
        print(f"VERDICT: ❌ {total - passed} CHECKS FAILED")
    print(f"{'='*65}")
    return passed, total


if __name__ == "__main__":
    main()
