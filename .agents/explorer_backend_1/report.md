# Comprehensive Backend Codebase Survey & Gap Analysis Report

**Project**: «Manga AI Translator Studio»  
**Auditor**: Backend Codebase Explorer (`explorer_backend_1`)  
**Date**: 2026-08-23  
**Status**: Investigation Complete — Read-Only Mode  

---

## 1. Executive Summary

An exhaustive investigation of the backend subsystem located in `backend/` was conducted to evaluate the pipeline architecture, server endpoints, LLM failover cascade, inpainting/typesetting engines, and test suite integrity against the authoritative specification (`ORIGINAL_REQUEST.md` and `AGENTS.md`).

### Key Findings at a Glance:
1. **Core Pipeline Architecture (`backend/agents/manga_pipeline_service.py`)**: Solid 5-stage orchestration design exists with thread-safe task registry, multi-directory synchronization (`frontend/public/manga` and `backend/data/manga`), and fast singleton inference integration via `ModelInferenceManager`.
2. **Inpainting Anti-Patch Compliance**: **100% compliant**. Zero instances of `cv2.rectangle` solid box fills exist in active pipeline code. All text cleaning is performed strictly using adaptive per-pixel thresholding and `cv2.inpaint(..., inpaintRadius=4, flags=cv2.INPAINT_TELEA)`. Background SSIM degradation is $\le 0.2\%$ across all tested chapters.
3. **Elliptical Typesetting Math**: The chord formula $W(y) = 2a\sqrt{1 - (y/b)^2}$ is accurately implemented in `translator_typesetter_agent.py` lines 70–76, bounded within $\le 85\%$ safe oval limits with binary search font sizing ($12\text{px} \to 38\text{px}$) and dynamic auto-contrast.
4. **LLM Cascade Gaps**: While Google Gemini 2.5 Flash and Groq (Qwen 3.6 / GPT-OSS 120B) are implemented, OpenRouter and DeepSeek adapters are **unimplemented** in `llm_translator.py` despite being present in `.env` and `config/translation_providers.json`.
5. **Real-time Telemetry (SSE) Gap**: Live telemetry is currently simulated on the frontend via polling `setInterval` against `/api/studio/tasks/{id}`; no genuine Server-Sent Events (`text/event-stream`) streaming endpoint exists in FastAPI.
6. **CLI & Turnkey Scripts Missing**: Unified CLI `backend/cli.py` (with `--title <title> --chapters <range> [--auto-deploy]`) and root launch scripts (`start_service.bat` / `start_service.sh`) are **not yet created**.
7. **Server Redundancy**: Dual entry points (`backend/server.py` and `backend/main.py`) exist with divergent route schemas, causing fragmentation between reader and studio frontend requests.

---

## 2. Codebase Architecture & File Inventory

### 2.1 Directory Structure Overview
```
backend/
├── .env                              # Environment secrets (GEMINI, GROQ, OPENROUTER, DEEPSEEK)
├── main.py                           # Legacy/Extended FastAPI server (ports /api/studio, /api/chapters)
├── server.py                         # Clean FastAPI server (ports /api/health, /api/translate-chapter, /api/status)
├── pipeline_runner.py                # Single-page/single-chapter CLI runner
├── requirements.txt                  # Python dependencies
├── config/
│   └── translation_providers.json    # Provider configuration schemas
├── assets/fonts/
│   └── ComicNeue-Bold.ttf            # Bundled fallback font
├── agents/
│   ├── manga_pipeline_service.py     # Central unified pipeline service & task manager
│   ├── model_inference_manager.py    # Singleton model inference (EasyOCR, MangaOCR, InpaintingEngine)
│   ├── comic_bubble_detector.py      # Bubble vs SFX Classifier & Glyph Mask extractor
│   ├── cleaner_agent.py              # Adaptive per-pixel Telea inpainter (0 cv2.rectangle)
│   ├── translator_typesetter_agent.py# Elliptical chord text-fitting & typography
│   ├── llm_translator.py             # SOTA LLM translation with glossary injection
│   ├── scanlation_memory_miner.py    # 10-chapter terminology graph miner
│   ├── chapter_integrity_checker.py  # Manifest v3.0.0, deficit resolver, parity auditor
│   ├── ocr_engine.py                 # 2-Pass OCR, Containment NMS, Figure-8 splitter
│   ├── qa_inspector_agent.py         # QA metrics validator
│   ├── scraper_agent.py              # Downloader & mirror scraper
│   └── translations_db.json          # Persistent translation cache
├── data/manga/                       # Canonical manga storage layout
│   └── The_Ultimate_of_All_Ages/
│       ├── glossary.json
│       ├── glossary_memory.json
│       └── chapter_531 ... 542/
│           ├── v1_original/
│           ├── v2_cleaned/
│           ├── v3_translated/
│           ├── pipeline_manifest.json
│           └── The_Ultimate_of_All_Ages_Chapter_XXX_Russian.zip
└── tests/
    ├── anti_patch_guard.py           # SSIM & Solid Patch Quality Guard
    ├── bubble_benchmark_100.py       # 100-Bubble archetype benchmark suite
    ├── test_typesetter_layout.py     # Elliptical typesetting & auto-contrast unit tests
    ├── test_glossary_and_topology.py # Glossary injection & reading order tests
    └── test_model_inference_and_integrity.py # Singleton & manifest generation tests
```

