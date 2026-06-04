"""
test_hybrid_interactive.py

Interactive test for hybrid TNEA rank prediction.

Run from project root:
    python backend/scripts/test_hybrid_interactive.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.ml_utils import predict_rank_hybrid

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]


def main():
    print("=" * 80)
    print("HYBRID TNEA RANK PREDICTOR — INTERACTIVE TEST")
    print("=" * 80)
    print("\nThis model predicts your rank based on:")
    print("  • Your aggregate marks (0-200)")
    print("  • Your community category")
    print("  • Historical trends from 2022-2024 data")
    print("\nOutput includes:")
    print("  • Most likely rank")
    print("  • Confidence range (±50-100 ranks)")
    print("  • Confidence score")
    print("  • Historical basis for prediction\n")

    while True:
        try:
            # Get marks
            while True:
                try:
                    mark_input = input("Enter aggregate marks (0-200): ").strip()
                    mark = float(mark_input)
                    if 0 <= mark <= 200:
                        break
                    print("❌ Must be between 0 and 200")
                except ValueError:
                    print("❌ Enter a valid number")

            # Get community
            while True:
                comm_input = input(f"Enter community ({'/'.join(COMMUNITIES)}): ").strip().upper()
                if comm_input == "BCM":
                    comm_input = "BC"
                    print("  (BCM normalized to BC)")
                if comm_input in COMMUNITIES:
                    break
                print(f"❌ Choose from: {', '.join(COMMUNITIES)}")

            # Predict
            print("\n⏳ Computing prediction …\n")
            result = predict_rank_hybrid(mark, comm_input)

            # Display results
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print("=" * 80)
                print("PREDICTION RESULT")
                print("=" * 80)

                print(f"\n📊 INPUT")
                print(f"   Marks      : {result['mark']:.1f}/200")
                print(f"   Community  : {result['community']}")

                print(f"\n🎯 PREDICTION")
                print(f"   Most Likely Rank : {result['rank']:,}")
                print(f"   Prediction Range : {result['rank_min']:,} – {result['rank_max']:,}")
                print(f"   Confidence       : {result['confidence']}%")

                print(f"\n📈 BREAKDOWN")
                comp = result["components"]
                for key, val in comp.items():
                    if key not in ["mark_pred"]:
                        print(f"   {key.replace('_', ' ').title():<30} : {val}")

                if result["historical_cases"]:
                    print(f"\n📚 HISTORICAL BASIS")
                    for case in result["historical_cases"]:
                        print(f"   • {case}")

                print("\n" + "=" * 80)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        # Another prediction?
        print()
        if input("Make another prediction? (y/n): ").strip().lower() != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()