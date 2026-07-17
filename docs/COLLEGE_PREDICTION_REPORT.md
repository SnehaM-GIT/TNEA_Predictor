# College Prediction Model — Technical Report

**System:** TNEA Predictor (PickMySeat.AI)
**Component:** College + branch recommendation from predicted rank + community
**Report date:** 2026-07-14

---

## 1. Purpose

Given a student's **predicted rank** (from the Rank model) and **community**,
recommend attainable **college + branch** seats for the **2026** admission year,
each with a safety margin, status (SAFE / MARGINAL / WONT_GET) and match
confidence.

Under the hood this is a **cutoff (closing-rank) predictor**: for every
`(college, branch, community)` combo it forecasts the **2026 closing rank**, then
filters/ranks combos the student can reach.

---

## 2. Data sources

### 2.1 Raw data (PDFs)
Location: `backend/data/raw/` — allotment **round** PDFs (opening/closing rank
comes from round allotments, not rank lists):

| Year | Round PDFs |
|------|-----------|
| 2021 | `2021 - ROUND1..4.pdf` |
| 2022 | `2022_round1..4.pdf` |
| 2023 | `2023_round1..4.pdf` |
| 2024 | `2024_round1..4.pdf` |
| 2025 | `2025_round1..3.pdf` |

### 2.2 Extraction
Script: **`backend/scripts/extract_tnea_data.py`**

- Parses each round PDF, extracting `rank, college_code, branch_code,
  allotted_category` per allotment row.
- Groups by `(college_code, branch_code, allotted_category, year)`:
  `opening_rank = min(rank)`, `closing_rank = max(rank)`, `seats_filled = count`.
- Output → `backend/data/cleaned/cutoffs.csv`.

Branch/college code tables (`backend/scripts/extract_codes.py`):
- `college_codes.csv` — **478 colleges** (`college_code, name, short, type, district`)
- `course_codes.csv` — **130 branches** (`branch_code, branch_name`)

### 2.3 Cleaned training files
`backend/data/cleaned/`

**`cutoffs.csv`** — **62,144 rows**
Columns: `college_code, branch_code, year, opening_rank, closing_rank, seats_filled, community`

| Year | Combo-year rows |
|------|-----------------|
| 2021 | 11,142 **(EXCLUDED)** |
| 2022 | 10,035 |
| 2023 | 13,196 |
| 2024 | 12,862 |
| 2025 | 14,909 |

> **2021 is excluded.** Its `closing_rank` is a *community rank* (max ~26k),
> incompatible with the *overall rank* metric (max ~239k) used 2022–2025. Mixing
> it corrupts every trend.

**`ranks.csv`** (same file as Rank model, 621,042 rows) — used to build rank
**distributions per community per bucket** (context, not the trend itself).

College type breakdown (`college_codes.csv`):
Self-Financing 440 · Constituent 16 · Government 11 · University Departments 5 ·
CECRI/CIPET 3 · Government Aided 3.

---

## 3. Training

Script: **`backend/scripts/build_cutoff_model.py`**

### 3.1 Why not per-combo XGBoost
The original spec's "26k separate XGBoost models on ≤4 points each" overfit
badly (global XGBoost scored R²=0.05, MAE=42,172). With only 1–4 yearly points
per combo, a **damped weighted linear trend** is the statistically sound choice.

### 3.2 Method — per-combo damped weighted linear trend
Config:
```
MIN_YEAR        = 2022        # 2021 dropped (metric mismatch)
YEAR_WEIGHT_BASE = 2019       # weight = year − 2019 (recent years weigh more)
DAMP            = 0.3         # damp toward last-value baseline
SEG_THRESHOLD   = 10000       # last value < this → persistence
```
Per combo `(college, branch, community)`:
- **1 point / no year variation** → `persistence` (repeat last value).
- **Competitive** (last closing < 10,000) → `persistence`. Empirically beats
  trend extrapolation on the seats that actually matter for recommendations.