---

## 3. Deep-Dive Subsystem Analysis

### 3.1 Core Pipeline Service (`backend/agents/manga_pipeline_service.py`)
- **Lifecycle Execution**:
  1. `process_page()`: RAW Ingestion $\to$ 2-Pass OCR & NMS $\to$ Telea Inpainting $\to$ LLM Translation $\to$ Typesetting $\to$ Metadata synchronization.
  2. `process_chapter()`: Batch-processes entire chapter directories with natural numeric page sorting (`re.split(r'(\d+)', s)`).
  3. `create_task()` & `run_pipeline_async()`: Background execution using `ThreadPoolExecutor(max_workers=2)`. State tracked in `active_tasks: Dict[str, Dict[str, Any]]`.
- **Strengths**: Robust thread-safe isolation, concurrent public and backend data synchronization, natural page sorting.
- **Architectural Gaps**:
  - `MangaPipelineService.process_chapter()` does not automatically call `ChapterIntegrityChecker.generate_pipeline_manifest()`; `pipeline_manifest.json` is generated separately in `ChapterIntegrityChecker`.
  - Task progress callback emits coarse updates (10%, 15–90%, 95%, 100%) rather than fine-grained sub-step telemetry (`[Page X/Y] 2-Pass OCR -> Telea Inpaint -> Batch LLM -> Typeset`).

---

### 3.2 FastAPI Servers & Routing Fragmentation
Currently, there are two distinct server files in `backend/`:

| Endpoint | `backend/server.py` | `backend/main.py` | Frontend Consumer |
|---|---|---|---|
| `GET /api/health` | ✅ Present | ❌ Missing | Healthchecks & startup scripts |
| `GET /api/chapters/{manga}` | ❌ Missing | ✅ Present | Reader page |
| `GET /api/studio/mangas` | ❌ Missing | ✅ Present | Studio dashboard |
| `POST /api/studio/translate` | ❌ Missing | ✅ Present | Studio dashboard |
| `POST /api/studio/upload` | ❌ Missing | ✅ Present | Studio dashboard drag-and-drop |
| `GET /api/studio/tasks/{id}` | ❌ (`/api/status/{id}`) | ✅ Present | Studio dashboard progress polling |
| `GET /api/studio/download/...` | ✅ `/download/{manga}/{ch}/{layer}` | ✅ `/download/{manga}/{ch_folder}/{ver}` | Studio / Reader ZIP downloads |
| `GET /api/pipeline/stream/{id}` (SSE) | ❌ Missing | ❌ Missing | Required by Requirement R3 |

**Critical Architectural Recommendation**: Merge `backend/server.py` and `backend/main.py` into a unified `backend/server.py` (or router-based structure) that implements all endpoints, standardizes URL paths, mounts static storage, and introduces genuine SSE streaming.

---

### 3.3 LLM Cascade, Failover & Terminology Graph Injection

