"""
extract_codes.py
PickMySeat.AI — College & Course Code Extraction Script

Reads: PreProcessed DATA/College and course code.pdf
Writes to: data/
  - college_codes.csv  (college_code, college_name, college_type, district)
  - course_codes.csv   (branch_code, branch_name)

Usage:
    python extract_codes.py
"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
PDF_PATH   = Path(__file__).parent.parent.parent / "PreProcessed DATA" / "College and course code.pdf"
OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def norm(s) -> str:
    return re.sub(r"\s+", "", str(s).strip().lower()) if s else ""


def safe_int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def is_college_header(headers: list[str]) -> bool:
    joined = " ".join(norm(h) for h in headers)
    return "collegecode" in joined and ("collegename" in joined or "name" in joined)


def is_course_header(headers: list[str]) -> bool:
    joined = " ".join(norm(h) for h in headers)
    return ("branchcode" in joined or "coursecode" in joined) and (
        "branchname" in joined or "coursename" in joined or "name" in joined
    )


def find_col(headers: list[str], *keywords) -> int | None:
    for i, h in enumerate(headers):
        hn = norm(h)
        if all(k in hn for k in keywords):
            return i
    return None


# ── College table parser ──────────────────────────────────────────────────────

def parse_college_table(table: list[list]) -> list[dict]:
    if not table or len(table) < 2:
        return []
    raw = [str(h) if h else "" for h in table[0]]
    headers = raw

    i_code = find_col(headers, "college", "code") or find_col(headers, "code")
    i_name = find_col(headers, "college", "name") or find_col(headers, "name")
    i_type = find_col(headers, "type") or find_col(headers, "category")
    i_dist = find_col(headers, "district") or find_col(headers, "location")

    if None in (i_code, i_name):
        return []

    rows = []
    for row in table[1:]:
        if not row:
            continue
        code = safe_int(row[i_code] if i_code < len(row) else None)
        name = str(row[i_name]).strip() if i_name < len(row) and row[i_name] else None
        typ  = str(row[i_type]).strip() if i_type is not None and i_type < len(row) and row[i_type] else None
        dist = str(row[i_dist]).strip() if i_dist is not None and i_dist < len(row) and row[i_dist] else None

        if code is None or not name or name.lower() in ("none", ""):
            continue

        rows.append({
            "college_code": code,
            "college_name":  name,
            "college_type":  typ,
            "district":      dist,
        })
    return rows


# ── Course table parser ───────────────────────────────────────────────────────

def parse_course_table(table: list[list]) -> list[dict]:
    if not table or len(table) < 2:
        return []
    raw = [str(h) if h else "" for h in table[0]]
    headers = raw

    i_code = find_col(headers, "branch", "code") or find_col(headers, "course", "code") or find_col(headers, "code")
    i_name = find_col(headers, "branch", "name") or find_col(headers, "course", "name") or find_col(headers, "name")

    if None in (i_code, i_name):
        return []

    rows = []
    for row in table[1:]:
        if not row:
            continue
        code = str(row[i_code]).strip().upper() if i_code < len(row) and row[i_code] else None
        name = str(row[i_name]).strip() if i_name < len(row) and row[i_name] else None

        if not code or not name or name.lower() in ("none", ""):
            continue
        # Skip purely numeric "codes" — those are likely college codes on wrong table
        if code.isdigit():
            continue

        rows.append({
            "branch_code": code,
            "branch_name": name,
        })
    return rows


# ── Text fallback parsers ─────────────────────────────────────────────────────

def parse_text_colleges(text: str) -> list[dict]:
    """Fallback: parse lines like '1  Anna University - CEG  University  Chennai'"""
    rows = []
    for line in text.split("\n"):
        parts = line.split()
        if not parts:
            continue
        # First token must be an integer (college code)
        code = safe_int(parts[0])
        if code is None or code <= 0:
            continue
        # Rest of tokens form the name (at minimum 1 word)
        if len(parts) < 2:
            continue
        name = " ".join(parts[1:])
        rows.append({"college_code": code, "college_name": name, "college_type": None, "district": None})
    return rows


def parse_text_courses(text: str) -> list[dict]:
    """Fallback: parse lines like 'CS  Computer Science and Engineering'"""
    rows = []
    for line in text.split("\n"):
        parts = line.split(None, 1)  # split into max 2 parts
        if len(parts) < 2:
            continue
        code = parts[0].strip().upper()
        name = parts[1].strip()
        # Branch codes are 2–4 alpha chars
        if not re.match(r"^[A-Z]{2,4}$", code):
            continue
        rows.append({"branch_code": code, "branch_name": name})
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("PickMySeat.AI — College & Course Code Extraction")
    print("=" * 60)
    print(f"\nReading: {PDF_PATH}")

    if not PDF_PATH.exists():
        print(f"❌ File not found: {PDF_PATH}")
        return

    college_rows = []
    course_rows  = []

    with pdfplumber.open(str(PDF_PATH)) as pdf:
        total = len(pdf.pages)
        print(f"Pages: {total}\n")

        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    raw_headers = [str(h) if h else "" for h in table[0]]

                    if is_college_header(raw_headers):
                        parsed = parse_college_table(table)
                        college_rows.extend(parsed)
                        if parsed:
                            print(f"  Page {i+1}: +{len(parsed)} colleges (table)")
                    elif is_course_header(raw_headers):
                        parsed = parse_course_table(table)
                        course_rows.extend(parsed)
                        if parsed:
                            print(f"  Page {i+1}: +{len(parsed)} courses (table)")
                    else:
                        # Unknown table — try both parsers
                        c = parse_college_table(table)
                        b = parse_course_table(table)
                        if c:
                            college_rows.extend(c)
                            print(f"  Page {i+1}: +{len(c)} colleges (auto-detected)")
                        if b:
                            course_rows.extend(b)
                            print(f"  Page {i+1}: +{len(b)} courses (auto-detected)")
            else:
                # No tables — fall back to text parsing
                text = page.extract_text() or ""
                text_lower = text.lower()

                if "college code" in text_lower or "college name" in text_lower:
                    parsed = parse_text_colleges(text)
                    college_rows.extend(parsed)
                    if parsed:
                        print(f"  Page {i+1}: +{len(parsed)} colleges (text fallback)")
                elif "branch code" in text_lower or "course code" in text_lower:
                    parsed = parse_text_courses(text)
                    course_rows.extend(parsed)
                    if parsed:
                        print(f"  Page {i+1}: +{len(parsed)} courses (text fallback)")

    # ── Deduplicate & save ────────────────────────────────────────────────────

    print("\n[college_codes.csv]")
    if college_rows:
        df = pd.DataFrame(college_rows).drop_duplicates(subset=["college_code"])
        df = df.sort_values("college_code").reset_index(drop=True)
        out = OUTPUT_DIR / "college_codes.csv"
        df.to_csv(out, index=False)
        print(f"  ✅ {len(df)} colleges → {out}")
        print(df.head(5).to_string(index=False))
    else:
        print("  ⚠️  No college rows extracted")

    print("\n[course_codes.csv]")
    if course_rows:
        df = pd.DataFrame(course_rows).drop_duplicates(subset=["branch_code"])
        df = df.sort_values("branch_code").reset_index(drop=True)
        out = OUTPUT_DIR / "course_codes.csv"
        df.to_csv(out, index=False)
        print(f"  ✅ {len(df)} branches → {out}")
        print(df.head(5).to_string(index=False))
    else:
        print("  ⚠️  No course rows extracted")

    print("\n" + "=" * 60)
    print("Done. Check data/ folder.")
    print("=" * 60)


if __name__ == "__main__":
    main()
