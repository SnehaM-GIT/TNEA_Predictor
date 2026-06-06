"""
extract_tnea_data.py
PickMySeat.AI — TNEA Data Extraction Script

Extracts two CSVs from TNEA PDF data:
  - ranks.csv   : student rank data for XGBoost training
  - cutoffs.csv : college/branch opening+closing rank per year

Usage:
    python extract_tnea_data.py

PDFs expected in ../../TNEA_DATA/ relative to this script.
Output goes to ./output/
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent.parent.parent / "TNEA_DATA"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

YEARS = [2022, 2023, 2024, 2025]

COMMUNITY_ENCODE = {
    "OC": 0, "BC": 1, "BCM": 2, "MBC": 3,
    "SC": 4, "SCA": 5, "ST": 6,
}

VALID_CATEGORIES = set(COMMUNITY_ENCODE.keys())

# ── Helpers ───────────────────────────────────────────────────────────────────

def norm(s: str) -> str:
    """Normalize a header string: lowercase, remove all internal whitespace."""
    return re.sub(r"\s+", "", str(s).strip().lower()) if s else ""


def find_col(headers: list[str], *keywords) -> int | None:
    """Return first header index whose normalized form contains ALL keywords."""
    for i, h in enumerate(headers):
        hn = norm(h)
        if all(k in hn for k in keywords):
            return i
    return None


def safe_int(val) -> int | None:
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def safe_float(val) -> float | None:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def parse_table(table: list[list], year: int, source: str) -> list[dict]:
    """Generic dispatcher — detects table type from headers and parses."""
    if not table or len(table) < 2:
        return []
    raw_headers = [str(h) if h else "" for h in table[0]]
    headers = [norm(h) for h in raw_headers]

    # Detect table type
    has_rank      = find_col(headers, "rank") is not None
    has_aggregate = find_col(headers, "aggr") is not None or find_col(headers, "aggregate") is not None
    has_college   = find_col(headers, "college") is not None or find_col(headers, "allotted") is not None
    has_branch    = find_col(headers, "branch") is not None

    if has_rank and has_aggregate and not has_college:
        return parse_rank_table(table, headers, year)
    elif has_rank and has_college and has_branch:
        return parse_round_table(table, headers, year, source)
    return []


# ── Rank list table parser ────────────────────────────────────────────────────

def parse_rank_table(table, headers, year):
    """
    Headers (typical): RANK | APPLICATION NUMBER | NAME | DOB | AGGREGATE MARK | COMMUNITY | COMMUNITY RANK
    """
    i_rank = find_col(headers, "rank")
    # Exclude community rank — prefer bare "rank" without "community"
    for i, h in enumerate(headers):
        if "rank" in h and "community" not in h and "govt" not in h and "general" not in h:
            i_rank = i
            break

    i_app  = find_col(headers, "application") or find_col(headers, "appln") or find_col(headers, "appl")
    i_agg  = find_col(headers, "aggr") or find_col(headers, "aggregate")
    i_comm = None
    for i, h in enumerate(headers):
        if "commun" in h and "rank" not in h and "allotted" not in h:
            i_comm = i
            break

    if None in (i_rank, i_app, i_agg, i_comm):
        return []

    rows = []
    for row in table[1:]:
        if not row:
            continue
        rank  = safe_int(row[i_rank] if i_rank < len(row) else None)
        app   = safe_int(row[i_app]  if i_app  < len(row) else None)
        agg   = safe_float(row[i_agg] if i_agg  < len(row) else None)
        comm  = str(row[i_comm]).strip().upper() if i_comm < len(row) and row[i_comm] else None

        if None in (rank, app, agg) or comm not in VALID_CATEGORIES:
            continue

        rows.append({
            "rank":           rank,
            "app_no":         app,
            "aggregate_mark": agg,
            "community":      comm,
        })
    return rows


# ── Allotment round table parser ──────────────────────────────────────────────

def parse_round_table(table, headers, year, source):
    """
    Handles all round header variations:
      Round 1: APPLN NO | AGGR MARK | RANK | COMMUNITY | COLLEGE CODE | BRANCH CODE | ALLOTTED CATEGORY
      Round 2: APPLN NO | AGGREGATE MARK | COMMUNITY | RANK | ALLOTTED COLLEGE | BRANCH CODE | ALLOTTED CATEGORY
      Round 3: APPLN NUMBER | COMMUNITY | AGGR MARK | GENERAL RANK | GOVT RANK | COLLEGE CODE | BRANCH CODE | ALLOTTED CATEGORY
      2025 R1: APPLN NO | COMMUNITY | AGGREGATE MARK | RANK | COLLEGE CODE | BRANCH CODE | ALLOTTED COMMUNITY
    """
    i_app  = find_col(headers, "appln") or find_col(headers, "appl")
    i_agg  = find_col(headers, "aggr") or find_col(headers, "aggregate")

    # Rank: prefer "general rank" if present, else bare rank (not govt rank)
    i_rank = find_col(headers, "general", "rank")
    if i_rank is None:
        for i, h in enumerate(headers):
            if "rank" in h and "govt" not in h and "community" not in h:
                i_rank = i
                break

    # Community: first col with "commun" but not "allotted"
    i_comm = None
    for i, h in enumerate(headers):
        if "commun" in h and "allotted" not in h:
            i_comm = i
            break

    # College code: prefer "college code" or "allotted college"
    i_col = find_col(headers, "college", "code") or find_col(headers, "allotted", "college")
    if i_col is None:
        for i, h in enumerate(headers):
            if "college" in h:
                i_col = i
                break

    # Branch code
    i_branch = find_col(headers, "branch", "code") or find_col(headers, "branch")

    # Allotted category/community — last col with "allotted"
    i_allcat = None
    for i in range(len(headers) - 1, -1, -1):
        if "allotted" in headers[i] or ("commun" in headers[i] and i > (i_comm or 0)):
            i_allcat = i
            break

    if None in (i_rank, i_col, i_branch, i_allcat):
        return []

    rows = []
    for row in table[1:]:
        if not row:
            continue

        def get(idx):
            return row[idx] if idx is not None and idx < len(row) else None

        rank     = safe_int(get(i_rank))
        col_code = safe_int(get(i_col))
        branch   = str(get(i_branch)).strip().upper() if get(i_branch) else None
        allot    = str(get(i_allcat)).strip().upper() if get(i_allcat) else None
        app_no   = safe_int(get(i_app))
        agg      = safe_float(get(i_agg))
        comm_raw = get(i_comm)
        comm     = str(comm_raw).strip().upper() if comm_raw else None

        if None in (rank, col_code, branch, allot):
            continue
        if not branch or not allot:
            continue
        if allot not in VALID_CATEGORIES:
            continue

        rows.append({
            "app_no":           app_no,
            "rank":             rank,
            "aggregate_mark":   agg,
            "community":        comm,
            "college_code":     col_code,
            "branch_code":      branch,
            "allotted_category": allot,
        })
    return rows


# ── Extract one PDF ───────────────────────────────────────────────────────────

def extract_pdf(path: Path, year: int, source_label: str) -> list[dict]:
    rows = []
    with pdfplumber.open(str(path)) as pdf:
        total = len(pdf.pages)
        print(f"    {total} pages", flush=True)
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                parsed = parse_table(table, year, source_label)
                rows.extend(parsed)
            if (i + 1) % 200 == 0:
                print(f"    ... {i+1}/{total} pages | {len(rows)} rows", flush=True)
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("PickMySeat.AI — TNEA Data Extraction")
    print("=" * 60)

    all_rank_rows = []
    all_allot_rows = []

    for year in YEARS:
        print(f"\n── {year} ──────────────────────────────────")

        # Rank list
        rank_path = DATA_DIR / f"{year}_rank.pdf"
        if rank_path.exists():
            print(f"  [rank] {rank_path.name}")
            rows = extract_pdf(rank_path, year, "rank")
            for r in rows:
                r["year"] = year
            print(f"  → {len(rows):,} students")
            all_rank_rows.extend(rows)
        else:
            print(f"  [SKIP] {rank_path.name} not found")

        # Allotment rounds
        for rnd in [1, 2, 3, 4]:
            rnd_path = DATA_DIR / f"{year}_round{rnd}.pdf"
            if rnd_path.exists():
                print(f"  [round{rnd}] {rnd_path.name}")
                rows = extract_pdf(rnd_path, year, f"round{rnd}")
                for r in rows:
                    r["year"] = year
                    r["round"] = rnd
                print(f"  → {len(rows):,} allotments")
                all_allot_rows.extend(rows)

    # ── Save ranks.csv ──
    print("\n[ranks.csv]")
    if all_rank_rows:
        ranks_df = pd.DataFrame(all_rank_rows)
        ranks_df["year_normalized"]   = ranks_df["year"] - 2022
        ranks_df["community_encoded"] = ranks_df["community"].map(COMMUNITY_ENCODE)
        ranks_df = ranks_df[["rank", "app_no", "aggregate_mark", "community",
                              "community_encoded", "year", "year_normalized"]]
        ranks_df = ranks_df.sort_values(["year", "rank"]).reset_index(drop=True)
        out = OUTPUT_DIR / "ranks.csv"
        ranks_df.to_csv(out, index=False)
        print(f"  ✅ {len(ranks_df):,} rows → {out}")
        print(ranks_df.head(3).to_string(index=False))
    else:
        print("  ⚠️  No rank rows extracted")

    # ── Save cutoffs.csv ──
    print("\n[cutoffs.csv]")
    if all_allot_rows:
        allot_df = pd.DataFrame(all_allot_rows)
        cutoffs = (
            allot_df
            .groupby(["college_code", "branch_code", "allotted_category", "year"], as_index=False)
            .agg(
                opening_rank=("rank", "min"),
                closing_rank=("rank", "max"),
                seats_filled=("rank", "count"),
            )
            .sort_values(["year", "college_code", "branch_code", "allotted_category"])
            .reset_index(drop=True)
        )
        out = OUTPUT_DIR / "cutoffs.csv"
        cutoffs.to_csv(out, index=False)
        print(f"  ✅ {len(cutoffs):,} rows → {out}")
        print(cutoffs.head(3).to_string(index=False))
    else:
        print("  ⚠️  No allotment rows extracted")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