#### Credential Loading & Security
- Loaded from `backend/.env` or root `.env` via `llm_translator.py` lines 28–36.
- Secret keys are kept strictly on the backend and are not forwarded to frontend responses.

#### Provider Failover Chain (`llm_translator.py`)
- **Current Cascade Order**:
  1. Google Gemini 2.5 Flash (`translate_with_gemini`, lines 215–257)
  2. Groq Qwen 3.6 / GPT-OSS 120B (`translate_with_groq`, lines 258–305)
  3. Local Xianxia Glossary Fallback (`fallback_translate_text`, lines 96–107)
- **Gaps**:
  - **OpenRouter Gateway Missing**: OpenRouter (`https://openrouter.ai/api/v1/chat/completions`) with Claude 3.5 Sonnet / Qwen 2.5 72B is configured in `translation_providers.json` and `.env` but has no implementation method in `SOTALLMTranslator`.
  - **DeepSeek Gateway Missing**: DeepSeek API adapter is omitted.
  - **Failover Order**: Should be: OpenRouter $\to$ Gemini 2.5 Flash $\to$ Groq Qwen 3.6 $\to$ Local Xianxia fallback.

#### Terminology Graph Injection (`scanlation_memory_miner.py`)
- Mined graph is persisted to `backend/data/manga/{title}/glossary_memory.json`.
- Contains 16+ canonical characters, 22+ cultivation terms, 7+ factions/places, and 4 strict localization rules.
- Injected into system prompts with strict 1-based sequential integer ID contracts (`[{"id": 1, "translated": "..."}]`).
- Parsing is fortified with markdown fence removal, trailing comma sanitization, and regex fallback in `parse_llm_json_response()`.

---

### 3.4 Inpainting & Typesetting Quality Verification

#### Anti-Patch Policy (Zero `cv2.rectangle`)
- **Inspection Result**: PASSED.
- In `cleaner_agent.py`:
  - `clean_speech_bubble_seamless()` extracts ROI with 6px padding.
  - Computes Otsu threshold combined with Euclidean color distance (`color_diff > 25`).
  - Dilates by 2 iterations with elliptical $3\times3$ structuring element.
  - Preserves 2px boundary for genuine reference pixels.
  - Invokes `cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)`.
  - **Zero instances of `cv2.rectangle` or solid color fills.**

#### Elliptical Chord Equation & Typography (`translator_typesetter_agent.py`)
- **Equation**:
  $$\text{allowed\_w}(y) = 2a \sqrt{1 - \left(\frac{y}{b}\right)^2}$$
  Implemented in `wrap_text_elliptic()` (lines 70–76):
  ```python
  y_mid = - (total_text_h / 2.0) + i * line_step + (line_h / 2.0)
  u = abs(y_mid) / max(1.0, b_semi)
  allowed_w = int(2.0 * a_semi * math.sqrt(1.0 - u * u)) if u < 1.0 else 0
  ```
- **Bounds & Padding**: Text is strictly contained within 85% oval boundaries (`safe_w = int(w * 0.85)`).
- **Auto-Contrast**: Calculates background crop luminance; uses black text on light backgrounds ($\text{luma} \ge 120$) and white text with 1.5–2px black stroke on dark backgrounds ($\text{luma} < 120$).
- **Cross-Platform Font Fallback**: Font dictionary in `translator_typesetter_agent.py` lines 19–25 points to `C:\Windows\Fonts\...`. To ensure seamless execution on Linux/macOS/Docker, fallback to `backend/assets/fonts/ComicNeue-Bold.ttf` or bundled fonts is recommended.

---

## 4. Requirement Compliance & Gap Matrix

