# Manga AI Translator v3.0 SOTA Enterprise — Backend & Pipeline Survey Report

**Author**: Backend & Pipeline Explorer Agent  
**Date**: 2026-08-22  
**Target Architecture**: v3.0 SOTA Enterprise Standard  
**Working Directory**: `c:\Users\asana\OneDrive\Desktop\Manga`

---

## 1. Executive Summary

This survey provides a comprehensive audit of the backend codebase (`backend/agents/`, `backend/main.py`, `backend/server.py`, `backend/data/`, and `backend/tests/`) against the v3.0 SOTA Enterprise specification defined in `ORIGINAL_REQUEST.md` and domain rules in `AGENTS.md`.

### Component Readiness Matrix

| Component | Status | Implementation Quality | Gaps / Required Actions |
|---|---|---|---|
| **Layer Isolation (v1/v2/v3)** | 🟡 Partially Implemented | Clean separation in `manga_pipeline_service.py` (`v1_original` -> `v2_cleaned` -> `v3_translated`) | Storage path mismatch (`v1`/`v2`/`v3` in frontend public vs `v1_original`/`v2_cleaned`/`v3_translated` in backend data); stray folders in `frontend/public/manga/`. |
| **Cleaning & Inpainting** | 🟢 Compliant | Zero `cv2.rectangle` fills; per-pixel glyph binarization (Otsu + color distance + Telea inpaint) | Inpaint radius is set to 4px (spec: 3px); missing programmatic `anti_patch_guard.py` test suite. |
| **Dialogue Topology & Sorting** | 🟡 Partially Implemented | Containment NMS and Figure-8 splitting functional | Bubble sorting currently uses row buckets `(y // row_height, x, y)` instead of `y_center * 10000 + x_center`. |
| **Elliptical Typesetting** | 🟢 Compliant | True horizontal chord math (`2 * a * sqrt(1 - (y/b)^2)`), <=85% safe box, binary font search (38px–12px), auto-contrast | Verified by `test_typesetter_layout.py` with zero text bleed. |
| **Persistent Glossary** | 🔴 Missing | Hardcoded 10-word fallback in `llm_translator.py` | `glossary.json` file missing; prompt injection pipeline for character/faction/cultivation terminology not wired. |
| **ML Inference Singleton** | 🔴 Missing | Global lazy EasyOCR instance in `ocr_engine.py` | No unified `ModelInferenceManager` singleton class; no ThreadPool/ProcessPool dual executor. |
| **Chapter Integrity Checker** | 🔴 Missing | Basic chapter listing in `main.py` | Missing `ChapterIntegrityChecker`, deficit detection (<8 pages in Ch. 537 & 538), multi-mirror rotation, and `pipeline_manifest.json`. |
| **Anti-Patch Guard Tests** | 🔴 Missing | Custom tests in `verify_pipeline.py` | `backend/tests/anti_patch_guard.py` not created; solid patch color variance check and SSIM diff <= 0.5% not automated. |

---

## 2. Deep Dive: Layer Isolation & Architecture (R1)

### 2.1 Layer Contract & Physical Data Flow
The v3.0 standard mandates strict 3-tier layer isolation:
1. **`v1_original` (RAW Scan Layer)**:
   - Immutable raw scan ingested directly from scraper or user upload.
   - Accessible strictly to: Ingestion Scraper (`scraper_agent.py`) and Cleaner (`cleaner_agent.py`).
   - Inspected location: `backend/data/manga/{title}/{chapter}/v1_original/` and `frontend/public/manga/{title}/{chapter}/v1/`.
2. **`v2_cleaned` (Cleaned Artwork Layer)**:
   - Produced solely by `cleaner_agent.py` by inpainting text glyphs from `v1_original`.
   - Artwork outside text glyph masks is completely untouched (0 max pixel diff outside bounding ROI).
   - Inspected location: `backend/data/manga/{title}/{chapter}/v2_cleaned/` and `frontend/public/manga/{title}/{chapter}/v2/`.
3. **`v3_translated` (Final Typeset Layer)**:
   - Produced solely by `translator_typesetter_agent.py`.
   - **Strict isolation constraint**: Consumes only `v2_cleaned` as image canvas (`process_page_translation(v2_p, clusters, output_path=v3_p)`). Never references `v1_original`.
   - Text is applied as vector typography using Pillow `ImageDraw.Draw` directly onto the RGB canvas without pasting opaque rectangular sub-patches.

