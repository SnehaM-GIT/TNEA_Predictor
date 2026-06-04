"""
test_predict_interactive.py

Interactive test — enter marks + community, get predicted rank + top 5 colleges.

Run from project root:
    python backend/scripts/test_predict_interactive.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.ml_utils import predict_rank, predict_colleges, load_models

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]


def get_input():
    while True:
        try:
            marks = float(input("\nEnter aggregate marks (0-200): ").strip())
            if 0 <= marks <= 200:
                break
            print("❌ Must be between 0 and 200.")
        except ValueError:
            print("❌ Enter a number.")

    while True:
        community = input(f"Enter community ({'/'.join(COMMUNITIES)}): ").strip().upper()
        if community == "BCM":
            community = "BC"
        if community in COMMUNITIES:
            break
        print(f"❌ Choose from: {', '.join(COMMUNITIES)}")

    return marks, community


def show_results(marks, community, rank, colleges):
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📊 PREDICTED RANK")
    print(f"   Marks      : {marks:.1f}/200")
    print(f"   Community  : {community}")
    print(f"   Rank       : {rank:,}")

    print(f"\n🎓 TOP 5 COLLEGES")
    print("─" * 70)

    if not colleges:
        print("\n❌ No colleges found — rank may be too low.")
        return

    for i, c in enumerate(colleges, 1):
        prob = c["probability"]
        pct  = int(prob * 100)
        bar  = "█" * int(20 * prob) + "░" * (20 - int(20 * prob))

        if prob == 0.85:
            status = "✅ Likely"
        elif prob == 0.30:
            status = "⚠️  Risky"
        else:
            status = "❌ Unlikely"

        print(f"\n{i}. {c['college_name']}")
        print(f"   Branch       : {c['course_name']}")
        print(f"   Cutoff range : {c['opening_rank']:,} – {c['closing_rank']:,}")
        print(f"   Probability  : {bar} {pct}%  {status}")
        print(f"   Seats filled : {c['seats_filled']}")


def main():
    print("=" * 70)
    print("PICKMYSEAT.AI — PREDICTION TEST")
    print("=" * 70)

    print("\nLoading models …")
    load_models()
    print("✅ Models loaded")

    while True:
        try:
            marks, community = get_input()

            print("\n⏳ Predicting …")
            rank     = predict_rank(marks, community)
            colleges = predict_colleges(rank, community, limit=5)

            show_results(marks, community, rank, colleges)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

        print("\n" + "─" * 70)
        if input("Test another? (y/n): ").strip().lower() != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()