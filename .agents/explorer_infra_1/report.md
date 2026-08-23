# Comprehensive Survey Report: Testing Infrastructure, CLI & Startup Scripts
**Project**: Manga AI Translator Studio  
**Explorer Role**: Test, CLI & Infrastructure Spec Miner  
**Date**: 2026-08-23  
**Integrity Mode**: Development / Specification Mining  

---

## Executive Summary

An exhaustive inspection of the testing suites, CLI tools, service startup scripts, and dataset storage layers was performed across `backend/`, `frontend/`, `tests/`, and root directories.

The core computer vision inpainting algorithms, SOTA OCR filtering, and topological typesetting modules exhibit outstanding quality and mathematical compliance (SSIM $\ge 99.5\%$, 100/100 bubble benchmark archetypes passing, 18/18 discoverable unit tests passing, and 0 TypeScript compilation errors in Next.js).

However, key infrastructure integration components required by **R1**, **R4**, and the Acceptance Criteria are currently **missing or have defects**:
1. **Missing CLI Tool**: `backend/cli.py` is completely absent.
2. **Missing Startup Scripts**: `start_service.bat` (Windows) and `start_service.sh` (Linux/macOS) are absent.
3. **Broken Test Import**: `backend/tests/verify_pipeline.py` fails immediately on import (`ImportError: cannot import name 'extract_json_array' from 'agents.llm_translator'`).
4. **Test Discovery Inconsistencies**: `test_typesetter_layout.py` defines bare functions rather than `unittest.TestCase` methods, and `bubble_benchmark_100.py` lacks the `test_*.py` filename prefix, meaning standard `unittest discover` does not automatically include them.
5. **Audit File Path Optimization**: `anti_patch_guard.py` queries `meta.json` in backend data directories (where only `pipeline_manifest.json` exists), triggering expensive OCR re-inference fallbacks during full audit sweeps.

---

## 1. Testing Infrastructure Survey

### 1.1 `anti_patch_guard.py` (Anti-Patch & Visual Layer Quality Guard)
- **Location**: `backend/tests/anti_patch_guard.py` (806 lines)
- **Role**: Programmatic quality validator enforcing strict visual layer integrity for Manga AI Translator.
- **CLI Interface**:
  ```bash
  python backend/tests/anti_patch_guard.py --manga The_Ultimate_of_All_Ages --chapter chapter_531 --pages 2 8
  python backend/tests/anti_patch_guard.py --all
  python backend/tests/anti_patch_guard.py --test-synthetic
  python backend/tests/anti_patch_guard.py --json-output <path>
  ```
- **Validation Mechanics**:
  1. **Check A (Solid Patch Detector)**:
     - Inspects bounding boxes and cleaned regions in `v2_cleaned`.
     - Computes color variance per channel ($\sigma^2$).
     - Implements a sliding window ($16\times 16$ px sub-patches with step 8) to detect localized solid rectangle fills ($\sigma^2 < 1.0$).
     - Evaluates bubble context (dark contour outline `np.any(gray < 90)` or light gutter `mean > 235, std < 20`).
     - Computes Sobel gradient magnitude (`mag < 1.0`) and connected component flat ratio & flat contrast to catch solid rectangle fills (`cv2.rectangle`) while permitting natural Telea/LaMa inpainting gradients.
  2. **Check B (Background SSIM Difference)**:
     - Computes Structural Similarity Index (SSIM) between `v3_translated` and `v1_original` on non-bubble background pixels (padded by 12 px outside bubble bounding boxes).
     - Enforces background degradation threshold $\le 0.5\%$ (i.e. background SSIM $\ge 0.995$).
     - Supports scikit-image `structural_similarity` with a pure NumPy fallback Gaussian window implementation.
- **Synthetic Test Verification (`--test-synthetic`)**:
  - `Test 1` (Genuine Inpainting): PASS (Check A & B passed).
  - `Test 2` (Solid Rectangle Detection): PASS (Flagged 1 violation with var=0.0).
  - `Test 3` (Background Degradation Detection): PASS (Detected degradation 2.99%, SSIM 0.970).
  - Verdict: **100% PASS** in 0.6s.
