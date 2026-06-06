"""Phase 1: Rank model comprehensive test — 20 cases (5 marks × 4 communities)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.ml_utils import predict_rank

MARKS_LIST = [200, 195, 150, 100, 75]
COMMUNITIES = ["OC", "BC", "SC", "MBC"]

# Conservative expected rank ranges per marks level (based on CDF of 239k students)
EXPECTED_RANGES = {
    200: (1, 2000),
    195: (1, 10000),
    150: (5000, 230000),   # actual: ~118k (50% of students score above 150)
    100: (20000, 239299),
    75:  (50000, 239299),
}


def test_all():
    print("=" * 95)
    print("PHASE 1: RANK MODEL COMPREHENSIVE TEST  (5 marks × 4 communities = 20 cases)")
    print("=" * 95)
    print(f"{'#':>3} {'Marks':>6} {'Community':>10} {'Pred Rank':>12} "
          f"{'Range':>22} {'Conf':>6} {'Basis':>12} {'Status':>6}")
    print("-" * 95)

    total = 0
    passed = 0
    warnings = []
    failures = []

    for marks in MARKS_LIST:
        for community in COMMUNITIES:
            total += 1
            result = predict_rank(marks, community)

            if "error" in result:
                print(f"{total:>3} {marks:>6} {community:>10}  ERROR: {result['error']}")
                failures.append(f"#{total} marks={marks} community={community}: {result['error']}")
                continue

            pred_rank = result["predicted_rank"]
            rmin      = result["range_min"]
            rmax      = result["range_max"]
            conf      = result["confidence"]
            basis     = result.get("basis", "?")

            # Structural checks
            struct_ok = (
                isinstance(pred_rank, int)
                and isinstance(rmin, int)
                and isinstance(rmax, int)
                and rmax == pred_rank + 100
                and rmin == max(1, pred_rank - 100)
                and 0 <= conf <= 100
                and "predicted_rank" in result
                and "range_min" in result
                and "range_max" in result
                and "confidence" in result
                and "basis" in result
            )

            lo, hi = EXPECTED_RANGES[marks]
            range_ok = lo <= pred_rank <= hi

            if struct_ok and range_ok:
                status = "✅"
                passed += 1
            elif struct_ok:
                status = "⚠️"
                warnings.append(
                    f"#{total} marks={marks} {community}: rank={pred_rank:,} "
                    f"expected [{lo:,}–{hi:,}]"
                )
            else:
                status = "❌"
                failures.append(
                    f"#{total} marks={marks} {community}: struct_ok={struct_ok} "
                    f"pred_rank={pred_rank} rmin={rmin} rmax={rmax}"
                )

            range_str = f"[{rmin:,} – {rmax:,}]"
            print(f"{total:>3} {marks:>6} {community:>10} {pred_rank:>12,} "
                  f"{range_str:>22} {conf:>5}% {basis[:12]:>12} {status:>6}")

    print("-" * 95)
    print(f"\nPassed: {passed}/{total}")

    if warnings:
        print("\nWarnings (struct OK, range unexpected):")
        for w in warnings:
            print(f"  ⚠️  {w}")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  ❌  {f}")

    if passed == total:
        print("\nVERDICT: ✅ ALL 20 TESTS PASSED")
    elif passed + len(warnings) == total:
        print(f"\nVERDICT: ⚠️  {passed} PASS, {len(warnings)} RANGE WARNINGS (structure correct)")
    else:
        print(f"\nVERDICT: ❌  {len(failures)} STRUCTURAL FAILURES")

    return passed, total


if __name__ == "__main__":
    test_all()
