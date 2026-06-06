# PickMySeat.AI — TNEA Predictor Production Readiness Report

**Generated:** 2026-06-06  
**System:** TNEA 2026 Rank & College Prediction (PickMySeat.AI)  
**Branch:** main

---

## 1. EXECUTIVE SUMMARY

| | |
|---|---|
| **System Status** | ⚠️ READY WITH KNOWN LIMITATIONS |
| **Rank Model MAE** | ~589 ranks (CDF-based primary) |
| **Cutoff Model MAE** | 1,559 ranks competitive (565 for top-5,000 seats) |
| **Avg Prediction Time** | < 1 ms (rank), 6.6 ms (college recs) |
| **Model Load Time** | 752 ms |
| **100 Concurrent Requests** | 686 ms (no crashes) |

The system is functionally correct and performant. The cutoff model's competitive-segment MAE of 1,559 is inflated by two small communities (ST: 8 combos, SCA: 6 combos) with volatile ranks. For the practically important segment (top 5,000 seats — IIT/NIT-tier), MAE is 565. The system is suitable for advisory use. Students should be advised that predictions carry ±1,000–2,000 rank uncertainty for competitive seats.

---

## 2. TEST RESULTS SUMMARY

| Phase | Description | Result | Detail |
|---|---|---|---|
| 1 | Rank Model (20 cases) | ✅ 20/20 PASS | All structures correct, monotone, ±100 range exact |
| 2 | Cutoff Model Validation | ⚠️ ACCEPTABLE | Comp. MAE 1,559; Top-5k MAE 565; driven by ST/SCA |
| 3 | predict_colleges() (50 cases) | ✅ 50/50 PASS | All fields present, no WONT_GET, logic correct |
| 4 | Edge Cases (27 cases) | ✅ 27/27 PASS | Invalid input, extremes, BCM alias, decimals |
| 5 | Performance Benchmarks | ✅ ALL TARGETS MET | Well within all thresholds |
| 6 | Year-by-Year Accuracy | ⚠️ ACCEPTABLE | MAE stable 1,141–2,016 across years |
| 7 | Data Integrity (41 checks) | ✅ 41/41 PASS | 1 note: 23 unmapped college codes (1.6% rows) |

---

## 3. DETAILED METRICS

### 3.1 Rank Model

| Metric | Value |
|---|---|
| Primary method | 2025 mark CDF lookup (exact count of students above mark) |
| Fallback method | Historical norm_rank + hybrid community shift |
| Primary MAE | ~589 ranks (from mark-tie aliasing only) |
| Fallback MAE | ~3,096 ranks |
| Range band | ±100 ranks (hard-coded) |
| Total students in pool | 239,299 |

**Observed predictions (2025 CDF, community-agnostic):**

| Marks | Predicted Rank | Notes |
|---|---|---|
| 200 | 1 | Highest possible mark |
| 195 | 4,519 | Top ~1.9% |
| 150 | 118,139 | ~50th percentile |
| 100 | 229,233 | ~95th percentile |
| 75 | 239,299 (max) | Below CDF floor |

### 3.2 Cutoff Model

**Validation: Train 2022-2024 → Predict 2025 → Compare actual 2025**

| Community | Count | Comp. MAE | RMSE | Within ±500 | Within ±1000 |
|---|---|---|---|---|---|
| OC | 112 | 832 | 1,483 | 52.7% | 71.4% |
| BC | 66 | 1,000 | 1,331 | 30.3% | 71.2% |
| SC | 20 | 1,600 | 2,209 | 10.0% | 40.0% |
| ST | 8 | 19,225 | 29,790 | 0.0% | 0.0% |
| MBC | 68 | 937 | 1,544 | 63.2% | 70.6% |
| SCA | 6 | 4,647 | 5,921 | 16.7% | 16.7% |
| **ALL** | **280** | **1,559** | **5,323** | **44.6%** | **65.7%** |

**Top-5,000 segment (most competitive seats):**
- MAE: **565 ranks**
- n: 148 combos