- **Dataset Audit Verification (`--all`)**:
  - Automatically invokes `ensure_chapters_pipeline_processed()` for chapter deficit resolution, Schema v3.0.0 manifest generation, and ZIP packaging.
  - Audits 13 chapters across `The_Ultimate_of_All_Ages` (12 chapters: 531–542) and `Test_Manga` (1 chapter: ch 1).
  - Pre-generated audit output in `backend/tests/anti_patch_report.json` confirms:
    - Total chapters audited: **13 / 13**
    - `global_passed`: `true`
    - Mean background SSIM: `0.9985 - 0.9997` ($> 0.995$)
    - Degradation: `0.03% - 0.15%` ($< 0.5\%$)
    - Zero patch violations detected.

---

### 1.2 `bubble_benchmark_100.py` (100-Bubble Comprehensive Benchmark Suite)
- **Location**: `backend/tests/bubble_benchmark_100.py` (235 lines)
- **Role**: Validates region classification (`SPEECH_BUBBLE` vs `SFX_ART`), text glyph mask extraction, and noise isolation across 100 synthetic and realistic bubble archetypes.
- **7 Evaluation Categories**:
  | # | Category | Count | Tested Archetype | Expected Classification | Mask Validation | Status |
  |---|----------|-------|------------------|-------------------------|-----------------|--------|
  | 1 | Standard Oval Light Bubbles | 20 | Normal dialogue (e.g. "Hello, how are you?") | `SPEECH_BUBBLE` | $\sum \text{mask} > 0$ | PASS |
  | 2 | Inverted Dark Bubbles | 20 | White text on dark/combat backgrounds (e.g. "DIE, TRAITOR!") | `SPEECH_BUBBLE` | $\sum \text{mask} > 0$ | PASS |
  | 3 | Spiky Shout / Scream Bubbles | 15 | Jagged polygon contours (e.g. "WATCH OUT!!") | `SPEECH_BUBBLE` | Contour preserved | PASS |
  | 4 | Floating Borderless Text | 15 | Narration lines on art gradients | `SPEECH_BUBBLE` | Classified as text | PASS |
  | 5 | System / Skill Windows | 10 | Rectangular UI boxes (`[Skill: Nine Heavens Palm]`) | `SPEECH_BUBBLE` | Box & text isolated | PASS |
  | 6 | Action SFX & Noise Artifacts | 10 | 'G2', 'hx KY', '0g09', 'BOOM', 'SLASH', 'WHOOSH' | `SFX_ART` | Must NOT be inpainted/stamped | PASS |
  | 7 | Thought Clouds | 10 | Semi-transparent thought bubbles with parentheses | `SPEECH_BUBBLE` | Clean extraction | PASS |
- **Execution Command & Result**:
  ```bash
  python backend/tests/bubble_benchmark_100.py
  # Result: Ran 7 tests in 0.745s -> OK (100/100 passed, 0 art corruptions)
  ```

---

### 1.3 Unit Tests Inventory in `backend/tests/`

| Test File | Test Suite Class | Tests Count | Focus / Coverage | Execution Result |
|-----------|------------------|-------------|-------------------|------------------|
| `test_adversarial_challenger_1.py` | `TestAdversarialVisionPipeline` | 5 | Complex gradients, 16-point spiky polygons, overlapping chained bubbles, SFX rejection (`BOOM`, `G2`, `hx KY`), Anti-Patch Guard attack scenarios | **PASS (5/5)** |
| `test_glossary_and_topology.py` | `TestGlossaryAndTopology` | 5 | Glossary loading ($\ge 30$ Xianxia terms), prompt injection, topological sort math ($y_{\text{center}} \times 10000 + x_{\text{center}}$), 1-based sequential ID preservation in batch JSON, offline fallback Xianxia translation | **PASS (5/5)** |
| `test_model_inference_and_integrity.py` | `TestModelInferenceAndIntegrity` | 8 | `ModelInferenceManager` Singleton & dual executors, OCR/Inpainting engine access, SHA-256 hash calculation, gutter-cut webtoon panel slicing math, chapter deficit expansion to $\ge 8$ pages, Schema v3.0.0 manifest generation, ZIP archive creation & frontend sync, chapter audit flow | **PASS (8/8)** |
| `test_typesetter_layout.py` | Standalone functions | 2 | Circular bubble fitting with 12-word Russian text within $r \le 88\%$ ($< 63.75$ px radius), dark bubble auto-contrast | **PASS (2/2)** when run directly |
| `verify_pipeline.py` | Standalone QA Script | 5 | OCR & numbering, smart inpainting, LLM JSON integrity, typesetting bounds, E2E pipeline run | **FAIL on import** (`extract_json_array` missing) |

