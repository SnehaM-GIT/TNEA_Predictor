#!/usr/bin/env python3
"""
Orchestrates 4 locust load tests in sequence, then parses all CSVs.
Run from repo root: python run_load_tests.py
Expected wall time: ~75 minutes (dominated by 60-min soak)
"""

import subprocess
import sys
import os
import time
import csv
import httpx
from pathlib import Path

LOCUSTFILE = Path(__file__).parent / "locustfile.py"
HOST       = "https://tneapredictor-production.up.railway.app"
PYTHON     = sys.executable

TESTS = [
    # (label,         users, spawn_rate, run_time, csv_prefix)
    ("RAMP-1K",    1000,  50,    "5m",  "results_ramp_1k"),
    ("SPIKE-5K",   5000,  5000,  "3m",  "results_spike_5k"),
    ("SPIKE-10K",  10000, 10000, "2m",  "results_spike_10k"),
    ("SOAK-500",   500,   20,    "60m", "results_soak"),
]

THRESHOLDS = {
    "/predict/colleges": {"p95_warn": 2000, "p95_hard": 5000},
    "/auth/login":       {"p95_warn": 500,  "p95_hard": 2000},
    "/payment/create-order": {"p95_warn": 1000, "p95_hard": 3000},
}
FAIL_RATE_WARN = 1.0   # %
FAIL_RATE_HARD = 2.0   # %


def run_locust(label, users, spawn_rate, run_time, csv_prefix):
    cmd = [
        PYTHON, "-m", "locust",
        "--headless",
        "-f", str(LOCUSTFILE),
        f"--host={HOST}",
        f"-u", str(users),
        f"-r", str(spawn_rate),
        f"--run-time={run_time}",
        f"--csv={csv_prefix}",
        "--csv-full-history",
        "--only-summary",
        "--stop-timeout=30",
    ]
    print(f"\n{'='*65}")
    print(f"  STARTING: {label}  users={users}  spawn={spawn_rate}/s  duration={run_time}")
    print(f"{'='*65}")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=False, text=True)
    elapsed = time.time() - t0
    print(f"  DONE: {label} in {elapsed:.0f}s  exit={proc.returncode}")
    return proc.returncode


def parse_stats(csv_prefix):
    """Parse _stats.csv, return list of row dicts."""
    path = Path(f"{csv_prefix}_stats.csv")
    if not path.exists():
        return []
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Name", "").strip() == "Aggregated":
                continue
            rows.append(row)
    return rows


def flag(value, warn, hard, higher_is_worse=True):
    if value is None:
        return ""
    v = float(value)
    if higher_is_worse:
        if v >= hard:   return "HARD-FAIL"
        if v >= warn:   return "WARN"
    return ""


def main():
    print("NOTE: Open Railway metrics dashboard and UptimeRobot now.")
    print("      Tests start in 5 seconds...\n")
    time.sleep(5)

    # Run all 4 tests
    exits = {}
    for label, users, spawn_rate, run_time, csv_prefix in TESTS:
        rc = run_locust(label, users, spawn_rate, run_time, csv_prefix)
        exits[label] = rc

    # ── 10-minute post-10K health check ──────────────────────────────
    print(f"\n{'='*65}")
    print("  POST-10K SPIKE: waiting 10 minutes then checking /config ...")
    print(f"{'='*65}")
    time.sleep(600)
    try:
        r = httpx.get(f"{HOST}/config", timeout=15)
        post_spike_ok = r.status_code == 200 and "rank_list_released" in r.json()
        print(f"  /config after 10min: {r.status_code}  {r.text[:80]}")
        print(f"  Site health post-10K spike: {'OK' if post_spike_ok else 'DEGRADED'}")
    except Exception as e:
        post_spike_ok = False
        print(f"  /config FAILED: {e}")

    # ── Parse + report ────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("  LOAD TEST RESULTS")
    print(f"{'='*65}")

    all_flags = []

    for label, users, spawn_rate, run_time, csv_prefix in TESTS:
        rows = parse_stats(csv_prefix)
        if not rows:
            print(f"\n[{label}] No stats CSV found (test may have failed to start)")
            continue

        print(f"\n[{label}]  users={users}  spawn={spawn_rate}/s  duration={run_time}")
        print(f"  {'Endpoint':<42} {'Req':>7} {'Fail':>6} {'Fail%':>6} {'Med':>6} {'p95':>6} {'Max':>7}  FLAGS")
        print(f"  {'-'*42} {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*7}  -----")

        for row in rows:
            name  = row.get("Name", "")
            # Strip trailing task labels like [guest] [auth]
            base  = name.split(" [")[0].strip()

            reqs  = int(row.get("Request Count", 0) or 0)
            fails = int(row.get("Failure Count", 0) or 0)
            frate = (fails / reqs * 100) if reqs else 0

            med   = row.get("50%", "")
            p95   = row.get("95%", "")
            mx    = row.get("Max", "")

            def _f(x):
                try: return float(x)
                except: return None

            flags = []
            if frate >= FAIL_RATE_HARD:
                flags.append(f"FAIL-RATE-HARD({frate:.1f}%>={FAIL_RATE_HARD}%)")
            elif frate >= FAIL_RATE_WARN:
                flags.append(f"FAIL-RATE-WARN({frate:.1f}%>={FAIL_RATE_WARN}%)")

            if base in THRESHOLDS:
                th = THRESHOLDS[base]
                p95v = _f(p95)
                if p95v is not None:
                    if p95v >= th["p95_hard"]:
                        flags.append(f"P95-HARD({p95v:.0f}>={th['p95_hard']}ms)")
                    elif p95v >= th["p95_warn"]:
                        flags.append(f"P95-WARN({p95v:.0f}>={th['p95_warn']}ms)")

            flag_str = " | ".join(flags) if flags else "ok"
            if flags:
                all_flags.append(f"[{label}] {name}: {' | '.join(flags)}")

            print(f"  {name:<42} {reqs:>7} {fails:>6} {frate:>5.1f}% "
                  f"{med:>6} {p95:>6} {mx:>7}  {flag_str}")

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("  SUMMARY")
    print(f"{'='*65}")
    for label, _, _, _, _ in TESTS:
        print(f"  {label}: exit={exits.get(label,'?')}")
    print(f"\n  Post-10K spike /config: {'200 OK' if post_spike_ok else 'DEGRADED/FAIL'}")

    if all_flags:
        print(f"\n  !!! FLAGGED ({len(all_flags)}) !!!")
        for f in all_flags:
            print(f"    {f}")
    else:
        print("\n  No threshold violations detected.")

    print(f"\n{'='*65}")


if __name__ == "__main__":
    main()
