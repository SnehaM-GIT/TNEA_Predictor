# TNEA Predictor — Final Checklist

**Date:** 2026-06-06  
**Status:** ⚠️ READY WITH KNOWN LIMITATIONS (see PRODUCTION_READINESS_REPORT.md)

---

## System Completeness

- [x] Rank model trained (`rank_model_final.pkl`)
- [x] Rank model outputs ±100 ranges with CDF-based predictions
- [x] Cutoff model trained (`cutoff_predictor.pkl` — 15,022 combos)
- [x] 15,022 college+branch+community combos have 2026 predictions
- [x] College names populated from `college_codes.csv` (430/453 codes, 98.4%)
- [x] Branch names populated from `course_codes.csv` (91/114 codes, 79.8%)
- [x] `predict_colleges()` function working
- [x] Interactive test script (`test_predict_interactive.py`)
- [x] Comprehensive test suite (7 scripts, 9 phases)
- [x] Performance benchmarks met (all targets)
- [x] Edge cases handled gracefully
- [x] Data integrity verified (41/41 checks pass)
- [x] Production readiness report generated

---

## File Structure

### Models & Data (`backend/data/cleaned/`)

- [x] `rank_model_final.pkl` — rank model (21 KB)
- [x] `rank_model_meta.pkl` — rank model metadata
- [x] `cutoff_predictor.pkl` — per-combo cutoff model (1.1 MB)
- [x] `cutoff_model_meta.pkl` — cutoff model metadata + validation metrics
- [x] `distribution_2024.pkl` — rank distribution per community per bucket
- [x] `historical_patterns.pkl` — per-combo closing rank history (727 KB)
- [x] `college_codes.csv` — college metadata (88 KB, 478 colleges)
- [x] `course_codes.csv` — branch name lookup (4.5 KB)
- [x] `cutoff_lookup_2026.csv` — predicted 2026 closing ranks (279 KB, 15,022 rows)
- [x] `cutoffs.csv` — historical cutoffs 2021–2025 (2.0 MB)
- [x] `ranks.csv` — historical rank data (20 MB)

### Utils (`backend/utils/`)

- [x] `ml_utils.py` — `predict_rank()`, `predict_rank_adjusted()`, `load_model()`
- [x] `predict_colleges.py` — `predict_colleges()` recommender

### Scripts (`backend/scripts/`)

- [x] `test_predict_interactive.py` — interactive manual testing
- [x] `test_rank_model_comprehensive.py` — Phase 1: 20 rank model cases
- [x] `test_cutoff_model_comprehensive.py` — Phase 2: cutoff model validation
- [x] `test_predict_colleges_comprehensive.py` — Phase 3: 50 college prediction cases
- [x] `test_edge_cases.py` — Phase 4: edge case handling
- [x] `test_performance.py` — Phase 5: timing + concurrency
- [x] `test_accuracy_benchmark.py` — Phase 6: year-by-year accuracy
- [x] `test_data_integrity.py` — Phase 7: data quality checks

---

## Test Results

| Phase | Script | Result |
|---|---|---|
| 1 — Rank Model | `test_rank_model_comprehensive.py` | ✅ 20/20 PASS |
| 2 — Cutoff Model | `test_cutoff_model_comprehensive.py` | ⚠️ MAE=1,559 (top-5k MAE=565) |
| 3 — predict_colleges | `test_predict_colleges_comprehensive.py` | ✅ 50/50 PASS |
| 4 — Edge Cases | `test_edge_cases.py` | ✅ 27/27 PASS |
| 5 — Performance | `test_performance.py` | ✅ ALL TARGETS MET |
| 6 — Accuracy Trend | `test_accuracy_benchmark.py` | ⚠️ MAE 1,141–2,016 (no degradation) |
| 7 — Data Integrity | `test_data_integrity.py` | ✅ 41/41 PASS |

---

## Known Issues (Non-blocking)

- [ ] 23 college codes unmapped in `college_codes.csv` → show "College XXXX" (1.6% of rows)
- [ ] ST community cutoff predictions unreliable (only 8 competitive combos, high variance)
- [ ] SCA community cutoff predictions unreliable (only 6 competitive combos)
- [ ] Marks ≤ 75 all get rank = 239,299 (floor of CDF — no data below this mark)
- [ ] Rank prediction does not validate marks range (extrapolates for marks < 0 or > 200)

---

## Deployment Checklist

- [ ] Backend API tested end-to-end (`/predict`, `/colleges` endpoints)
- [ ] Frontend connected to backend
- [ ] UI shows uncertainty warning (±500–1,000 ranks)
- [ ] ST / SCA warning shown in UI for those communities
- [ ] Production server deployed
- [ ] Monitoring set up (log inputs, measure latency)

---

## Post-Deployment Actions

- [ ] August 2026: Compare predicted ranks vs. actual TNEA 2026 ranks
- [ ] September 2026: Compare predicted 2026 cutoffs vs. actual counselling data
- [ ] Collect user feedback
- [ ] Source names for 23 unmapped college codes and patch `college_codes.csv`
- [ ] Retrain both models with 2026 data before the 2027 counselling cycle