- **Unittest Discovery Run**:
  ```bash
  python -m unittest discover -s backend/tests -v
  # Output: Ran 18 tests in 19.883s -> OK
  ```
  *(18 discoverable tests = 5 from `test_adversarial_challenger_1` + 5 from `test_glossary_and_topology` + 8 from `test_model_inference_and_integrity`)*

---

### 1.4 Frontend TypeScript Quality Guard
- **Command**: `cd frontend && npx tsc --noEmit`
- **Result**: **0 TypeScript compilation errors** (Exit code 0).

---

## 2. CLI Tools Survey

### 2.1 Missing `backend/cli.py`
Per Requirement **R1** and the Acceptance Criteria:
> Provide a unified CLI interface `python backend/cli.py --title <title> --chapters <range> [--auto-deploy]` enabling both human power users and Antigravity AI agents to process multi-chapter translation batches without chat overhead.

#### Current State
- `backend/cli.py` does **NOT exist**.
- Existing partial runner: `backend/pipeline_runner.py` (takes `--input`, `--title`, `--chapter`, `--page`, `--output`), which does not support multi-chapter range arguments (e.g. `531-532`, `531,532`, `all`), does not support `--auto-deploy`, and cannot be invoked as specified by Acceptance Criteria:
  `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532`

#### Specification for `backend/cli.py` Implementation
1. **Command Line Interface**:
   - `--title <str>`: Title of manga (e.g. `The_Ultimate_of_All_Ages` or `"The Ultimate of All Ages"`).
   - `--chapters <str>`: Chapter specification:
     - Hyphen range: `531-535`
     - Comma-separated list: `531,532,534`
     - Single chapter: `531`
     - Keyword: `all`
   - `--auto-deploy`: Boolean flag. When set, automatically executes `ChapterIntegrityChecker.sync_to_frontend()`, updates `chapters_index.json`, and generates verified release archives `{title}_Chapter_{num}_Russian.zip`.
   - `--workers <int>`: Optional concurrent worker threads (default: 4).
   - `--force`: Optional flag to force re-processing existing layers.
2. **Execution Flow**:
   - Parse `--chapters` into a sorted list of integer chapter numbers.
   - For each chapter:
     - Check local source directory `backend/data/manga/{title}/chapter_{num}/v1_original`.
     - If empty/missing and scraper available, trigger `ScraperAgent.download_chapter()`.
     - Execute multi-stage pipeline via `ModelInferenceManager.get_instance().process_chapter_concurrent()`:
       1. 2-Pass OCR & Bubble Segmentation.
       2. Per-pixel Telea Inpainting -> `v2_cleaned`.
       3. LLM Translation with glossary injection.
       4. Elliptical typeset -> `v3_translated`.
     - Generate Schema v3.0.0 `pipeline_manifest.json` with SHA-256 checksums.
     - Generate production release ZIP `{title}_Chapter_{num}_Russian.zip`.
   - If `--auto-deploy` or by default:
     - Sync chapters to `frontend/public/manga/{title}/`.
     - Update `frontend/public/manga/chapters_index.json`.
3. **Exit Codes & Output**:
   - Exit code `0` on successful completion of all requested chapters.
   - Non-zero exit code (`1`) on fatal processing failure.
   - Clean tabular progress report logged to stdout.

---

## 3. Startup Scripts Survey