### 2.2 Storage Layout Inconsistencies Identified
- **Backend vs Frontend directory naming discrepancy**:
  - Backend uses descriptive folder names: `v1_original`, `v2_cleaned`, `v3_translated`.
  - Frontend public directory currently has both short names (`v1`, `v2`, `v3`) and duplicate long names (`v1_original`, `v2_cleaned`, `v3_translated`) created by earlier runs.
  - In `frontend/public/manga/`, stray root folders (`v2/`, `v2_cleaned/`, `v3/`, `v3_translated/`) cause `update_global_chapters_index()` to falsely report them as distinct manga titles in `chapters_index.json`.

---

## 3. Deep Dive: Cleaning & Inpainting Engine (R1)

### 3.1 Algorithm Inspection in `backend/agents/cleaner_agent.py`
The cleaning implementation was inspected at lines 15–140:
1. **Background Color Sampling (`get_bubble_background_color`)**:
   - Extracts 8px perimeter strips above, below, left, and right of the text bounding box.
   - Calculates median BGR color: `med_bgr = np.median(all_p, axis=0)`.
   - Determines bubble luminance: `bg_lum = 0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b` (marks `is_dark = bg_lum < 90`).
2. **Per-Pixel Glyph Binarization (`clean_speech_bubble_seamless`)**:
   - Calculates Euclidean color distance: `color_diff = np.sqrt(np.sum((roi - bg_color)^2, axis=2))`.
   - Applies Otsu thresholding on grayscale ROI (`cv2.THRESH_BINARY` for dark bubbles, `cv2.THRESH_BINARY_INV` for light bubbles).
   - Combines Otsu mask with distance threshold: `text_mask = cv2.bitwise_and(otsu_mask, (color_diff > 25))`.
   - Cleans noise with `cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_2x2)`.
   - Dilates glyph contours to capture antialiasing: `cv2.dilate(text_mask, kernel_ellipse_3x3, iterations=2)`.
3. **Telea Inpainting**:
   - `cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)` (spec recommends `inpaintRadius=3`).
   - Writes inpainted ROI back into image buffer.

### 3.2 Verification of Solid Patch Prohibition
- Ripgrep pattern search across `backend/` confirmed **0 occurrences of `cv2.rectangle` or solid color fills** in `cleaner_agent.py` and `manga_pipeline_service.py`.
- The bubble border contours and surrounding artwork remain 100% intact.

### 3.3 Required Anti-Patch Guard (`backend/tests/anti_patch_guard.py`)
To formally prevent regressions, the missing validator must implement:
- **Check A (Solid Patch Detector)**: Evaluates bounding boxes in `v2_cleaned` and `v3_translated`. If any non-text bounding box region has color variance < 2.0 (solid flat gray/white rectangle), the test fails.
- **Check B (Background SSIM Diff Guard)**: Computes Structural Similarity Index (SSIM) between `v1_original` and `v3_translated` for all pixels outside the union of speech bubble bounding boxes. Pixel degradation must not exceed 0.5% (SSIM >= 0.995).

---

## 4. Deep Dive: Dialogue Topology, Batch Translation & Typesetting (R2)

### 4.1 Bubble Sorting & Reading Order
- **Current State (`ocr_engine.py:74-81`)**:
  ```python
  def topological_reading_sort_key(box: tuple, row_height: int = 50) -> tuple:
      x, y, w, h = box
      row = y // row_height
      return (row, x, y)
  ```
- **v3.0 SOTA Requirement**:
  - Replace row bucketing with explicit continuous geometric center sorting:
    $$\text{Sort Key} = y_{\text{center}} \times 10000 + x_{\text{center}}$$
  - For Manhua (left-to-right reading): $y_{\text{center}} \times 10000 + x_{\text{center}}$
  - For Manga (right-to-left reading): $y_{\text{center}} \times 10000 + (W - x_{\text{center}})$
  - Assign strict 1-based sequential integer IDs (`cluster["id"] = 1, 2, ... N`).

### 4.2 Batch JSON & ID Contract
- `llm_translator.py:106-133` packs the entire page's dialogue into a single JSON array:
  `[{"id": 1, "text": "..."}, {"id": 2, "text": "..."}]`
- Enforces strict JSON Schema return: `[{"id": 1, "translated": "..."}, {"id": 2, "translated": "..."}]`
- `translator_typesetter_agent.py` renders text matching `dialogue.id == bubble.id`.

### 4.3 Elliptical Text Fitting Engine (`translator_typesetter_agent.py`)
- **Horizontal Ellipse Chord Calculation**:
  For an ellipse with semi-axes $a = \frac{\text{safe\_w}}{2}$ and $b = \frac{\text{safe\_h}}{2}$, the available width at vertical offset $y_{\text{mid}}$ from center is:
  $$\text{allowed\_w}(y_{\text{mid}}) = 2 a \sqrt{1 - \left(\frac{|y_{\text{mid}}|}{b}\right)^2}$$
