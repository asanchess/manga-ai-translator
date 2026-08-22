# Changes Summary — Milestone M1: Layer Isolation & Programmatic Anti-Patch Guard

**Agent**: teamwork_preview_worker_m1  
**Milestone**: M1 (Layer Isolation & Programmatic Anti-Patch Guard)  
**Date**: 2026-08-22  

---

## 1. Objectives Addressed

1. **Anti-Patch Guard Quality Validator (`backend/tests/anti_patch_guard.py`)**:
   - Implemented a programmatic validator enforcing:
     - **Check A (Solid Patch Detector)**: Mathematical inspection of bounding boxes and sliding sub-patches inside speech bubbles. Detects solid/uniform color fills ($\sigma^2 < 1.0$) characteristic of `cv2.rectangle` coarse patching.
     - **Check B (Background SSIM Difference)**: Computes Structural Similarity Index (SSIM) on non-bubble background pixels between `v3_translated` and `v1_original`. Validates degradation $\le 0.5\%$ (SSIM $\ge 0.995$).
   - Full CLI support:
     - `--manga <name> --chapter <ch> --pages <p1> <p2>`
     - `--all` for sweeping audits across all chapters.
     - `--test-synthetic` for self-contained unit tests.
     - `--json-output <path>` generating detailed per-page metrics reports.

2. **Frontend Public Directory Cleanup**:
   - Removed stray directories at `frontend/public/manga/` (`v2/`, `v2_cleaned/`, `v3/`, `v3_translated/`) that previously corrupted `chapters_index.json` by registering as phantom manga titles.
   - Synchronized `chapters_index.json`, restoring the catalog to only valid manga titles (`The_Ultimate_of_All_Ages`).

3. **Layer Isolation & Codebase Audit**:
   - Audited `backend/agents/cleaner_agent.py`, `backend/agents/manga_pipeline_service.py`, and `backend/agents/translator_typesetter_agent.py`.
   - Verified 0 occurrences of `cv2.rectangle` or solid rectangular fills in active pipeline code.
   - Confirmed physical layer isolation:
     - `v1_original` (RAW scan) $\to$ `cleaner_agent.py` $\to$ `v2_cleaned` (Cleaned art via Telea inpainting).
     - `v2_cleaned` $\to$ `translator_typesetter_agent.py` $\to$ `v3_translated` (Vector overlay typeset). `v3` strictly takes `v2` as input and never touches `v1`.

---

## 2. Files Modified & Created

| File | Status | Description |
|---|---|---|
| `backend/tests/anti_patch_guard.py` | Created | Core Anti-Patch Guard programmatic quality validator CLI and test harness. |
| `frontend/public/manga/chapters_index.json` | Updated | Rebuilt metadata without phantom manga entries. |
| `frontend/public/manga/v2/` | Deleted | Removed stray directory. |
| `frontend/public/manga/v2_cleaned/` | Deleted | Removed stray directory. |
| `frontend/public/manga/v3/` | Deleted | Removed stray directory. |
| `frontend/public/manga/v3_translated/` | Deleted | Removed stray directory. |
| `backend/tests/anti_patch_report.json` | Generated | Quality report output for audited pages. |

---

## 3. Test Verification Results

### 3.1 Synthetic Sanity Tests
Command: `python backend/tests/anti_patch_guard.py --test-synthetic`
- **Synthetic Test 1 (Genuine Inpainting)**: `[PASS]` (Check A MinVar > 1.0, Check B SSIM >= 0.995).
- **Synthetic Test 2 (Solid Rectangle Detection)**: `[PASS]` (Flagged `cv2.rectangle` fill with variance 0.0).
- **Synthetic Test 3 (Background Degradation Detection)**: `[PASS]` (Flagged background corruption with 2.99% degradation).

### 3.2 Real Manga Chapter 531 Pages 2 & 8
Command: `python backend/tests/anti_patch_guard.py --chapter chapter_531 --pages 2 8`
- **Page 2 (`page_002.webp`)**:
  - Check A (Solid Patch): MinVar = `37.84` $\ge 1.0$ `[PASS]`
  - Check B (Background SSIM): SSIM = `0.99951` (Degradation: `0.049%` $\le 0.5\%$) `[PASS]`
  - Verdict: `[PASS]`
- **Page 8 (`page_008.webp`)**:
  - Check A (Solid Patch): MinVar = `39.98` $\ge 1.0$ `[PASS]`
  - Check B (Background SSIM): SSIM = `0.99950` (Degradation: `0.050%` $\le 0.5\%$) `[PASS]`
  - Verdict: `[PASS]`

### 3.3 Typesetter Layout Unit Tests
Command: `python backend/tests/test_typesetter_layout.py`
- Circular bubble boundary test: `[PASS]` (Max text pixel distance 61.72px $\le$ safe limit 63.75px, 0 text bleed).
- Dark bubble auto-contrast test: `[PASS]` (White text rendered on dark background).
