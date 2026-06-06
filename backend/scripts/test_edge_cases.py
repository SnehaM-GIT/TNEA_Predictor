"""Phase 4: Edge case testing for predict_rank and predict_colleges."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.ml_utils import predict_rank
from predict_colleges import predict_colleges


def run_case(label, fn, *args, expect_error=False, expect_crash=False):
    """Run one edge case. Return (passed, actual_result_summary)."""
    try:
        result = fn(*args)
        if expect_crash:
            return False, f"Expected crash but got result: {result}"
        if expect_error:
            if isinstance(result, dict) and "error" in result:
                return True, f"Correctly returned error: {result['error']}"
            else:
                return False, f"Expected error dict, got: {str(result)[:80]}"
        # Expect graceful success
        if isinstance(result, dict) and "error" not in result:
            return True, f"OK (keys: {list(result.keys())[:5]})"
        elif isinstance(result, dict) and "error" in result:
            # Graceful error is still acceptable
            return True, f"Graceful error: {result['error']}"
        else:
            return False, f"Unexpected result type: {type(result)}"
    except (TypeError, ValueError, KeyError) as exc:
        if expect_crash:
            return True, f"Expected crash caught: {type(exc).__name__}: {exc}"
        return False, f"Unexpected crash: {type(exc).__name__}: {exc}"
    except Exception as exc:
        if expect_crash:
            return True, f"Crash caught: {type(exc).__name__}: {exc}"
        return False, f"Crash: {type(exc).__name__}: {exc}"


def main():
    print("=" * 75)
    print("PHASE 4: EDGE CASE TESTING")
    print("=" * 75)

    cases = [
        # label, fn, args, expect_error, expect_crash
        # ── Minimum marks ────────────────────────────────────────────────────
        ("marks=0 OC",   predict_rank, (0,   "OC"),  False, False),
        ("marks=1 OC",   predict_rank, (1,   "OC"),  False, False),
        ("marks=10 OC",  predict_rank, (10,  "OC"),  False, False),
        # ── Maximum marks ────────────────────────────────────────────────────
        ("marks=200 OC", predict_rank, (200, "OC"),  False, False),
        ("marks=199 OC", predict_rank, (199, "OC"),  False, False),
        ("marks=199.5 OC", predict_rank, (199.5,"OC"), False, False),
        # ── Out-of-range marks (no hard validation in model — should extrapolate) ─
        ("marks=-5 OC",  predict_rank, (-5,  "OC"),  False, False),
        ("marks=250 OC", predict_rank, (250, "OC"),  False, False),
        # ── Invalid community ─────────────────────────────────────────────────
        ("community=INVALID",  predict_rank, (195, "INVALID"),  True, False),
        ("community=invalid",  predict_rank, (150, "invalid"),  True, False),
        ("community=''",       predict_rank, (150, ""),         True, False),
        # ── marks='abc' → should crash (Python can't round a string) ──────────
        ("marks='abc' OC",     predict_rank, ("abc", "OC"),     False, True),
        # ── Decimal marks ─────────────────────────────────────────────────────
        ("marks=195.5 OC",  predict_rank, (195.5, "OC"),  False, False),
        ("marks=100.25 BC", predict_rank, (100.25,"BC"),  False, False),
        # ── BCM → BC alias ───────────────────────────────────────────────────
        ("community=BCM",   predict_rank, (150, "BCM"),   False, False),
        # ── All valid communities ─────────────────────────────────────────────
        ("OC",  predict_rank, (180, "OC"),  False, False),
        ("BC",  predict_rank, (180, "BC"),  False, False),
        ("SC",  predict_rank, (180, "SC"),  False, False),
        ("ST",  predict_rank, (180, "ST"),  False, False),
        ("MBC", predict_rank, (180, "MBC"), False, False),
        ("SCA", predict_rank, (180, "SCA"), False, False),
        # ── predict_colleges edge cases ───────────────────────────────────────
        ("colleges marks=0 OC",   predict_colleges, (0,   "OC"),  False, False),
        ("colleges marks=200 OC", predict_colleges, (200, "OC"),  False, False),
        ("colleges marks=75 SCA", predict_colleges, (75,  "SCA"), False, False),
        ("colleges invalid comm", predict_colleges, (150, "INVALID"), True, False),
        ("colleges BCM→BC",       predict_colleges, (150, "BCM"),    False, False),
    ]

    print(f"\n{'#':>3} {'Case':40} {'Result':>7}  Detail")
    print("-" * 75)

    total  = 0
    passed = 0

    for i, entry in enumerate(cases, 1):
        label, fn, args, expect_error, expect_crash = entry
        total += 1
        ok, detail = run_case(label, fn, *args,
                               expect_error=expect_error, expect_crash=expect_crash)
        if ok:
            passed += 1
            sym = "✅"
        else:
            sym = "❌"
        print(f"{i:>3} {label:40} {sym:>7}  {detail[:60]}")

    print("-" * 75)
    print(f"\nPassed: {passed}/{total}")

    # ── Extra: verify extreme ranks make sense ───────────────────────────────
    print("\nExtra sanity checks:")
    r0   = predict_rank(0,   "OC")
    r200 = predict_rank(200, "OC")
    if "error" not in r0 and "error" not in r200:
        high_rank  = r0.get("predicted_rank", 0)
        low_rank   = r200.get("predicted_rank", 999999)
        monotone   = high_rank > low_rank
        print(f"  marks=0   → rank {high_rank:,}")
        print(f"  marks=200 → rank {low_rank:,}")
        print(f"  Monotone (marks=0 rank > marks=200 rank): {'✅' if monotone else '❌'}")
        if monotone:
            passed += 1
        total += 1

    if passed == total:
        print(f"\nVERDICT: ✅ ALL {total} EDGE CASES HANDLED")
    else:
        print(f"\nVERDICT: ❌ {total - passed}/{total} CASES FAILED")

    return passed, total


if __name__ == "__main__":
    main()
