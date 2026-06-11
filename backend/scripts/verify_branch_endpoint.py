"""
Verify GET /predict/colleges/{college_code}/branches against
cutoff_lookup_2026.csv for every college.

Imports the endpoint's in-memory mapping directly (no HTTP).
Run from backend/:  python scripts/verify_branch_endpoint.py
"""

import sys
import types
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data" / "cleaned"
sys.path.insert(0, str(BACKEND_DIR))

# slowapi may be missing locally (prod-only dep); routes.predict imports it
try:
    import slowapi  # noqa: F401
except ImportError:
    slowapi = types.ModuleType("slowapi")

    class _Limiter:
        def __init__(self, key_func=None):
            pass

        def limit(self, *a, **k):
            def deco(f):
                return f
            return deco

    slowapi.Limiter = _Limiter
    util = types.ModuleType("slowapi.util")
    util.get_remote_address = lambda r: "127.0.0.1"
    sys.modules["slowapi"] = slowapi
    sys.modules["slowapi.util"] = util

from routes import predict  # noqa: E402

SPOT_CHECK = [1, 1207, 1210, 2626]


def main():
    # 1. ground truth from the CSV
    lookup = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv")
    csv_map = {}
    for ccode, bcode in zip(lookup["college_code"].astype(int),
                            lookup["branch_code"].astype(str)):
        csv_map.setdefault(ccode, set()).add(bcode)

    # 2. college names
    names_df = pd.read_csv(DATA_DIR / "college_codes.csv")
    names = dict(zip(names_df["college_code"].astype(int),
                     names_df["college_name_full"]))

    # 3. what the endpoint serves
    endpoint_map = predict._get_college_branch_map()

    mismatches = []
    empty_but_csv_has = []
    for ccode, csv_branches in sorted(csv_map.items()):
        ep_branches = {b["branch_code"]
                       for b in endpoint_map.get(ccode, [])}
        if ep_branches == csv_branches:
            continue
        missing = csv_branches - ep_branches   # CSV has, endpoint lacks
        extra = ep_branches - csv_branches     # endpoint has, CSV lacks
        mismatches.append((ccode, missing, extra))
        if not ep_branches:
            empty_but_csv_has.append(ccode)

    # endpoint colleges absent from CSV entirely
    extra_colleges = sorted(set(endpoint_map) - set(csv_map))

    # 4. report
    print(f"Total colleges in CSV checked: {len(csv_map)}")
    print(f"Total colleges served by endpoint: {len(endpoint_map)}")
    print(f"Colleges in endpoint but not CSV: {extra_colleges or 'none'}")
    print(f"Endpoint empty while CSV has branches: {empty_but_csv_has or 'none'}")
    print()

    # 5. spot checks
    print("=" * 70)
    print("SPOT CHECKS (CSV vs endpoint)")
    print("=" * 70)
    for ccode in SPOT_CHECK:
        name = names.get(ccode, "<name not in college_codes.csv>")
        csv_b = sorted(csv_map.get(ccode, set()))
        ep_b = sorted(b["branch_code"] for b in endpoint_map.get(ccode, []))
        print(f"\nCollege {ccode} — {name}")
        print(f"  CSV      ({len(csv_b):2d}): {csv_b}")
        print(f"  Endpoint ({len(ep_b):2d}): {ep_b}")
        print(f"  match: {set(csv_b) == set(ep_b)}")

    print()
    print("=" * 70)
    if not mismatches:
        print(f"PASS — all {len(csv_map)} colleges match")
        return 0
    print(f"FAIL — {len(mismatches)} mismatches found:")
    for ccode, missing, extra in mismatches:
        name = names.get(ccode, "?")
        if missing:
            print(f"  {ccode} {name}: endpoint MISSING {sorted(missing)}")
        if extra:
            print(f"  {ccode} {name}: endpoint EXTRA {sorted(extra)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
