# Technical Survey & Audit Report: R1, R2, R5
**Project**: Manga & Manhua AI Translation and Inpainting Pipeline v4.0  
**Author**: Explorer 2 (Survey & Gap Analysis)  
**Date**: 2026-08-23  
**Working Directory**: `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_explorer_survey_2`

---

## Executive Summary

This investigation conducted a comprehensive codebase and runtime audit for requirements **R1** (Bubble vs SFX Classification & Per-Pixel Glyph Masking), **R2** (100-Bubble Comprehensive Benchmark Verification), and **R5** (Anti-Patch Guard & Vector Typography / Elliptical Text Fitting).

### High-Level Status:
- **R1 (Bubble vs SFX & Inpainting)**: **FULLY IMPLEMENTED & HIGH FIDELITY**. Zero rectangular fills (`cv2.rectangle`) in cleaner agent; adaptive Otsu + color Euclidean distance binarization with Telea inpainting; robust regex & heuristic SFX classifier preserves sound effects and combat artwork.
- **R2 (100-Bubble Benchmark)**: **FULLY IMPLEMENTED & 100% PASSING**. `backend/tests/bubble_benchmark_100.py` evaluates 7 archetypes across 100 test cases with 0 errors in 0.47s.
- **R5 (Anti-Patch Guard & Typography)**: **IMPLEMENTED WITH 2 IDENTIFIED GAPS/BUGS**:
  1. **Anti-Patch Guard Check B Logic Defect**: `compute_background_ssim` masks out `cv2.absdiff(v1_img, v3_img)` from the background mask, disabling background corruption detection and causing `anti_patch_guard.py --test-synthetic` to fail.
  2. **Chapter 532 Layer Synchronization**: `page_007.webp` in Chapter 532 had missing/unrepaired `v2_cleaned` and `v3_translated` layers, causing `anti_patch_guard.py --all` to flag Chapter 532. All other 12 chapters passed with 100% page compliance.
  3. **Elliptical Typography**: **VERIFIED & WORKING**. Chord equation $W(y) = 2a\sqrt{1-(y/b)^2}$, binary search font sizing (12px–38px), $\le 85\%$ safe oval fitting, Cyrillic TTF support, and auto-contrast verified in `test_typesetter_layout.py`.

---

## 1. Detailed Investigation: Requirement R1 (Bubble vs SFX & Inpainting)

### 1.1 Bubble vs SFX Classification
- **Target Files**:
  - `backend/agents/comic_bubble_detector.py`
  - `backend/agents/ocr_engine.py` (lines 31-59)
  - `backend/agents/llm_translator.py` (lines 313-329)
- **Mechanism**:
  - `ComicBubbleDetector.is_sound_effect_or_noise()` applies 4-tier filtering:
    1. Regex pattern matching (`COMMON_SFX_REGEX`): Matches 1-3 char random noise (`G2`, `hx`, `KY`, `0g`, `09`, `qk`, `pk`, `vk`), onomatopoeia (`boom`, `bang`, `slash`, `whoosh`, `clash`, `roar`, `thud`, `crack`, etc.), and alphanumeric noise patterns (`^[0-9]+[a-zA-Z]+[0-9]*$`).
    2. Multi-token short noise check (e.g. `'hx KY'`, `'0g 09'`, `'A1 B2'`).
    3. Single/double character non-word suppression.
    4. Visual background texture analysis: Computes border luminance variance $\sigma^2_{border} > 1200$ to differentiate busy combat background art from enclosed bubble interiors.
  - Integration:
    - In `llm_translator.py`: When classified as SFX, `c["is_sfx"] = True` and `c["translated_text"] = ""` (SFX is never translated or stamped).
    - In `cleaner_agent.py`: `process_page_cleaning()` skips inpainting on any cluster where `is_sfx == True` or `is_sound_effect_or_noise() == True`.

