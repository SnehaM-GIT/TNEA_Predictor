# Rank Prediction Model — Technical Report

**System:** TNEA Predictor (PickMySeat.AI)
**Component:** Overall TNEA rank prediction from HSC aggregate mark + community
**Report date:** 2026-07-14

---

## 1. Purpose

Given a student's **aggregate mark (0–200)** and **community**, predict their
**overall TNEA rank** with a ±range band and a confidence score. This rank is the
input to the College Prediction model.

---

## 2. Data sources

### 2.1 Raw data (PDFs)
Location: `backend/data/raw/`

| Year | Rank list PDF | Allotment round PDFs |
|------|---------------|----------------------|
| 2021 | — (ROUND1–4 only) | 2021 - ROUND1..4.pdf |
| 2022 | `2022_rank.pdf` | `2022_round1..4.pdf` |
| 2023 | `2023_rank.pdf` | `2023_round1..4.pdf` |
| 2024 | `2024_rank.pdf` | `2024_round1..4.pdf` |
| 2025 | `2025_rank.pdf` | `2025_round1..3.pdf` |
| 2026 | `2026_rank_list_raw.pdf` | — |

### 2.2 Extraction
Script: **`backend/scripts/extract_tnea_data.py`** (uses `pdfplumber`)

- Parses each rank-list PDF page-by-page, auto-detecting header layout
  (rank / application no / aggregate mark / community columns vary per year).
- Merges `BCM → BC` at model time; community rank columns are ignored (overall
  rank only).
- Output → `backend/data/cleaned/ranks.csv`.

### 2.3 Cleaned training file
File: **`backend/data/cleaned/ranks.csv`** — **621,042 rows**

Columns: `rank, app_no, aggregate_mark, community, community_encoded, year, year_normalized`

| Year | Students | Mean mark | Max rank |
|------|----------|-----------|----------|
| 2022 | 156,278 | 140.65 | 156,278 |
| 2023 | 27,866  | 129.86 | 27,866  |
| 2024 | 197,599 | 143.99 | 197,601 |
| 2025 | 239,299 | 148.44 | 239,299 |

Communities present: `OC, BC, BCM, MBC, SC, SCA, ST` (BCM folded into BC → 6 modeled classes: `BC, MBC, OC, SC, SCA, ST`).

> **2023 is an anomaly year** (only 27,866 students, mean mark 129.86 — far below
> other years). It is down-weighted heavily and excluded from trend fitting.

---

## 3. Training

Script: **`backend/scripts/train_rank_model.py`**

### 3.1 Data split
- **Train:** years ≤ 2024 (2022, 2023, 2024)
- **Validation / current-year calibration:** 2025

### 3.2 Year weights (for historical fallback)
```
2022 → 0.20    2023 → 0.05 (anomaly)    2024 → 0.75
```
Trend fitting excludes 2023.

### 3.3 Model type: `cdf_primary_hybrid_fallback`

Two tiers:

**PRIMARY — 2025 mark CDF lookup**
HSC marks are published *before* TNEA ranks, so the current-year mark
distribution is a legitimate input feature. For each rounded mark:
```
pred_rank = (count of students with strictly higher mark) + 1
```
Residual error comes only from mark-tie aliasing.

**FALLBACK — historical norm_rank + hybrid shift correction**
Used when the mark falls outside the CDF range or for future-year prediction:
- Weighted historical `mark → norm_rank` lookup (linear-interpolated /
  extrapolated) built across 2022–2024, weighted by year weights.
- **Hybrid delta** shift = `max(community-specific delta, overall delta)`, where
  `delta = actual_2025_mean_mark − weighted_historical_mean_mark`. Corrects for
  mark inflation ("same mark → worse rank when the pool's average rises"). The
  hybrid `max` handles communities like OC whose own marks barely move while the
  overall pool inflates.

### 3.4 Output artifacts
Location: `backend/data/cleaned/`

| File | Contents |
|------|----------|
| `rank_model_final.pkl` | Full model: 2025 CDF, historical lookup, interp fn, per-community deltas, weights, metrics |
| `rank_model_meta.pkl` | Metadata + validation metrics |

---

## 4. Validation results (predict 2025)

| Approach | MAE | Notes |
|----------|-----|-------|
| **Primary — 2025 mark CDF** | **589** | Production default (`use_cdf=True`) |
| Hybrid actual-delta fallback | 3,096 | Used when CDF unavailable |
| Hybrid trend-delta | (higher) | Conservative, no future data used |
| No correction | (highest) | Baseline |

**Basis label:** *"percentile-based from 2022–2026 data"*
**Range band:** ±100 ranks (`range_halfwidth = 100`)

---

## 5. Runtime / inference

File: **`backend/utils/ml_utils.py`** → `predict_rank(marks, community)`

Flow:
1. Load `rank_model_final.pkl` (cached).
2. `BCM → BC`; reject unknown communities.
3. Round mark to nearest 0.5.
4. If mark in 2025 CDF → primary lookup (`basis="cdf_exact"`, confidence ≤ 90).
5. Else → historical fallback with hybrid delta (`basis="hist_exact"`/`"hist_interp"`, confidence ≤ 85).
6. Return `predicted_rank`, `range_min = rank−100` (≥1), `range_max = rank+100`, `confidence`, `basis`.

Confidence = `(1 − |norm_rank − 0.5|) × 100`, clamped (mid-distribution marks →
higher confidence; extremes → lower).

---

## 6. Known limitations

- Primary CDF is 2025-specific; a fresh year requires re-running extraction +
  training (`2026_rank_list_raw.pdf` is staged for this).
- 2023 data is structurally anomalous and contributes almost nothing (weight 0.05).
- Fallback path (MAE ~3,096) is markedly less accurate than the CDF path.
- Tie-group aliasing sets the ~589 MAE floor on the primary path.
