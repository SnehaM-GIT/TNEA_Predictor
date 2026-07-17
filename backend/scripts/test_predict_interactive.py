"""
test_interactive.py

INTERACTIVE TNEA RANK & COLLEGE PREDICTOR

Test the rank model and college prediction system end-to-end.

Run from: C:/Users/CHARANJAGAN/TNEA/TNEA_Predictor/
    python backend/scripts/test_predict_interactive.py
"""

import sys
import io
import pandas as pd
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.ml_utils import predict_rank
from utils.predict_colleges import predict_colleges

COMMUNITIES = ["OC", "BC", "SC", "ST", "MBC", "SCA"]

def print_header(text):
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80)

def print_section(text):
    print(f"\n{text}")
    print("─" * 80)

def main():
    print_header("TNEA RANK & COLLEGE PREDICTOR (Interactive Test)")
    
    print("""
This tool predicts your expected TNEA rank and top 5 colleges based on:
  • Aggregate marks (0-200)
  • Community category (OC, BC, SC, ST, MBC, SCA)
  • Historical data from 2022-2026
  
Predictions are based on Method 3 (Rank Distribution + Cutoff Patterns)
    """)

    while True:
        try:
            print_section("STEP 1: ENTER YOUR DETAILS")
            
            # Get marks
            while True:
                try:
                    mark_input = input("\n📍 Aggregate marks (0-200): ").strip()
                    mark = float(mark_input)
                    if 0 <= mark <= 200:
                        break
                    print("   ❌ Must be between 0 and 200")
                except ValueError:
                    print("   ❌ Enter a valid number")

            # Get community
            print(f"\n📍 Community options: {', '.join(COMMUNITIES)}")
            while True:
                comm = input("   Enter community: ").strip().upper()
                if comm == "BCM":
                    comm = "BC"
                if comm in COMMUNITIES:
                    break
                print(f"   ❌ Choose from: {', '.join(COMMUNITIES)}")

            print("\n⏳ Calculating rank prediction...")
            print_section("STEP 2: YOUR PREDICTED RANK")
            
            # Get rank prediction
            rank_result = predict_rank(mark, comm)
            
            if "error" in rank_result:
                print(f"❌ Error: {rank_result['error']}")
                continue
            
            predicted_rank = rank_result["predicted_rank"]
            range_min = rank_result["range_min"]
            range_max = rank_result["range_max"]
            confidence = rank_result["confidence"]
            
            print(f"""
📊 YOUR PREDICTION DETAILS:
   Marks         : {mark}/200
   Community     : {comm}
   
🎯 PREDICTED RANK
   Most Likely   : {predicted_rank:,}
   Confidence Range : {range_min:,} – {range_max:,} (±100)
   Confidence    : {confidence}%
   
ℹ️  This means you're likely to get rank between {range_min:,} and {range_max:,}
            """)
            
            print("\n⏳ Finding top 5 colleges...")
            print_section("STEP 3: TOP 5 COLLEGES YOU'LL GET")
            
            # Get college predictions
            college_result = predict_colleges(mark, comm, top_n=5)
            
            if "error" in college_result:
                print(f"❌ Error: {college_result['error']}")
                continue
            
            recommendations = college_result["recommendations"]
            
            if not recommendations:
                print("""
❌ NO COLLEGES FOUND

Your predicted rank is too high (worse) for available options.
Try retaking the exam or look for more colleges in your range.
                """)
                continue
            
            # Display results
            print(f"\n✅ Found {len(recommendations)} colleges for you:\n")
            
            for idx, college in enumerate(recommendations, 1):
                college_name = college["college_name"]
                college_type = college["college_type"]
                district = college["college_district"]
                branch_name = college["branch_name"]
                closing_rank = college["closing_rank"]
                safety_margin = college["safety_margin"]
                status = college["status"]
                confidence = college["match_confidence"]
                
                # Status emoji
                if status == "SAFE":
                    status_emoji = "✅ SAFE"
                elif status == "MARGINAL":
                    status_emoji = "⚠️  MARGINAL"
                else:
                    status_emoji = "❌ WON'T GET"
                
                print(f"""
{idx}. {college_name}
   Type         : {college_type}
   Location     : {district}
   Branch       : {branch_name}
   Closing Rank : {closing_rank:,}
   Your Rank    : {predicted_rank:,}
   Margin       : {safety_margin:+,} ranks ({status_emoji})
   Match Confidence : {confidence}%
""")
            
            print_section("SUMMARY")
            safe_count = sum(1 for c in recommendations if c["status"] == "SAFE")
            marginal_count = sum(1 for c in recommendations if c["status"] == "MARGINAL")
            
            print(f"""
📈 ANALYSIS:
   Safe Colleges    : {safe_count} (Closing rank >> Your rank)
   Marginal Colleges: {marginal_count} (Closing rank ≈ Your rank)
   
💡 RECOMMENDATION:
   • SAFE colleges: Apply confidently
   • MARGINAL colleges: Apply with caution (risky)
   • Also apply to more colleges below this list as backup
   
⚠️  Note: These predictions are based on 2022-2026 patterns.
   Actual 2026 closing ranks may vary based on competition level.
            """)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        # Ask to continue
        print("\n")
        again = input("🔄 Make another prediction? (y/n): ").strip().lower()
        if again != "y":
            print("\n👋 Thank you for using TNEA Predictor!")
            break

if __name__ == "__main__":
    main()