- **Bounds Constraints**:
  - $\text{safe\_w} = \max(20, \lfloor w \times 0.85 \rfloor)$
  - $\text{safe\_h} = \max(15, \lfloor h \times 0.85 \rfloor)$
- **Adaptive Binary Search Sizing**:
  - Iterates font size from 38px down to 12px (extended fallback to 8px).
  - Line height and step: $\text{line\_step} = \text{line\_height} + \lfloor 0.15 \times \text{font\_size} \rfloor$.
  - Fits words into $N$ chords greedily.
  - Centers each line horizontally: $x_{\text{line}} = x + \frac{w - w_{\text{line}}}{2}$.
  - Centers entire text block vertically: $y_{\text{start}} = y + \frac{h - H_{\text{total}}}{2}$.
- **Auto-Contrast & Typography**:
  - Light bubbles (luminance >= 120): Black text `(0, 0, 0)`, stroke width 0.
  - Dark bubbles (luminance < 120): White text `(255, 255, 255)`, black outline stroke width 1–2px (`(0, 0, 0)`).
  - Fonts: Windows Cyrillic TTF paths (`comicbd.ttf`, `segoeuib.ttf`, `arialbd.ttf`).

### 4.4 Persistent Glossary Architecture (Missing)
- Target file path: `backend/data/manga/The_Ultimate_of_All_Ages/glossary.json`
- Required terminology categories:
  1. **Characters**:
     - Gu Feiyang -> Гу Фэйян
     - Li Yunxiao -> Ли Юньсяо
     - Luo Yunshang -> Ло Юньшан
     - Ding Ling'er -> Дин Линъэр
     - Mo Huayuan -> Мо Хуаюань
  2. **Factions & Locations**:
     - Beimin Clan -> Клан Бэймин
     - Sanctuary -> Святилище
     - Heavenly Martial Continent -> Континент Тяньу
     - Yanwu City -> Город Яньу
  3. **Cultivation & Martial Terms**:
     - Yao Beast -> Демонический Зверь
     - Dantian -> Даньтянь
     - Qi -> Ци
     - Martial Sovereign -> Боевой Владыка
     - Nine Heavens Martial Emperor -> Боевой Император Девяти Небес
- **Prompt Injection Engine**:
  - When `translate_bubbles_batch` is called, it must resolve the manga's `glossary.json`, format the glossary table into the system prompt for Ollama and OpenRouter, and enforce dictionary replacements before returning.

---

## 5. Deep Dive: High-Speed ML Inference Singleton (R3)

### 5.1 Current ML Lifecycle Deficiencies
- `ocr_engine.py` initializes EasyOCR via a module global variable `_reader = None` on CPU without GPU acceleration checks or multi-worker concurrency.
- Inpainting and typesetting are invoked synchronously per page.
- There is no central model manager to preload weights or keep them resident across requests.

### 5.2 Required `ModelInferenceManager` Specification
```
backend/agents/model_inference_manager.py
```
- **Singleton Pattern**:
  - `ModelInferenceManager.get_instance()` initializes once upon application startup.
  - Preloads:
    1. EasyOCR Reader (English + Chinese/Japanese models with GPU detection `torch.cuda.is_available()`).
    2. Manga-OCR (if enabled) / Inpainting models (Telea / Fast Inpaint).
    3. Font cache for PIL FreeTypeFont objects.
- **Dual Execution Pool**:
  - `io_executor = ThreadPoolExecutor(max_workers=4)` for disk I/O, image loading/saving, and network LLM calls.
  - `cpu_executor = ProcessPoolExecutor(max_workers=min(4, os.cpu_count()))` for CPU-bound OpenCV inpainting and morphology operations.
- **Performance Benchmark Target**:
  - Standard chapter (12–15 pages): Full OCR + Inpainting + Translation + Typesetting in **60–120 seconds**.

---

## 6. Deep Dive: Chapter Integrity Auditor & Scraper Resiliency (R3)

### 6.1 Chapter Status Audit for "The Ultimate of All Ages" (531 to 542)