- **Else** → weighted `polyfit` linear trend, then damp toward last value:
  `pred = last + 0.3 × (trend_raw − last)`, clamped to `[0.3·min, 3·max]`.

Counselling rounds are collapsed to one row per combo-year:
`closing = max` (final closing), `opening = min`, `seats = sum`.

### 3.3 Data split
- **Train:** 2022, 2023, 2024
- **Validation:** predict 2025, compare to actual
- **Final predictor:** refit each combo on **all** years (2022–2025), forecast **2026**

### 3.4 Output artifacts
`backend/data/cleaned/`

| File | Contents |
|------|----------|
| `cutoff_predictor.pkl` | Per-combo trend params (slope, intercept, method, n, last/min/max, pred_2026) — **15,022 combos** |
| `cutoff_lookup_2026.csv` | Predicted 2026 closing rank per combo — **15,022 rows** |
| `historical_patterns.pkl` | Per-combo closing ranks 2022–2025 + YoY trend |
| `distribution_2024.pkl` | Rank distribution per community per rank-bucket (2022–2024) |
| `cutoff_model_meta.pkl` | Validation metrics + config |

Rank buckets: `1–100, 100–500, 500–1000, 1000–5000, 5000–10000, 10000+`.

---

## 4. Validation results (train 2022–2024 → predict 2025)

Metrics are **stratified** — low-demand branches (1–2 seats) have near-random
closing ranks and dominate raw MAE; the **competitive segment (< 10,000)** is
what drives recommendations.

| Segment | MAE | Notes |
|---------|-----|-------|
| **Competitive (actual < 10,000)** | **1,559** | Recommendation-relevant |
| Top (actual < 5,000) | 565 | Most competitive seats |
| Full set (all combos) | 27,210 | Dominated by noisy low-demand tail |

Competitive band hit-rates: **within ±500 → 44.6%**, **within ±1000 → 65.7%**.

Per-community competitive MAE:

| Comm | MAE |
|------|-----|
| OC | 831.7 |
| BC | 999.9 |
| MBC | 936.8 |
| SC | 1,600.4 |
| SCA | 4,647.0 |
| ST | 19,224.6 (very sparse data) |

**Verdict (competitive): ACCEPTABLE** (MAE 1,559; < 2,000 threshold).
ST/SCA are weak due to tiny sample sizes.

---

## 5. Runtime / inference

File: **`backend/utils/predict_colleges.py`** → `predict_colleges(marks, community, top_n=5)`

Flow:
1. `predict_rank(marks, community)` → predicted rank + ±100 range
   (or `forced_rank` for a verified rank).
2. Load `cutoff_lookup_2026.csv`; filter to student's community.
3. **Attainable** = `predicted_closing_rank_2026 ≥ predicted_rank`
   (`safety_margin = closing − rank`).
4. Status: `< 0 → WONT_GET`, `≤ 500 → MARGINAL`, else `SAFE`.
5. Attach college name/type/district (`college_codes.csv`) and branch name
   (`course_codes.csv`).
6. Rank by **college tier** then branch competitiveness; return `top_n`.
7. `match_confidence` from rank-vs-closing ratio (clamped 48–95).

College tier order (most→least preferred): University Departments → Constituent
→ Government → Government Aided → CECRI/CIPET → Self-Financing.

---

## 6. Known limitations

- Only the **competitive segment (< 10,000)** is reliable; low-demand branch
  closing ranks are ~random year-to-year (full-set MAE ~27k).
- **ST** (MAE ~19k) and **SCA** (~4.6k) are weak — very sparse training data.
- **2021 excluded** entirely (incompatible rank metric).
- Trend rests on 4 yearly points max (2022–2025); a distorted round schedule
  (e.g. 2025 had 3 rounds vs 4) can bias `closing_rank = max`.
- 2026 forecast assumes continuation of the 2022–2025 trend; a large pool-size
  or seat-matrix change is not modeled.
