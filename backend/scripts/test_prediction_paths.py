"""
test_prediction_paths.py

PICKMYSEAT.AI — INTERACTIVE PREDICTION PATHS

Lets you pick one of 4 real prediction use cases and run it against the
production rank model (rank_model_final.pkl) + 2026 cutoff lookup.

    PATH 1  Find colleges & courses        (marks + community)
    PATH 2  Find best course in a college   (marks + community + college)
    PATH 3  Find colleges for a course      (marks + community + course)
    PATH 4  Check probability for an exact  (marks + community + college + course)

Rank is OPTIONAL in every path: leave it blank and it is predicted from
marks + community; type a number to use your own.

Run from: C:/Users/CHARANJAGAN/TNEA/TNEA_Predictor/
    python backend/scripts/test_prediction_paths.py
"""

import sys
import io
import pandas as pd
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"
sys.path.insert(0, str(BASE_DIR))

from utils.ml_utils import predict_rank
from utils.predict_colleges import predict_colleges, TIER_RANK

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]
W = 64  # box inner width

# ──────────────────────────────────────────────────────────────────────────────
# DATA (loaded once)
# ──────────────────────────────────────────────────────────────────────────────
_DATA = {}


def _data():
    if not _DATA:
        lk = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv")
        lk["community"] = lk["community"].replace("BCM", "BC")
        lk["branch_code"] = lk["branch_code"].astype(str)
        cc = pd.read_csv(DATA_DIR / "college_codes.csv")
        cr = pd.read_csv(DATA_DIR / "course_codes.csv")
        cr["branch_code"] = cr["branch_code"].astype(str)
        _DATA["lookup"] = lk
        _DATA["colleges"] = cc
        _DATA["college_map"] = cc.set_index("college_code").to_dict("index")
        _DATA["courses"] = cr
        _DATA["branch_map"] = dict(zip(cr["branch_code"], cr["branch_name"]))
    return _DATA


def college_name(code):
    info = _data()["college_map"].get(int(code))
    return info["college_name_short"] if info else f"College {code}"


def college_name_full(code):
    info = _data()["college_map"].get(int(code))
    return info["college_name_full"] if info else f"College {code}"


def college_tier(code):
    info = _data()["college_map"].get(int(code))
    return TIER_RANK.get(info["college_type"], 9) if info else 9


def branch_name(code):
    return _data()["branch_map"].get(str(code), f"Branch {code}")


# ──────────────────────────────────────────────────────────────────────────────
# DISPLAY HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def box_top():
    print("┌" + "─" * (W + 2) + "┐")


def box_bottom():
    print("└" + "─" * (W + 2) + "┘")


def box_line(text=""):
    # truncate visually-long lines so the box stays aligned
    for chunk in _wrap(text, W):
        print("│ " + chunk.ljust(W) + " │")


def _wrap(text, width):
    if text == "":
        return [""]
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def header(text):
    print("\n╔" + "═" * (W + 2) + "╗")
    print("║ " + text.center(W) + " ║")
    print("╚" + "═" * (W + 2) + "╝")


# ──────────────────────────────────────────────────────────────────────────────
# PROBABILITY MODEL
# ──────────────────────────────────────────────────────────────────────────────
def calc_probability(student_rank, closing_rank):
    """
    Returns (percent, status_label, emoji).

    diff = closing_rank - student_rank  (positive => student is better placed).
      diff >= 1000  -> 95%  VERY LIKELY
      0 <= diff      -> 85%  LIKELY
      deficit <= 500 -> 60%  MARGINAL
      deficit <=1000 -> 25%  RISKY
      else           ->  5%  VERY RISKY
    """
    diff = closing_rank - student_rank
    if diff >= 1000:
        return 95, "VERY LIKELY", "✅"
    if diff >= 0:
        return 85, "LIKELY", "✅"
    deficit = -diff
    if deficit <= 500:
        return 60, "MARGINAL", "⚠️"
    if deficit <= 1000:
        return 25, "RISKY", "⚠️"
    return 5, "VERY RISKY", "❌"


# ──────────────────────────────────────────────────────────────────────────────
# INPUT HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def get_marks_and_community():
    while True:
        try:
            marks = float(input("\n📍 Enter marks (0-200): ").strip())
            if 0 <= marks <= 200:
                break
            print("   ❌ Must be between 0 and 200")
        except ValueError:
            print("   ❌ Enter a valid number")

    print(f"\n📍 Community options: {', '.join(COMMUNITIES)}")
    while True:
        comm = input("   Enter community (OC/BC/SC/ST/MBC/SCA): ").strip().upper()
        if comm == "BCM":
            comm = "BC"
        if comm in COMMUNITIES:
            break
        print(f"   ❌ Choose from: {', '.join(COMMUNITIES)}")
    return marks, comm


