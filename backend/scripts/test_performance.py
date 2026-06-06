"""Phase 5: Performance benchmarking — load time, prediction time, concurrency."""
import sys
import time
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


TARGETS = {
    "model_load_ms":    5000,
    "rank_pred_ms":      100,
    "college_pred_ms":   500,
    "concurrent_100_ms":10000,
}


def main():
    print("=" * 60)
    print("PHASE 5: PERFORMANCE TESTING")
    print("=" * 60)

    results = {}

    # ── 1. Model load time ────────────────────────────────────────────────────
    print("\n[1/4] Model load time ...")
    import importlib
    # Force a cold load by clearing cached state
    import utils.ml_utils as mlmod
    mlmod.MODEL_DATA = None  # reset cache

    t0 = time.perf_counter()
    mlmod.load_model()
    load_ms = (time.perf_counter() - t0) * 1000
    results["model_load_ms"] = load_ms
    target = TARGETS["model_load_ms"]
    sym = "✅" if load_ms < target else "❌"
    print(f"  Load time : {load_ms:>8.1f} ms  (target < {target} ms)  {sym}")

    # ── 2. Single rank prediction ─────────────────────────────────────────────
    print("\n[2/4] Single rank prediction time ...")
    from utils.ml_utils import predict_rank

    # warm-up
    predict_rank(195, "OC")

    N = 50
    t0 = time.perf_counter()
    for _ in range(N):
        predict_rank(195, "OC")
    rank_ms = (time.perf_counter() - t0) * 1000 / N
    results["rank_pred_ms"] = rank_ms
    target = TARGETS["rank_pred_ms"]
    sym = "✅" if rank_ms < target else "❌"
    print(f"  Rank pred : {rank_ms:>8.2f} ms  (target < {target} ms)  {sym}  "
          f"(avg over {N} calls)")

    # ── 3. College recommendation time ────────────────────────────────────────
    print("\n[3/4] College prediction time ...")
    from predict_colleges import predict_colleges

    # warm-up
    predict_colleges(195, "OC", top_n=5)

    N = 20
    t0 = time.perf_counter()
    for _ in range(N):
        predict_colleges(195, "OC", top_n=5)
    col_ms = (time.perf_counter() - t0) * 1000 / N
    results["college_pred_ms"] = col_ms
    target = TARGETS["college_pred_ms"]
    sym = "✅" if col_ms < target else "❌"
    print(f"  College   : {col_ms:>8.1f} ms  (target < {target} ms)  {sym}  "
          f"(avg over {N} calls)")

    # ── 4. 100 concurrent requests ────────────────────────────────────────────
    print("\n[4/4] 100 concurrent requests ...")
    errors = []
    results_list = [None] * 100

    def worker(idx):
        try:
            marks = [200, 195, 180, 150, 100, 75][idx % 6]
            comm  = ["OC", "BC", "SC", "ST", "MBC", "SCA"][idx % 6]
            results_list[idx] = predict_colleges(marks, comm, top_n=5)
        except Exception as exc:
            errors.append(f"Thread {idx}: {exc}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(100)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)
    conc_ms = (time.perf_counter() - t0) * 1000
    results["concurrent_100_ms"] = conc_ms

    crashed = sum(1 for r in results_list if r is None)
    target  = TARGETS["concurrent_100_ms"]
    sym = "✅" if (conc_ms < target and not errors and crashed == 0) else "❌"
    print(f"  100 reqs  : {conc_ms:>8.1f} ms  (target < {target} ms)  {sym}")
    if errors:
        for e in errors[:5]:
            print(f"    Error: {e}")
    if crashed:
        print(f"    {crashed} threads did not complete")
    else:
        print(f"    All 100 completed, no crashes")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("-" * 60)
    print(f"  {'Metric':<30} {'Actual':>10}  {'Target':>10}  {'Pass':>5}")
    print("-" * 60)
    labels = {
        "model_load_ms":    "Model load",
        "rank_pred_ms":     "Rank prediction (avg)",
        "college_pred_ms":  "College prediction (avg)",
        "concurrent_100_ms":"100 concurrent requests",
    }
    all_pass = True
    for k, label in labels.items():
        v = results.get(k, float("inf"))
        t = TARGETS[k]
        ok = v < t
        if not ok:
            all_pass = False
        sym = "✅" if ok else "❌"
        print(f"  {label:<30} {v:>8.1f} ms  {t:>8} ms  {sym:>5}")
    print("=" * 60)
    print(f"VERDICT: {'✅ ALL TARGETS MET' if all_pass else '❌ SOME TARGETS MISSED'}")
    return all_pass


if __name__ == "__main__":
    main()
