# Production Architecture & Technical Specification: «Manga AI Translator Studio»

**Version**: 4.0.0  
**Date**: 2026-08-23  
**Status**: APPROVED SPECIFICATION  

---

## 1. System Architecture Overview

The system is a production-grade, autonomous local Manga & Webtoon Translation Studio designed for high throughput, zero English dialogue leaks, strict visual layer preservation, and real-time observability.

```
[ Human User / CLI / Web Browser ]
                 │
  ┌──────────────┴──────────────┐
  ▼                             ▼
[ Next.js 16 Web Studio ]   [ CLI / Turnkey Scripts ]
(Reader / Studio Dashboard) (backend/cli.py / start_service)
  │                             │
  └──────────────┬──────────────┘
                 │ HTTP REST / SSE Stream
                 ▼
     [ FastAPI Backend Server ] (backend/server.py :8000)
                 │
                 ▼
   [ MangaPipelineService ] (ThreadPoolExecutor / Task Queue)
                 │
                 ├── 1. 2-Pass OCR & ComicBubbleDetector (NMS + SFX Classifier)
                 ├── 2. CleanerAgent (Per-Pixel Adaptive Telea Inpainter, 0 cv2.rectangle)
                 ├── 3. SOTALLMTranslator (OpenRouter -> Gemini -> Groq -> Xianxia Fallback)
                 │      └─ Injected with 10-Chapter Terminology Graph (glossary_memory.json)
                 ├── 4. TranslatorTypesetterAgent (Elliptical Chord W(y), Auto-Contrast, TTF)
                 └── 5. ChapterIntegrityChecker (Schema v3.0.0 Manifest, ZIP Packaging, Sync)
```

---

## 2. Milestone Decomposition & Contracts

### Milestone 1: CLI & Turnkey Scripts (R1)
- **`backend/cli.py`**:
  - Arguments: `--title <title>`, `--chapters <range>`, `--auto-deploy`, `--workers <num>`, `--force`.
  - Batch parsing: `531-532`, `531,532`, `all`.
  - Multiprocessing/threading integration with `MangaPipelineService`.
  - Automatic release ZIP generation and frontend deployment.
- **`start_service.bat` & `start_service.sh`**:
  - Automated environment checks (Python venv, Node modules).
  - Background dual process spawn (FastAPI on port 8000, Next.js on port 3000).
  - Automated curl / PowerShell healthchecks (`http://localhost:8000/api/health`, `http://localhost:3000`).

### Milestone 2: Multi-Provider LLM Cascade & Failover (R2)
- **`backend/agents/llm_translator.py`**:
  - Secure `.env` credential loading.
  - Multi-tier provider cascade:
    1. OpenRouter (`https://openrouter.ai/api/v1/chat/completions`, Claude 3.5 Sonnet / Qwen 2.5 72B).
    2. Google Gemini 2.5 Flash (`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`).
    3. Groq API (`https://api.groq.com/openai/v1/chat/completions`, Qwen 3.6 / GPT-OSS 120B).
    4. Local Xianxia Terminology Fallback (dictionary matching).
  - 10-chapter terminology graph injection (`glossary_memory.json` / `glossary.json`).
  - Resilient JSON array parsing with 1-based sequential ID validation.

### Milestone 3: Consolidated Server & Real-Time SSE Pipeline (R3)
- **`backend/server.py`**:
  - Merge routes from `main.py`.
  - Real-time Server-Sent Events endpoint: `GET /api/pipeline/stream/{task_id}` emitting sub-step telemetry.
  - Transparent error diagnostics without fake completion logs.
  - Healthcheck endpoint: `GET /api/health`.

### Milestone 4: Production ZIP Packaging & Releases (R4)
- **Release Packaging**:
  - Verify and generate `{title}_Chapter_{num}_Russian.zip` containing all `v3_translated` pages.
  - Expose `GET /api/studio/download/{manga}/{chapter}/v3` and static paths.

### Milestone 5: Strict Anti-Patch Inpainting & Elliptical Typesetting (R5)
- **`cleaner_agent.py`**:
  - Adaptive per-pixel glyph inpainting using `cv2.inpaint(..., flags=cv2.INPAINT_TELEA)`.
  - Zero `cv2.rectangle` calls; background SSIM $\ge 99.5\%$.
- **`translator_typesetter_agent.py`**:
  - Mathematical chord formula: $W(y) = 2a\sqrt{1-(y/b)^2}$.
  - Binary search font scaling ($12\text{px} \to 38\text{px}$) within 85% oval boundaries.
  - Dynamic auto-contrast and cross-platform TTF font loading fallbacks.

### Milestone 6: Next.js Studio Dashboard & Reader Overhaul (R6)
- **`src/app/studio/page.tsx`**:
  - Drag-and-drop zone for ZIPs and folders (`webkitdirectory`).
  - Title and Chapter Range batch launcher (`start_chapter` to `end_chapter`).
  - Live SSE progress visualizer hook (`useSSE`).
  - Chapter Library interactive table with instant read and download actions.
- **`src/app/reader/[manga]/page.tsx`**:
  - Fix refresh race condition: preserve URL `?chapter=chapter_XXX` and `localStorage` on page refresh without resetting to 531.
  - Prominent «Скачать главу (ZIP)» button in header.
  - Burger navigation drawer (catalog link, chapter selector, view modes, hotkeys).
  - Multi-layer switch (1 RAW / 2 Clean / 3 RUS).
  - Remove defunct auto-translate button.
- **`src/app/api/studio/mangas/route.ts`**:
  - Correct parsing of `chapters_index.json` (`data.mangas`).

### Milestone 7: Test Suite Remediation, Full E2E Verification & Git Deployment
- Fix `backend/tests/verify_pipeline.py` import.
- Wrap `test_typesetter_layout.py` in `unittest.TestCase`.
- Run all automated test suites:
  - `python backend/tests/anti_patch_guard.py --all` (13/13 chapters pass, SSIM >= 99.5%).
  - `python backend/tests/bubble_benchmark_100.py` (100/100 pass).
  - `python -m unittest discover -s backend/tests` (18/18 pass).
  - `cd frontend && npx tsc --noEmit` (0 errors).
  - `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532` test run.
- Auto-commit and git push to GitHub repository main branch.
