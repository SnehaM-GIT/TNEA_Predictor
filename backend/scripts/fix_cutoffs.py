"""
fix_cutoffs.py

Fixes two issues in cutoffs.csv:
  1. Merges 'community' and 'allotted_category' into one column
  2. Normalizes BCM → BC

Run from project root:
    python backend/scripts/fix_cutoffs.py
"""

import pandas as pd
from pathlib import Path
import sys
import io

# UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR    = Path(__file__).resolve().parent.parent / "data" / "cleaned"
CUTOFFS_CSV = DATA_DIR / "cutoffs.csv"

print("Loading cutoffs.csv …")
df = pd.read_csv(CUTOFFS_CSV)
print(f"Rows   : {len(df):,}")
print(f"Columns: {df.columns.tolist()}")

print(f"\nBefore fix:")
print(f"  community (NaN)         : {df['community'].isnull().sum():,}")
print(f"  allotted_category (NaN) : {df['allotted_category'].isnull().sum():,}")

# ── Merge the two columns into one ───────────────────────────────────────────
# community has 2021 data, allotted_category has 2022-2025 data
df["community"] = df["community"].fillna(df["allotted_category"])

# ── Normalize BCM → BC ────────────────────────────────────────────────────────
df["community"] = df["community"].replace("BCM", "BC")

# ── Drop allotted_category (no longer needed) ─────────────────────────────────
df = df.drop(columns=["allotted_category"])

# ── Verify ────────────────────────────────────────────────────────────────────
print(f"\nAfter fix:")
print(f"  community (NaN)  : {df['community'].isnull().sum():,}")
print(f"\nCommunity distribution:")
print(df["community"].value_counts().to_string())

print(f"\nYear distribution:")
print(df["year"].value_counts().sort_index().to_string())

print(f"\nColumns now: {df.columns.tolist()}")

# ── Save ──────────────────────────────────────────────────────────────────────
df.to_csv(CUTOFFS_CSV, index=False)
print(f"\n[OK] cutoffs.csv fixed and saved! ({len(df):,} rows)")