def get_rank_input():
    """Return int rank, or None if the user skipped."""
    while True:
        raw = input("\n📍 Enter your rank (optional, press Enter to skip): ").strip()
        if raw == "":
            return None
        try:
            rank = int(raw.replace(",", ""))
            if rank >= 1:
                return rank
            print("   ❌ Rank must be 1 or higher")
        except ValueError:
            print("   ❌ Enter a whole number, or press Enter to skip")


def predict_or_use_rank(marks, community, rank_input):
    """
    Resolve the rank to use. Never rejected for a missing rank.

    Returns (rank, source_line) where source_line is ready-to-print.
    """
    if rank_input is not None:
        return rank_input, f"Using your input rank: {rank_input:,}"
    rk = predict_rank(marks, community)
    if "error" in rk:
        raise ValueError(rk["error"])
    r = rk["predicted_rank"]
    return r, (f"Predicted Rank: {r:,} "
               f"(±{(rk['range_max'] - r)}, Confidence: {rk['confidence']}%)")


def _search_and_pick(query, df, code_col, name_col, label):
    matches = df[df[name_col].str.contains(query, case=False, na=False)]
    if matches.empty:
        print(f"   ❌ No {label} matched '{query}'.")
        return None
    rows = matches.head(30).reset_index(drop=True)
    if len(rows) == 1:
        row = rows.iloc[0]
        print(f"   ✓ {row[name_col]}")
        return row[code_col], row[name_col]

    print(f"\n   Multiple {label}s matched '{query}':")
    for i, row in rows.iterrows():
        print(f"     {i + 1:>2}. {row[name_col]}")
    while True:
        sel = input(f"   Pick a {label} (1-{len(rows)}): ").strip()
        try:
            idx = int(sel) - 1
            if 0 <= idx < len(rows):
                row = rows.iloc[idx]
                return row[code_col], row[name_col]
            print("   ❌ Out of range")
        except ValueError:
            print("   ❌ Enter a number")


def get_college_choice():
    d = _data()
    while True:
        q = input("\n📍 Enter college name (or part of it): ").strip()
        if not q:
            print("   ❌ Type something to search")
            continue
        res = _search_and_pick(q, d["colleges"], "college_code",
                               "college_name_full", "college")
        if res:
            return res  # (college_code, college_name_full)


def get_course_choice():
    d = _data()
    while True:
        q = input("\n📍 Enter course name (or part of it): ").strip()
        if not q:
            print("   ❌ Type something to search")
            continue
        res = _search_and_pick(q, d["courses"], "branch_code",
                               "branch_name", "course")
        if res:
            return res  # (branch_code, branch_name)


# ──────────────────────────────────────────────────────────────────────────────
# RESULT DISPLAYS
# ──────────────────────────────────────────────────────────────────────────────
def display_path_1_results(rank_line, recs):
    box_top()
    box_line(rank_line)
    box_line()
    box_line("TOP 5 COLLEGES YOU CAN GET:")
    box_line()
    if not recs:
        box_line("No attainable colleges found for this rank.")
        box_bottom()
        return
    for c in recs:
        box_line(f"{c['rank']}. {c['college_name']}")
        box_line(f"   Course      : {c['branch_name']}")
        box_line(f"   Closing Rank: {c['closing_rank']:,}")
        box_line(f"   Probability : {c['match_confidence']}%")
        box_line(f"   Status      : {c['status']}")
        box_line()
    box_bottom()


def display_path_2_results(rank, college, courses):
    box_top()
    box_line(f"Your Rank: {rank:,}")
    box_line(f"College  : {college}")
    box_line()
    box_line("BEST COURSES FOR YOU (in order):")
    box_line()
    if not courses:
        box_line("No courses found for this college / community.")
        box_bottom()
        return
    for i, c in enumerate(courses, 1):
        box_line(f"{i}. {c['name']}")
        box_line(f"   Closing Rank: {c['closing']:,}")
        box_line(f"   Probability : {c['prob']}%")
        box_line(f"   Status      : {c['emoji']} {c['label']}")
        box_line()
    box_bottom()


def display_path_3_results(rank, course, colleges):
    box_top()
    box_line(f"Your Rank: {rank:,}")
    box_line(f"Course   : {course}")
    box_line()
    box_line("TOP COLLEGES OFFERING THIS COURSE:")
    box_line()
    if not colleges:
        box_line("No colleges found offering this course / community.")
        box_bottom()
        return
    for i, c in enumerate(colleges, 1):
        box_line(f"{i}. {c['name']}")
        box_line(f"   Closing Rank: {c['closing']:,}")
        box_line(f"   Probability : {c['prob']}%")
        box_line(f"   Status      : {c['emoji']} {c['label']}")
        box_line()
    box_bottom()