### 1.2 Per-Pixel Glyph Masking & Telea Inpainting (Zero Rectangular Fills)
- **Target File**: `backend/agents/cleaner_agent.py`
- **Mechanism**:
  - `get_bubble_background_color()`: Dynamically samples median BGR color from 4 perimeter strips outside the text ROI.
  - `clean_speech_bubble_seamless()`:
    1. Color Euclidean distance: $\Delta C = \sqrt{(R - R_{bg})^2 + (G - G_{bg})^2 + (B - B_{bg})^2}$.
    2. Otsu adaptive binarization (`cv2.threshold` + Otsu) with auto-polarity (inverted for dark bubbles with $L_{bg} < 90$).
    3. Mask intersection `cv2.bitwise_and(otsu_mask, dist_mask)`.
    4. Small noise filtering via `cv2.morphologyEx(MORPH_OPEN, (2,2))` and glyph edge dilation via `cv2.dilate(MORPH_ELLIPSE, (3,3), iterations=2)`.
    5. Boundary protection: Zeroes out 2px outer border of ROI to guarantee authentic background reference pixels.
    6. Seamless inpainting: `cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)`.
  - **Compliance**: Zero occurrences of `cv2.rectangle` or solid color fill across the cleaning pipeline.

---

## 2. Detailed Investigation: Requirement R2 (100-Bubble Comprehensive Benchmark)

### 2.1 Benchmark Architecture & Test Matrix
- **Target File**: `backend/tests/bubble_benchmark_100.py`
- **Test Archetypes Breakdown**:
  | Archetype ID | Category | Count | Ground Truth Expected | Test Method | Status |
  |---|---|---|---|---|---|
  | 1 | Standard Oval Light Bubbles | 20 | `SPEECH_BUBBLE`, Mask Area > 0 | `test_01_oval_light_bubbles_20` | **PASS (20/20)** |
  | 2 | Inverted Dark Bubbles | 20 | `SPEECH_BUBBLE`, Mask Area > 0 | `test_02_dark_inverted_bubbles_20` | **PASS (20/20)** |
  | 3 | Spiky Shout / Scream Bubbles | 15 | `SPEECH_BUBBLE` | `test_03_spiky_shout_bubbles_15` | **PASS (15/15)** |
  | 4 | Floating Borderless Narrations | 15 | `SPEECH_BUBBLE` | `test_04_floating_borderless_text_15` | **PASS (15/15)** |
  | 5 | System / Skill Windows (RPG UI) | 10 | `SPEECH_BUBBLE` | `test_05_system_windows_10` | **PASS (10/10)** |
  | 6 | SFX & Noise Artifacts | 10 | `SFX_ART` (0 text stamping) | `test_06_sfx_and_noise_artifacts_10` | **PASS (10/10)** |
  | 7 | Semi-transparent Thought Clouds | 10 | `SPEECH_BUBBLE` | `test_07_thought_clouds_10` | **PASS (10/10)** |
  | **Total** | | **100** | | | **PASS (100/100)** |

### 2.2 Execution Verification
- Command: `python backend/tests/bubble_benchmark_100.py`
- Output: `Ran 7 tests in 0.472s - OK`
- False positive rate on SFX: 0.0% (all 10 noise/SFX samples correctly isolated).
- Detection accuracy: 100/100 (100%).

---

## 3. Detailed Investigation: Requirement R5 (Anti-Patch Guard & Typography)

### 3.1 Vector Typography & Elliptical Text Fitting
- **Target Files**:
  - `backend/agents/translator_typesetter_agent.py`
  - `backend/tests/test_typesetter_layout.py`
- **Mathematical Formulation**:
  - Elliptical horizontal chord width:
    $$W(y) = 2a \sqrt{1 - \left(\frac{y}{b}\right)^2}$$
    where $a = \frac{\text{safe\_w}}{2}$, $b = \frac{\text{safe\_h}}{2}$, with safe bounds $\le 85\%$ of bubble dimensions.
  - Binary search font size optimization: Searches range $[12\text{px}, 38\text{px}]$ to find the maximum legible font size where all lines pack inside elliptical chords.
  - Diamond silhouette centering: Computes line height $H_{line} + 0.15 \cdot \text{font\_size}$, perfectly centering lines both horizontally and vertically.
  - Auto-contrast:
    - Light bubbles ($L_{avg} \ge 120$): Black text `(0, 0, 0)`, stroke width 0.
    - Dark bubbles ($L_{avg} < 120$): Bright white text `(255, 255, 255)` with $1.5\text{px} - 2\text{px}$ black stroke outline.
  - Cyrillic TTF support: `comicbd.ttf`, `segoeuib.ttf`, `arialbd.ttf`.
- **Layout Test Verification**:
  - `python backend/tests/test_typesetter_layout.py` passed with max text pixel distance $59.08\text{px} \le 63.75\text{px}$ (circle radius $75\text{px}$, 85% safe bound) with 0 text pixels leaking outside the circle.

