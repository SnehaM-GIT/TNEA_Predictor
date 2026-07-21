"""
extract_seat_matrix.py — parse the 2026 official seat matrix PDF into a flat CSV.

Source: data/raw/GENERAL_ACADEMIC_SEAT_MATRIX_BEFORE_SPECIAL_RESERVATION_COUNSELLING_2026.pdf
Table repeats per page with header
  COLLEGE CODE | COLLEGE NAME | BRANCH CODE | BRANCH NAME | OC BC BCM MBC SC SCA ST TOTAL
Output: data/cleaned/seat_matrix_2026.csv
  college_code, college_name, branch_code, branch_name, OC, BC, BCM, MBC, SC, SCA, ST, TOTAL
"""

import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "raw" / "GENERAL_ACADEMIC_SEAT_MATRIX_BEFORE_SPECIAL_RESERVATION_COUNSELLING_2026.pdf"
OUT_PATH = BASE_DIR / "data" / "cleaned" / "seat_matrix_2026.csv"

COMMUNITY_COLS = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
NUMERIC_COLS = COMMUNITY_COLS + ["TOTAL"]


def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _clean_branch_code(text):
    """Branch codes are always exactly 2 letters. Some source rows bleed a
    trailing '-' from the college address column (e.g. "...Kanchipuram-
    631604." wraps with the hyphen glued straight to the pincode, and
    pdfplumber's column-boundary detection drops that hyphen into the
    neighbouring branch_code cell instead of college_name) — giving
    "- AD" instead of "AD". Extracting the trailing 2-letter code recovers
    the real value regardless of what leaked in front of it."""
    cleaned = _clean(text)
    m = re.search(r"[A-Za-z]{2}$", cleaned)
    return m.group(0) if m else cleaned


def extract(pdf_path=PDF_PATH):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                for r in table[1:]:  # skip repeated header row
                    if not r or len(r) != 12:
                        continue
                    college_code, college_name, branch_code, branch_name, *nums = r
                    if not (college_code or "").strip().isdigit():
                        continue  # stray/merged row, skip
                    try:
                        nums = [int(_clean(n).replace(",", "")) for n in nums]
                    except (ValueError, TypeError):
                        continue  # malformed numeric row, skip
                    rows.append([
                        int(college_code.strip()),
                        _clean(college_name),
                        _clean_branch_code(branch_code),
                        _clean(branch_name),
                        *nums,
                    ])

    df = pd.DataFrame(
        rows,
        columns=["college_code", "college_name", "branch_code", "branch_name", *NUMERIC_COLS],
    )
    # some colleges list the same college_code+branch_code twice across page
    # breaks with identical data (table split); dedupe defensively.
    df = df.drop_duplicates(subset=["college_code", "branch_code", *NUMERIC_COLS])
    return df


if __name__ == "__main__":
    df = extract()
    print(f"parsed {len(df)} rows, {df['college_code'].nunique()} colleges, "
          f"{df['branch_code'].nunique()} distinct branch codes")
    df.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")