### 3.1 Missing `start_service.bat` and `start_service.sh`
Per Requirement **R1** and Acceptance Criteria:
> Provide one-click startup scripts (`start_service.bat` for Windows and `start_service.sh` for Linux/macOS) that launch both FastAPI backend and Next.js frontend with automated healthchecks.

#### Current State
- Neither `start_service.bat` nor `start_service.sh` exists in the repository root.

#### Specification for `start_service.bat` (Windows)
1. **Environment Checks**:
   - Check for Python 3.10+ installation.
   - Check if `backend/venv` exists; if not, create virtualenv `python -m venv backend/venv` and install `backend/requirements.txt`.
   - Check if Node.js and npm are available.
   - Check if `frontend/node_modules` exists; if not, run `npm install` inside `frontend/`.
2. **Process Orchestration**:
   - Start FastAPI backend in background:
     `start "Manga Backend Server" /min cmd /c "backend\venv\Scripts\python.exe backend\server.py"`
   - Start Next.js frontend:
     `start "Manga Next.js Frontend" /min cmd /c "cd frontend && npm run dev"`
3. **Automated Healthchecks**:
   - Poll `http://localhost:8000/api/health` via PowerShell `Invoke-RestMethod` until status is `"online"` (max 30s timeout).
   - Poll `http://localhost:3000` until frontend returns HTTP 200.
4. **User Experience**:
   - Print clean ANSI/Unicode status banner indicating:
     - Backend API URL: `http://localhost:8000`
     - Web Reader Studio URL: `http://localhost:3000`
     - Health Status: `ONLINE`
   - Open default web browser to `http://localhost:3000`.

#### Specification for `start_service.sh` (Linux / macOS)
1. **Environment Checks**:
   - Verify `python3`, `python3-venv`, `node`, `npm`.
   - Setup `backend/venv` and install `requirements.txt` if needed.
   - Run `npm install` in `frontend/` if `node_modules` is missing.
2. **Process Orchestration & Trap**:
   - Start backend: `backend/venv/bin/python backend/server.py & BACKEND_PID=$!`
   - Start frontend: `(cd frontend && npm run dev) & FRONTEND_PID=$!`
   - Setup trap `trap 'kill $BACKEND_PID $FRONTEND_PID; exit' SIGINT SIGTERM EXIT`.
3. **Automated Healthchecks**:
   - Loop with `curl -s -f http://localhost:8000/api/health` and `curl -s -f http://localhost:3000`.
4. **Display Banner**:
   - Output active endpoints and tail logs.

---

## 4. Manga Chapter Data & Storage Survey

### 4.1 Storage Inventory in `backend/data/manga/`
Total Manga Titles: **2**  
Total Chapters: **13**

| Title | Chapters List | Total Chapters | 3-Layer Structure | Manifest v3.0.0 | Release ZIPs |
|-------|---------------|----------------|-------------------|-----------------|--------------|
| `The_Ultimate_of_All_Ages` | `chapter_531` through `chapter_542` | 12 | `v1_original`, `v2_cleaned`, `v3_translated` present in all 12 chapters | Present in each chapter | Both `{title}_Chapter_{num}_Russian.zip` and `{title}_chapter_{num}_v3.zip` present |
| `Test_Manga` | `chapter_1` | 1 | `v1_original`, `v2_cleaned`, `v3_translated` present | Present | Release ZIP present |

### 4.2 Layer Validation Details
1. **`v1_original`**: High-resolution source manga pages (`.webp`).
2. **`v2_cleaned`**: Inpainted pages with text removed via per-pixel glyph masks; speech bubble borders and backgrounds preserved with zero solid color rectangles.
3. **`v3_translated`**: Typeset pages with Russian text fitted using elliptical chord boundaries ($W(y) = 2a\sqrt{1-(y/b)^2}$), dynamic font scaling, and auto-contrast.
4. **Sidecar Files**:
   - `pipeline_manifest.json`: Follows Schema version `3.0.0` with page dimensions, cluster counts, and SHA-256 hashes per image layer.
   - `The_Ultimate_of_All_Ages_Chapter_XXX_Russian.zip`: Verified standalone Russian chapter release package.
   - `glossary.json` & `glossary_memory.json`: 30+ canonical Xianxia entity names, cultivation stages, and locations.