def display_path_4_results(college, course, rank, closing, prob, label, emoji):
    diff = closing - rank
    if diff >= 0:
        diff_line = f"Rank Difference: +{diff:,} (Your favor)"
    else:
        diff_line = f"Rank Difference: {diff:,} (Against you)"

    box_top()
    box_line("YOUR CHOICE ANALYSIS")
    box_line()
    box_line(f"College: {college}")
    box_line(f"Course : {course}")
    box_line()
    box_line(f"Your Rank   : {rank:,}")
    box_line(f"Closing Rank: {closing:,}")
    box_line(diff_line)
    box_line()
    box_line(f"PROBABILITY: {prob}% {emoji} {label}")
    box_line()
    box_line("Analysis:")
    for line in _path4_analysis(diff, prob):
        box_line(f"   {line}")
    box_line()
    box_line(f"Recommendation: {_path4_reco(prob)}")
    box_bottom()


def _path4_analysis(diff, prob):
    if prob >= 95:
        return ["✅ Your rank is well below the closing rank",
                "✅ Large safety margin",
                "✅ Highly confident prediction"]
    if prob >= 85:
        return ["✅ Your rank clears the closing rank",
                "⚠️  Safety margin is modest",
                "✅ Good chance overall"]
    if prob >= 60:
        return ["⚠️  Your rank is just past the closing rank",
                "⚠️  Small deficit — competition dependent",
                "➖ Treat as a stretch option"]
    if prob >= 25:
        return ["⚠️  Your rank trails the closing rank",
                "❌ Sizable deficit",
                "➖ Keep safer backups ready"]
    return ["❌ Your rank is far above the closing rank",
            "❌ Very large deficit",
            "❌ Low-confidence outcome"]


def _path4_reco(prob):
    if prob >= 95:
        return "Apply confidently!"
    if prob >= 85:
        return "Strong choice — apply."
    if prob >= 60:
        return "Apply, but list safer backups too."
    if prob >= 25:
        return "Risky — use only as a reach option."
    return "Unlikely — prefer other options."


# ──────────────────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────────────────
def path_1():
    header("PATH 1: FIND COLLEGES & COURSES")
    marks, comm = get_marks_and_community()
    rank_input = get_rank_input()
    rank, rank_line = predict_or_use_rank(marks, comm, rank_input)

    if rank_input is None:
        # full model pipeline already uses predicted rank internally
        result = predict_colleges(marks, comm, top_n=5)
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        recs = result["recommendations"]
        for r in recs:                       # prefer compact short names
            r["college_name"] = college_name(r["college_code"])
    else:
        # honour the user-supplied rank against the 2026 lookup directly
        recs = _recs_for_rank(rank, comm, top_n=5)

    print("\n⏳ Finding your best colleges...\n")
    display_path_1_results(rank_line, recs)


def _recs_for_rank(rank, comm, top_n=5):
    """Build path-1 style recommendations for an explicit rank."""
    d = _data()
    df = d["lookup"]
    df = df[(df["community"] == comm) &
            (df["predicted_closing_rank_2026"] >= rank)].copy()
    df["tier"] = df["college_code"].apply(college_tier)
    df = df.sort_values(["tier", "predicted_closing_rank_2026"]).head(top_n)
    recs = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        closing = int(row["predicted_closing_rank_2026"])
        prob, label, _ = calc_probability(rank, closing)
        recs.append({
            "rank": i,
            "college_name": college_name(row["college_code"]),
            "branch_name": branch_name(row["branch_code"]),
            "closing_rank": closing,
            "match_confidence": prob,
            "status": label,
        })
    return recs


def path_2():
    header("PATH 2: FIND BEST COURSE IN A COLLEGE")
    marks, comm = get_marks_and_community()
    rank_input = get_rank_input()
    rank, rank_line = predict_or_use_rank(marks, comm, rank_input)
    print(f"\n   {rank_line}")

    ccode, cname = get_college_choice()

    d = _data()
    df = d["lookup"]
    df = df[(df["college_code"] == ccode) & (df["community"] == comm)].copy()

    courses = []
    for _, row in df.iterrows():
        closing = int(row["predicted_closing_rank_2026"])
        prob, label, emoji = calc_probability(rank, closing)
        courses.append({
            "name": branch_name(row["branch_code"]),
            "closing": closing, "prob": prob, "label": label, "emoji": emoji,
        })
    # best probability first, then most competitive (lowest closing) course
    courses.sort(key=lambda c: (-c["prob"], c["closing"]))

    print("\n⏳ Ranking courses in this college...\n")
    display_path_2_results(rank, college_name(ccode), courses)