| Requirement | Description | Current Status | Identified Gap / Required Action |
|---|---|---|---|
| **R1** | Autonomous Turnkey Launch & CLI | ⚠️ **Partial** | Missing `start_service.bat`, `start_service.sh`, and unified multi-chapter CLI `backend/cli.py` (`--title`, `--chapters 531-532`, `--auto-deploy`). |
| **R2** | Zero-Config LLM Cascade Failover | ⚠️ **Partial** | OpenRouter and DeepSeek adapters are missing in `llm_translator.py`; only Gemini and Groq are wired. Failover cascade should support all 4 providers. |
| **R3** | Real-Time Telemetry & SSE | ⚠️ **Partial** | FastAPI server lacks SSE streaming endpoint (`/api/pipeline/stream/{task_id}`). Frontend uses polling. Need true SSE endpoint with fine-grained sub-step telemetry. |
| **R4** | Production ZIP & Instant Downloads | ⚠️ **Partial** | ZIP generation exists in `ChapterIntegrityChecker` & `MangaPipelineService`, but Reader header lacks the prominent «Скачать главу (ZIP)» button, and studio dashboard uses static path. |
| **R5** | SOTA Glyph Inpainting & Elliptical Typesetting | ✅ **Complete** | Zero `cv2.rectangle` usage; per-pixel Telea inpainting; elliptical chord formula $W(y)$; 100/100 bubble benchmark passing; 18/18 unit tests passing. |

---

## 5. Test Suite Verification Summary

| Test Suite | Command | Result | Details |
|---|---|---|---|
| **Unit Test Discovery** | `python -m unittest discover -s backend/tests` | **18/18 PASS** | Verified singleton inference, SHA-256 manifests, deficit resolver, glossary injection, topological sorting. |
| **100-Bubble Benchmark** | `python backend/tests/bubble_benchmark_100.py` | **7/7 PASS (100/100)** | 20 Light Oval, 20 Dark Inverted, 15 Spiky Shout, 15 Floating, 10 System Window, 10 SFX Art (0 corruption), 10 Thought Clouds. |
| **Anti-Patch Guard (Full Scan)** | `python backend/tests/anti_patch_guard.py --all` | **13/13 Chapters PASS (100%)** | All 13 chapters (`Test_Manga` + Ch.531–542) verified with 0 solid patch violations and background SSIM $\ge 99.8\%$. |
| **Anti-Patch Guard (Synthetic)** | `python backend/tests/anti_patch_guard.py --test-synthetic` | **3/3 PASS** | Correctly validates genuine inpainting, reliably detects `cv2.rectangle` solid fills, catches background degradation. |
| **Frontend TypeScript Build** | `cd frontend && npx tsc --noEmit` | **0 Errors** | TypeScript strictly clean. |

---

## 6. Actionable Implementation Blueprint for Builder

To bring the backend to 100% compliance with R1–R5, the following specific tasks are recommended:

1. **Implement `backend/cli.py`**:
   - Add argument parsing: `--title <title>`, `--chapters <range>` (supports `531-532`, `531,532`, `all`), `--auto-deploy` (triggers frontend sync and global index update).
   - Integrate with `MangaPipelineService` and `ChapterIntegrityChecker`.

2. **Add Startup Scripts (`start_service.bat` & `start_service.sh`)**:
   - Launch FastAPI backend (`uvicorn server:app --port 8000`) and Next.js frontend (`npm run dev -- -p 3000`).
   - Include automated curl/python healthchecks against `http://localhost:8000/api/health` and `http://localhost:3000`.

3. **Consolidate FastAPI Server & Add SSE Streaming (`backend/server.py`)**:
   - Merge routes from `main.py` into `server.py`.
   - Add SSE endpoint: `GET /api/pipeline/stream/{task_id}` yielding real-time events (`data: {"progress": ..., "step": "...", "log": "..."}\n\n`).
   - Standardize ZIP download route: `GET /api/studio/download/{manga}/{chapter}/v3` returning `{manga}_Chapter_{num}_Russian.zip`.

4. **Expand LLM Failover Cascade (`backend/agents/llm_translator.py`)**:
   - Implement `translate_with_openrouter()` and `translate_with_deepseek()`.
   - Wire multi-tier cascade: OpenRouter $\to$ Gemini 2.5 Flash $\to$ Groq (Qwen 3.6 / GPT-OSS 120B) $\to$ Local Xianxia fallback.

5. **Enhance Cross-Platform Font Fallbacks (`backend/agents/translator_typesetter_agent.py`)**:
   - Add check for `backend/assets/fonts/` bundled TTF fonts when Windows system font directory is not present.