5. **Frontend Mirror (`frontend/public/manga/`)**:
   - Synced with 12 chapters under `frontend/public/manga/The_Ultimate_of_All_Ages/chapter_XXX/` with subfolders `v1/`, `v2/`, `v3/`, and `meta.json`.
   - `frontend/public/manga/chapters_index.json` maintains the central catalog index for the Next.js reader.

---

## 5. Discovered Gaps, Failing Tests & Defects

| # | Item / Component | Severity | Description / Observed Behavior | Acceptance Criteria Impact | Remediation Plan |
|---|------------------|----------|---------------------------------|----------------------------|------------------|
| 1 | `backend/cli.py` | **CRITICAL** | File does not exist. No multi-chapter CLI execution tool available. | Violates R1 & AC: `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532` | Create `backend/cli.py` supporting `--title`, `--chapters` range/list/all, `--auto-deploy`, multi-threaded batch inference, ZIP packaging, and frontend sync. |
| 2 | Startup Scripts | **CRITICAL** | `start_service.bat` and `start_service.sh` are missing from repo root. | Violates R1 & AC: Turnkey one-click launch scripts | Implement `start_service.bat` and `start_service.sh` with environment verification, background process management, and automated healthcheck polling. |
| 3 | `backend/tests/verify_pipeline.py` | **HIGH** | Fails with `ImportError: cannot import name 'extract_json_array' from 'agents.llm_translator'`. | Test suite failure on direct invocation | Update `verify_pipeline.py` to use `json.loads` or import the correct helper from `llm_translator.py`. |
| 4 | `test_typesetter_layout.py` | **MEDIUM** | Uses bare functions instead of `unittest.TestCase` class. Skipped during `unittest discover`. | Discovered unit tests count is 18 instead of 20 | Refactor `test_typesetter_layout.py` to wrap tests in `class TestTypesetterLayout(unittest.TestCase)` so they are included in discovery. |
| 5 | `bubble_benchmark_100.py` | **LOW** | Filename does not match `test_*.py` pattern. | Omitted from standard discovery, but runnable directly | Keep as dedicated benchmark script or add a test shim `test_bubble_benchmark_100.py` for standard discovery. |
| 6 | `anti_patch_guard.py` Metadata Lookup | **LOW** | Looks for `meta.json` in backend data folder instead of `pipeline_manifest.json`. | Triggers fallback OCR diffs, increasing audit time from ~10s to ~50s per chapter | Update `load_bubble_boxes` in `anti_patch_guard.py` to check `pipeline_manifest.json` or `frontend/public` `meta.json` first. |

---

