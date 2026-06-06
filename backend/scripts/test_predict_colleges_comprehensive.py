"""Phase 3: predict_colleges() comprehensive validation — 50 realistic test cases."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from predict_colleges import predict_colleges

# 10 cases per marks tier, cycling through communities
COMMUNITIES_CYCLE = ["OC", "BC", "SC", "ST", "MBC", "SCA", "OC", "BC", "SC", "ST"]

TIERS = [
    (200, "marks=200 (excellent)"),
    (195, "marks=195 (very good)"),
    (150, "marks=150 (average)"),
    (100, "marks=100 (below average)"),
    (75,  "marks=75  (low score)"),
]

SAFE_MARGIN = 500  # must match predict_colleges.py


def check_result(marks, community, result, test_num):
    issues = []

    if "error" in result:
        return False, [f"Function returned error: {result['error']}"], 0

    # Top-level fields
    for field in ["student_rank", "student_rank_range", "rank_confidence",
                  "community", "recommendations"]:
        if field not in result:
            issues.append(f"Missing field: {field}")

    if issues:
        return False, issues, 0

    rank  = result["student_rank"]
    rng   = result["student_rank_range"]
    conf  = result["rank_confidence"]
    recs  = result["recommendations"]

    if not isinstance(rank, int):
        issues.append(f"student_rank not int: {type(rank)}")
    if not (isinstance(rng, list) and len(rng) == 2):
        issues.append(f"student_rank_range wrong: {rng}")
    if not (0 <= conf <= 100):
        issues.append(f"rank_confidence out of range: {conf}")

    if not isinstance(recs, list):
        issues.append("recommendations not a list")
        return False, issues, 0

    n_colleges = len(recs)
    statuses = set()

    for i, rec in enumerate(recs, 1):
        for rf in ["college_name", "college_type", "college_district",
                   "branch_name", "closing_rank", "safety_margin",
                   "status", "match_confidence"]:
            if rf not in rec:
                issues.append(f"rec[{i}] missing field: {rf}")

        if "status" not in rec or "safety_margin" not in rec or "closing_rank" not in rec:
            continue

        status = rec["status"]
        margin = rec["safety_margin"]
        cr     = rec["closing_rank"]
        mc     = rec.get("match_confidence", -1)
        statuses.add(status)

        # WONT_GET should never appear (filtered in predict_colleges)
        if status == "WONT_GET":
            issues.append(f"rec[{i}] status=WONT_GET should be filtered out")

        # Status↔margin consistency
        if status == "SAFE" and margin <= SAFE_MARGIN:
            issues.append(f"rec[{i}] SAFE but margin={margin} <= {SAFE_MARGIN}")
        if status == "MARGINAL" and not (0 <= margin <= SAFE_MARGIN):
            issues.append(f"rec[{i}] MARGINAL but margin={margin}")

        # safety_margin = closing_rank - predicted_rank
        if cr - rank != margin:
            issues.append(f"rec[{i}] safety_margin mismatch: {cr}-{rank}={cr-rank} != {margin}")

        if not (0 <= mc <= 100):
            issues.append(f"rec[{i}] match_confidence out of range: {mc}")

        # college_name should be a string, not a numeric code
        cname = rec.get("college_name", "")
        if not isinstance(cname, str) or not cname:
            issues.append(f"rec[{i}] college_name invalid: {cname!r}")

    ok = len(issues) == 0
    return ok, issues, n_colleges


def main():
    print("=" * 85)
    print("PHASE 3: predict_colleges() COMPREHENSIVE TEST  (50 cases)")
    print("=" * 85)
    print(f"{'#':>3} {'Marks':>6} {'Comm':>6} {'Rank':>8} {'Colleges':>9} "
          f"{'Statuses':>22} {'Result':>7}")
    print("-" * 85)

    total  = 0
    passed = 0
    all_issues = []

    for marks, tier_label in TIERS:
        for comm in COMMUNITIES_CYCLE:
            total += 1
            result = predict_colleges(marks, comm, top_n=5)
            ok, issues, n_cols = check_result(marks, comm, result, total)

            if ok:
                passed += 1

            recs     = result.get("recommendations", [])
            rank     = result.get("student_rank", "?")
            statuses = ", ".join(sorted({r.get("status", "?") for r in recs})) if recs else "—"
            res_sym  = "✅" if ok else "❌"

            print(f"{total:>3} {marks:>6} {comm:>6} {str(rank):>8} "
                  f"{n_cols:>9} {statuses:>22} {res_sym:>7}")

            if issues:
                all_issues.append((total, marks, comm, issues))

    print("-" * 85)
    print(f"\nPassed: {passed}/{total}")

    if all_issues:
        print("\nIssues:")
        for num, m, c, iss in all_issues:
            print(f"  Test #{num} (marks={m}, {c}):")
            for issue in iss:
                print(f"    • {issue}")

    if passed == total:
        print("\nVERDICT: ✅ ALL 50 TESTS PASSED")
    else:
        print(f"\nVERDICT: ❌ {total - passed} FAILURES")

    return passed, total


if __name__ == "__main__":
    main()