**Error percentiles (competitive segment):**

| Percentile | Error |
|---|---|
| 25th | 191 |
| 50th (median) | 602 |
| 75th | 1,449 |
| 90th | 2,759 |
| 95th | 4,248 |

**Full set (all combos including low-demand tail):** MAE = 27,211  
*(Low-demand branches with 1–2 seats have essentially random year-to-year closing ranks — expected and documented.)*

### 3.3 Year-by-Year Accuracy Trend

| Year | Train Data | Comp. MAE | Comp. RMSE | Within ±500 | n_comp |
|---|---|---|---|---|---|
| 2023 | 2022 | 1,141 | 1,860 | 38.4% | 263 |
| 2024 | 2022–2023 | 2,016 | 4,494 | 43.2% | 280 |
| 2025 | 2022–2024 | 1,559 | 5,323 | 44.6% | 280 |

Competitive MAE is within a 1,000–2,000 range across years with no systematic degradation. 2024 was a volatile year.

### 3.4 Performance Benchmarks

| Metric | Actual | Target | Status |
|---|---|---|---|
| Model load time | 752 ms | < 5,000 ms | ✅ |
| Rank prediction (avg) | < 0.01 ms | < 100 ms | ✅ |
| College prediction (avg) | 6.6 ms | < 500 ms | ✅ |
| 100 concurrent requests | 686 ms | < 10,000 ms | ✅ |

---

## 4. KNOWN LIMITATIONS

1. **ST / SCA accuracy** — ST has only 8 competitive combos in the dataset; SCA has 6. Predictions for these communities are unreliable for competitive seats. The model defaults to "persistence" (last known value) which can miss sharp year-to-year rank swings.

2. **23 unmapped college codes** — 23 private colleges appear in cutoffs.csv but not in college_codes.csv. They are labelled "College XXXX" in recommendations (1.6% of 15,022 lookup rows). These are low-demand private colleges unlikely to appear in top-5 recommendations for competitive students.

3. **~21% unmapped branch codes** — 23/114 branch codes in the lookup fall back to "Branch XXX". These are mostly newer or minor specialisations. Standard branches (CS, EC, ME, CE, EE, IT) are fully mapped.

4. **CDF is 2025-specific** — The primary rank model uses the 2025 mark distribution (239,299 students). If 2026 student count changes significantly, predicted ranks will shift proportionally. Fallback uses historical norm_rank.

5. **Prediction range ±100 is statistical** — The true uncertainty for a given mark is approximately ±589 ranks (mark-tie aliasing). The ±100 band displayed is the model's output interval, not a 95% confidence interval.

6. **2026 cutoff predictions are extrapolations** — Based on 2022–2025 trends. Structural changes (new seats, new colleges, fee revisions) are not modelled.

---

## 5. RECOMMENDATIONS

- **Deploy** for advisory use. Make uncertainty explicit in the UI ("estimated rank ± 500–1,000").
- **Do not present predictions as exact** — frame as "most likely range."
- **For ST/SCA users**: show broader uncertainty warning in UI.
- **Monitor August 2026** — compare predicted vs. actual ranks once TNEA 2026 results are published.
- **Retrain annually** — add 2026 data and retrain both models before the 2027 counselling cycle.
- **Fix college_codes.csv gap** — source names for the 23 unmapped private colleges and patch the CSV.

---

## 6. NEXT STEPS

- [ ] Deploy to production (FastAPI backend + frontend)
- [ ] Add UI warning for ST / SCA predictions
- [ ] Source names for 23 unmapped college codes
- [ ] Monitor user predictions (log marks, community, predicted rank)
- [ ] **August 2026**: Validate predicted ranks against actual TNEA 2026 ranks
- [ ] **September 2026**: Compare predicted 2026 cutoffs against actual cutoffs
- [ ] Retrain with 2026 data for 2027 predictions

---

*Report auto-generated by the comprehensive test suite in `backend/scripts/`.*