## 6. Features Discovered Table

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Testing | Check A (Solid Patch Detector) | Mathematical detection of $\sigma^2 < 1.0$ solid fills and flat connected components | `cleaned_img`, `bubble_boxes` | Dict with `passed`, `violations`, `min_variance` | Flags violation if solid rectangular patch detected | `anti_patch_guard.py:99` |
| 2 | Testing | Check B (Background SSIM) | Structural similarity measurement on non-bubble background | `v1_img`, `v3_img`, `bubble_boxes` | Dict with `passed`, `bg_ssim`, `degradation_pct` | Flags violation if SSIM $< 0.995$ or degradation $> 0.5\%$ | `anti_patch_guard.py:221` |
| 3 | Testing | Synthetic Sanity Guard | Unit test verifying clean inpainting passes while solid patches & BG corruption fail | None | Boolean / stdout | Raises `AssertionError` if test fails | `anti_patch_guard.py:446` |
| 4 | Testing | 100-Bubble Archetype Benchmark | Comprehensive 7-category bubble & SFX classification suite | Synthetic crops & dialogue clusters | Test assertions & summary report | Fails if SFX misclassified or text glyphs missed | `bubble_benchmark_100.py:32` |
| 5 | Testing | Adversarial Vision Pipeline | Stress tests with radial gradients, acute spikes, chained bubbles, and combat SFX | Complex rendered images | `unittest` test results | Fails if gradient ruined or spikes clipped | `test_adversarial_challenger_1.py:32` |
| 6 | Testing | Glossary & Topology | Verification of 30+ Xianxia terms, prompt injection, and reading order sort | Entity dictionary & bubble coordinates | Verified translation mappings | Fails on term deviation or sort error | `test_glossary_and_topology.py:24` |
| 7 | Testing | Model Inference & Integrity | Singleton verification, dual thread pools, SHA-256 manifest, and deficit slicing | Synthetic chapter folders | Schema v3.0.0 manifests, ZIPs | Fails if chapter has $<8$ pages or invalid hash | `test_model_inference_and_integrity.py:37` |
| 8 | Testing | Typesetter Layout Constraints | Tests $r \le 88\%$ boundary limit and dark bubble auto-contrast | 12-word Russian text, bubble dimensions | Rendered image & pixel coordinates | Fails if text leaks outside oval radius | `test_typesetter_layout.py:17` |
| 9 | Service API | Healthcheck Endpoint | Returns service status, Ollama status, storage paths | GET `/api/health` | JSON with status, version, storage paths | HTTP 500 if server failure | `backend/server.py:52` |
| 10 | Service API | Chapter Translation Task API | Enqueues ZIP or image uploads for async processing | POST `/api/translate-chapter` | JSON with `task_id` and status URL | HTTP 400 if no images provided | `backend/server.py:68` |
| 11 | Service API | Task Status Polling | Live progress reporting for web client | GET `/api/status/{task_id}` | JSON with progress %, logs, state | HTTP 404 if task not found | `backend/server.py:161` |
| 12 | Service API | Release ZIP Download | Exposes endpoint to download chapter translation package | GET `/api/studio/download/{manga}/{chapter}/{layer}` | Application/ZIP file stream | HTTP 404 if chapter not ready | `backend/server.py:169` |
| 13 | Data Layer | Schema v3.0.0 Manifest | Canonical metadata manifest with SHA-256 checksums | Chapter image files | `pipeline_manifest.json` | Marks `FAILED` if layers inconsistent | `chapter_integrity_checker.py` |
| 14 | Data Layer | Multi-layer Chapter Storage | 3-layer physical separation (`v1_original`, `v2_cleaned`, `v3_translated`) | Chapter directories | 3 subdirectories per chapter | Raises exception if layer missing | `backend/data/manga/` |

---

## 7. Edge Cases Observed

| # | Feature | Input / Condition | Observed Behavior |
|---|---------|-------------------|-------------------|
| 1 | Bubble Classification | Short combat noise ('G2', 'hx KY', '0g09') | Correctly isolated as `SFX_ART`; zero inpainting or text stamping applied. |
| 2 | Speech Bubble Cleaning | Inverted dark bubble with internal gradient | Cleaned with per-pixel glyph mask; dark bubble background preserved with $\sigma^2 > 1.0$. |
| 3 | Typesetting Word Wrap | 12-word Russian text in $150\times 150$ circle | Max text pixel radius is $61.72$ px ($< 63.75$ px limit); $0$ pixels leak outside circle. |
| 4 | Webtoon Panel Slicing | Long strip image ($6000\times 800$ px) | `find_optimal_gutter_cuts()` successfully detects horizontal white gutter at $y=2400$ px and slices into valid panels. |
| 5 | Chapter Deficit Handling | Chapter with 4 pages ($< 8$ min threshold) | `resolve_chapter_deficit()` expands chapter to 12 pages via panel splitting and CDN fallback. |
| 6 | Unittest Discovery | `test_typesetter_layout.py` with standalone functions | `python -m unittest discover` skips the file because it does not subclass `unittest.TestCase`. |
| 7 | Pipeline Verification | `verify_pipeline.py` execution | Terminated with `ImportError: cannot import name 'extract_json_array'`. |
| 8 | Anti-Patch Guard Audit | `anti_patch_guard.py --all` on 13 chapters | All 13 chapters pass with background SSIM $> 0.995$ and 0 patch violations. |
