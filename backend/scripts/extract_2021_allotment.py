"""
extract_2021_allotment.py

Reads all 2021 allotment PDFs from backend/data/1.raw/
Extracts: college_code, branch_code, community, allotted_rank
Derives:  opening_rank, closing_rank, seats_filled per combo
Appends:  2021 rows to backend/data/2.cleaned/cutoffs.csv

Run from project root:
    python backend/scripts/extract_2021_allotment.py
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent          # backend/
RAW_DIR     = BASE_DIR / "data" / "raw"
CUTOFFS_CSV = BASE_DIR / "data" / "cleaned" / "cutoffs.csv"

KNOWN_COMMUNITIES = {'OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST'}

# ── Find 2021 allotment PDFs ─────────────────────────────────────────────────
all_pdfs = list(RAW_DIR.glob("*.pdf"))
round_pdfs = [
    p for p in all_pdfs
    if "2021" in p.name and "rank" not in p.name.lower()
]
round_pdfs.sort()

if not round_pdfs:
    print("❌  No 2021 allotment PDFs found in:", RAW_DIR)
    print("    Expected files like: 2021_round1.pdf, 2021_round2.pdf")
    raise SystemExit(1)

print(f"Found {len(round_pdfs)} PDF(s):")
for p in round_pdfs:
    print(f"  {p.name}")

# ── Helper: clean a cell ─────────────────────────────────────────────────────
def clean(cell):
    return str(cell).strip() if cell else ""

# ── Helper: is this a header / junk row? ────────────────────────────────────
HEADER_KEYWORDS = {
    "COLLEGE", "BRANCH", "COMMUNITY", "RANK", "APPLICATION",
    "NAME", "ALLOT", "SERIAL", "S.NO", "SL", "NO.",
}

def is_junk(row):
    text = " ".join(row).upper()
    return any(kw in text for kw in HEADER_KEYWORDS) or all(c == "" for c in row)

# ── Helper: parse one row → dict or None ────────────────────────────────────
def parse_row(row):
    rank_val = college_code = branch_code = community = None

    for cell in row:
        c = clean(cell)

        # Community
        if c.upper() in KNOWN_COMMUNITIES and community is None:
            community = "BC" if c.upper() == "BCM" else c.upper()
            continue

        # Allotted rank: 1–200000, pure integer
        if re.fullmatch(r"\d{1,6}", c) and rank_val is None:
            v = int(c)
            if 1 <= v <= 200_000:
                rank_val = v
                continue

        # College code: 4-digit number used by TNEA
        if re.fullmatch(r"\d{4}", c) and college_code is None:
            college_code = c
            continue

        # Branch code: 2–3 digit number
        if re.fullmatch(r"\d{2,3}", c) and branch_code is None:
            branch_code = c
            continue

    if rank_val and college_code and branch_code and community:
        return {
            "college_code":  college_code,
            "branch_code":   branch_code,
            "community":     community,
            "allotted_rank": rank_val,
        }
    return None

# ── Extract all pages from all round PDFs ────────────────────────────────────
raw_rows  = []
debug_shown = False

for pdf_path in round_pdfs:
    print(f"\nReading: {pdf_path.name} …")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                for row in table:
                    row = [clean(c) for c in row]
                    if is_junk(row):
                        continue
                    raw_rows.append(row)

print(f"\nRaw rows extracted: {len(raw_rows):,}")

# Show first 5 rows always — helps verify parsing is correct
print("\nSample raw rows (first 5):")
for r in raw_rows[:5]:
    print(" ", r)

# ── Parse rows ───────────────────────────────────────────────────────────────
parsed = []
for row in raw_rows:
    result = parse_row(row)
    if result:
        parsed.append(result)

print(f"\nSuccessfully parsed: {len(parsed):,} rows")

if len(parsed) == 0:
    print("\n❌  Parser could not extract any rows.")
    print("    The PDF column layout may differ from the expected format.")
    print("    Copy the 'Sample raw rows' above and share them to fix the parser.")
    raise SystemExit(1)

# ── Build 2021 cutoffs ───────────────────────────────────────────────────────
df = pd.DataFrame(parsed)

print("\nCommunity counts:")
print(df["community"].value_counts().to_string())

cutoffs_2021 = (
    df.groupby(["college_code", "branch_code", "community"])
    .agg(
        opening_rank=("allotted_rank", "min"),
        closing_rank=("allotted_rank", "max"),
        seats_filled=("allotted_rank", "count"),
    )
    .reset_index()
)
cutoffs_2021["year"] = 2021

print(f"\n2021 cutoff combinations: {len(cutoffs_2021):,}")
print(cutoffs_2021.head(8).to_string(index=False))

# ── Append to cutoffs.csv ─────────────────────────────────────────────────────
existing = pd.read_csv(CUTOFFS_CSV)
print(f"\nExisting cutoffs.csv  : {len(existing):,} rows, years={sorted(existing['year'].unique())}")

# Drop any old 2021 rows
existing = existing[existing["year"] != 2021]

combined = (
    pd.concat([existing, cutoffs_2021], ignore_index=True)
    .sort_values(["year", "college_code", "branch_code", "community"])
    .reset_index(drop=True)
)

combined.to_csv(CUTOFFS_CSV, index=False)
print(f"Updated cutoffs.csv   : {len(combined):,} rows, years={sorted(combined['year'].unique())}")
print("\n✅  2021 allotment extraction complete!")