### 3.2 Anti-Patch Guard Architecture & Bug Analysis
- **Target File**: `backend/tests/anti_patch_guard.py`
- **Check A (Solid Patch Detector)**:
  - Scans `v2_cleaned` bubble regions for color variance $\sigma^2 < 1.0$ across 16x16 sliding subpatches.
  - Successfully detects and fails solid rectangle artifacts while allowing Telea inpainting ($\sigma^2 > 5.0$).
- **Check B (Background SSIM Diff) & The Identified Bug**:
  - Specification: Background SSIM difference outside speech bubbles between `v3_translated` and `v1_original` must not exceed 0.5% pixel degradation ($\text{SSIM} \ge 0.995$).
  - **Bug Location**: `backend/tests/anti_patch_guard.py` lines 220–227:
    ```python
    diff_bgr = cv2.absdiff(v1_img, v3_img)
    diff_gray = cv2.cvtColor(diff_bgr, cv2.COLOR_BGR2GRAY) if len(diff_bgr.shape) == 3 else diff_bgr
    _, diff_thresh = cv2.threshold(diff_gray, 8, 255, cv2.THRESH_BINARY)
    if np.count_nonzero(diff_thresh) > 0:
        kernel_diff = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
        diff_dilated = cv2.dilate(diff_thresh, kernel_diff)
        bg_mask[diff_dilated > 0] = 0  # <--- CRITICAL BUG!
    ```
  - **Impact**: Masking `diff_dilated > 0` out of `bg_mask` means *any* changed background art pixel is excluded from the SSIM calculation. Consequently, deliberate background corruption (e.g. Test 3 in `run_synthetic_sanity_tests()`) is masked out, yielding a false $\text{SSIM} = 1.0$, which triggers `AssertionError: Check B failed to catch background corruption!`.
  - **Remedy**: In `compute_background_ssim()`, remove lines 220–227 so that `bg_mask` strictly masks the known `bubble_boxes` (+ padding), allowing background modifications to register in SSIM degradation.

### 3.3 Multi-Chapter Audit Results (`anti_patch_guard.py --all`)
- 12 of 13 chapters passed 100% of pages:
  - `Test_Manga` Ch.1: 1/1 pages passed
  - `The_Ultimate_of_All_Ages` Ch.531: 12/12 pages passed
  - `The_Ultimate_of_All_Ages` Ch.533: 14/14 pages passed
  - `The_Ultimate_of_All_Ages` Ch.534: 11/11 pages passed
  - `The_Ultimate_of_All_Ages` Ch.535: 13/13 pages passed
  - `The_Ultimate_of_All_Ages` Ch.536: 14/14 pages passed
  - `The_Ultimate_of_All_Ages` Ch.537: 8/8 pages passed
  - `The_Ultimate_of_All_Ages` Ch.538: 8/8 pages passed
  - `The_Ultimate_of_All_Ages` Ch.539: 9/9 pages passed
  - `The_Ultimate_of_All_Ages` Ch.540: 8/8 pages passed
  - `The_Ultimate_of_All_Ages` Ch.541: 12/12 pages passed
  - `The_Ultimate_of_All_Ages` Ch.542: 8/8 pages passed
- Chapter 532 failed due to missing `v2`/`v3` layer files for `page_007.webp` (9990x800 webtoon strip), which caused an audit exception.

---

## 4. Summary of Gaps & Actionable Recommendations for Builder

| ID | Module / Component | Issue Description | Recommended Fix |
|---|---|---|---|
| **GAP-01** | `backend/tests/anti_patch_guard.py` | `compute_background_ssim` masks `absdiff(v1, v3)` out of `bg_mask`, blinding Check B to background corruption. | Remove lines 220–227 in `anti_patch_guard.py`. `bg_mask` should solely mask `bubble_boxes` with padding. |
| **GAP-02** | `backend/data/manga/.../chapter_532` | `page_007.webp` in Chapter 532 is missing corresponding `v2_cleaned` and `v3_translated` layers. | Run `ModelInferenceManager.process_chapter_concurrent` or `MangaPipelineService.process_page` on Chapter 532 `page_007.webp` and sync to frontend. |
| **GAP-03** | `backend/tests/anti_patch_guard.py` | `audit_chapter()` crashes if a single page in `v2`/`v3` is missing instead of recording a failed page result. | Wrap page audit in try/except within `audit_chapter()` so ungenerated pages report as `[FAIL]` rather than uncaught `ValueError`. |

---
*Report compiled by Explorer 2.*