| Chapter | RAW Scans (v1) | Cleaned (v2) | Translated (v3) | ZIP Archive | Integrity Status |
|---|---|---|---|---|---|
| **Chapter 531** | 12 pages | 12 pages | 12 pages | Present (`.zip`) | 🟢 Complete (Ready) |
| **Chapter 532** | 13 pages | 13 pages | 13 pages | Present (`.zip`) | 🟢 Complete (Ready) |
| **Chapter 533** | 14 pages | 14 pages | 14 pages | Missing | 🟡 Need ZIP & Manifest |
| **Chapter 534** | 11 pages | 11 pages | 11 pages | Missing | 🟡 Need ZIP & Manifest |
| **Chapter 535** | 13 pages | 13 pages | 13 pages | Missing | 🟡 Need ZIP & Manifest |
| **Chapter 536** | 14 pages | 0 pages | 0 pages | Missing | 🔴 Needs v2/v3 Pipeline |
| **Chapter 537** | **4 pages** | 0 pages | 0 pages | Missing | ⚠️ **PAGE DEFICIT (< 8 pages)**; Needs Scraper Rotation |
| **Chapter 538** | **5 pages** | 0 pages | 0 pages | Missing | ⚠️ **PAGE DEFICIT (< 8 pages)**; Needs Scraper Rotation |
| **Chapter 539** | 9 pages | 0 pages | 0 pages | Missing | 🔴 Needs v2/v3 Pipeline |
| **Chapter 540** | 8 pages | 8 pages | 8 pages | Present (`.zip`) | 🟡 Complete; sync frontend metadata |
| **Chapter 541** | 12 pages | 0 pages | 0 pages | Missing | 🔴 Needs v2/v3 Pipeline |
| **Chapter 542** | 8 pages | 0 pages | 0 pages | Missing | 🔴 Needs v2/v3 Pipeline |

### 6.2 Chapter Integrity Auditor (`ChapterIntegrityChecker`)
To ensure full chapter completeness:
- **Deficit Detection**: Minimum threshold is $\ge 8$ pages per chapter.
- **Scraper Mirror Rotation**:
  1. Primary: Direct CDN (`cdn.black-clover.org`)
  2. Mirror 1: MangaKatana (`mangakatana.com/manga/the-ultimate-of-all-ages.24987/c{ch}`)
  3. Mirror 2: Comick / MangaDex API
  4. Mirror 3: Manhuatop / Manhwatop Playwright fallback
- **`pipeline_manifest.json` Specification**:
  Generated per chapter (`backend/data/manga/{title}/{chapter}/pipeline_manifest.json`):
  ```json
  {
    "manifest_version": "3.0.0",
    "manga": "The_Ultimate_of_All_Ages",
    "chapter": "531",
    "total_pages": 12,
    "timestamp": 1787394182,
    "checksums": {
      "v1_original": { "page_001.webp": "sha256...", ... },
      "v2_cleaned": { "page_001.webp": "sha256...", ... },
      "v3_translated": { "page_001.webp": "sha256...", ... }
    },
    "qa_verification": {
      "anti_patch_guard": "PASSED",
      "max_ssim_diff": 0.0021,
      "text_boundary_leak_pixels": 0
    }
  }
  ```

---

## 7. Actionable Implementation Plan for Builder

### Step 1: Glossary Creation & Injection
1. Write `backend/data/manga/The_Ultimate_of_All_Ages/glossary.json` with the canonical translation dictionary.
2. Update `backend/agents/llm_translator.py` to automatically load the glossary for the given manga and format it into the system prompt for Ollama and OpenRouter.

### Step 2: Anti-Patch Guard Validator
1. Create `backend/tests/anti_patch_guard.py` implementing:
   - `test_solid_patch_detector()`: Low-variance bounding box check on `v2_cleaned` and `v3_translated`.
   - `test_background_ssim_diff()`: SSIM comparison between `v1_original` and `v3_translated` outside speech bubbles ($\le 0.5\%$ degradation).
   - Test execution on Chapter 531 Pages 2 and 8.

### Step 3: ModelInferenceManager Singleton
1. Implement `backend/agents/model_inference_manager.py` with singleton pattern, preloaded EasyOCR Reader, and dual thread/process pools.
2. Refactor `ocr_engine.py` and `manga_pipeline_service.py` to utilize `ModelInferenceManager`.

### Step 4: Topological Bubble Sorting Refinement
1. Update `ocr_engine.py` to sort bubbles by $y_{\text{center}} \times 10000 + x_{\text{center}}$.

### Step 5: ChapterIntegrityChecker & Scraper Mirror Rotation
1. Implement `backend/agents/chapter_integrity_checker.py`.
2. Re-scrape chapters with page deficits (Chapters 537 & 538) using mirror rotation until $\ge 8$ pages are fetched.
3. Process remaining chapters (536, 537, 538, 539, 541, 542) through full v1 $\to$ v2 $\to$ v3 pipeline.
4. Generate `pipeline_manifest.json` and `.zip` archives for all chapters 531–542.
5. Clean up stray folders in `frontend/public/manga/` and update `chapters_index.json`.