def path_3():
    header("PATH 3: FIND COLLEGES FOR A COURSE")
    marks, comm = get_marks_and_community()
    rank_input = get_rank_input()
    rank, rank_line = predict_or_use_rank(marks, comm, rank_input)
    print(f"\n   {rank_line}")

    bcode, bname = get_course_choice()

    d = _data()
    df = d["lookup"]
    df = df[(df["branch_code"] == str(bcode)) & (df["community"] == comm)].copy()

    colleges = []
    for _, row in df.iterrows():
        closing = int(row["predicted_closing_rank_2026"])
        prob, label, emoji = calc_probability(rank, closing)
        colleges.append({
            "name": college_name(row["college_code"]),
            "closing": closing, "prob": prob, "label": label, "emoji": emoji,
            "tier": college_tier(row["college_code"]),
        })
    # best probability first, then college prestige tier
    colleges.sort(key=lambda c: (-c["prob"], c["tier"], c["closing"]))

    print("\n⏳ Finding colleges for this course...\n")
    display_path_3_results(rank, bname, colleges[:10])


def path_4():
    header("PATH 4: CHECK PROBABILITY FOR EXACT CHOICE")
    marks, comm = get_marks_and_community()
    rank_input = get_rank_input()
    rank, rank_line = predict_or_use_rank(marks, comm, rank_input)
    print(f"\n   {rank_line}")

    ccode, cname = get_college_choice()
    bcode, bname = get_course_choice()

    d = _data()
    df = d["lookup"]
    match = df[(df["college_code"] == ccode) &
               (df["branch_code"] == str(bcode)) &
               (df["community"] == comm)]

    if match.empty:
        print("\n❌ No 2026 cutoff on record for that exact "
              "college + course + community combination.")
        print("   (This branch may not be offered there for your community.)")
        return

    closing = int(match.iloc[0]["predicted_closing_rank_2026"])
    prob, label, emoji = calc_probability(rank, closing)

    print("\n⏳ Analysing your exact choice...\n")
    display_path_4_results(college_name(ccode), bname, rank,
                           closing, prob, label, emoji)


# ──────────────────────────────────────────────────────────────────────────────
# MENU
# ──────────────────────────────────────────────────────────────────────────────
def display_menu():
    print("\n╔" + "═" * (W + 2) + "╗")
    print("║ " + "PICKMYSEAT.AI — PREDICTION PATHS".center(W) + " ║")
    print("║ " + " ".center(W) + " ║")
    print("║ " + "Choose what you want to predict:".center(W) + " ║")
    print("╚" + "═" * (W + 2) + "╝")
    print("""
1️⃣   PATH 1: FIND COLLEGES & COURSES
     Input : Marks + Community (+ optional Rank)
     Output: Top colleges & courses with probability
     "I have marks, what colleges can I get?"

2️⃣   PATH 2: FIND BEST COURSE IN A COLLEGE
     Input : Marks + Community + College (+ optional Rank)
     Output: Best course in that college + probability
     "I want NIT Trichy, which course should I choose?"

3️⃣   PATH 3: FIND COLLEGES FOR A COURSE
     Input : Marks + Community + Course (+ optional Rank)
     Output: Top colleges offering that course + probability
     "I want CSE, which colleges can I get?"

4️⃣   PATH 4: CHECK PROBABILITY FOR EXACT CHOICE
     Input : Marks + Community + College + Course (+ optional Rank)
     Output: Probability of that exact college-course combo
     "What are my chances of NIT Trichy CSE?"

5️⃣   Exit
""")


def get_user_choice():
    return input("   Enter choice (1-5): ").strip()


def main():
    print("\n⏳ Loading models and data...")
    _data()           # warm the CSV cache
    predict_rank(180, "OC")  # warm the rank model
    print("✅ Ready.\n")

    paths = {"1": path_1, "2": path_2, "3": path_3, "4": path_4}

    while True:
        display_menu()
        choice = get_user_choice()

        if choice == "5":
            print("\n👋 Thank you for using PickMySeat.AI!")
            break
        if choice not in paths:
            print("   ❌ Invalid choice. Pick 1-5.")
            continue

        try:
            paths[choice]()
        except KeyboardInterrupt:
            print("\n   ↩  Cancelled, back to menu.")
            continue
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        again = input("\n🔄 Try another path? (y/n): ").strip().lower()
        if again != "y":
            print("\n👋 Thank you for using PickMySeat.AI!")
            break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")
