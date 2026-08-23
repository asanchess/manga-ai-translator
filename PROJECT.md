# Project: Manga AI Translator Studio

## Architecture
«Manga AI Translator Studio» is an autonomous, turnkey manga translation product consisting of:
- **Backend (FastAPI + Python ML)**:
  - `backend/server.py`: Consolidated FastAPI application providing REST, SSE telemetry streaming (`/api/pipeline/stream/{task_id}`), and release download endpoints.
  - `backend/cli.py`: Turnkey CLI tool for batch and headless multi-chapter translation runs.
  - `backend/agents/manga_pipeline_service.py`: Central pipeline service orchestrating 5-stage processing (OCR -> Telea Inpaint -> LLM -> Typeset -> Manifest/ZIP).
  - `backend/agents/model_inference_manager.py`: Thread-safe singleton inference manager caching OCR, Inpainting, and classifier models.
  - `backend/agents/cleaner_agent.py`: Adaptive per-pixel glyph inpainter using `cv2.inpaint` (Telea) and 0 `cv2.rectangle` calls (Anti-Patch strictly enforced).
  - `backend/agents/translator_typesetter_agent.py`: Mathematical elliptical typography engine implementing chord equation $W(y)=2a\sqrt{1-(y/b)^2}$ and auto-contrast.
  - `backend/agents/llm_translator.py`: Multi-provider failover cascade (OpenRouter -> Gemini 2.5 Flash -> Groq -> Xianxia fallback) with 10-chapter terminology graph injection.
  - `backend/agents/chapter_integrity_checker.py`: Schema v3.0.0 manifest generator, deficit resolver, release ZIP generator, and frontend mirror synchronizer.
- **Frontend (Next.js 16 + React 19 + Tailwind CSS)**:
  - `src/app/studio/page.tsx`: Studio Dashboard with drag-and-drop upload zone, batch chapter range launcher (e.g. `531-542`), real SSE visualizer hook, and interactive Chapter Library grid with direct read & download buttons.
  - `src/app/reader/[manga]/page.tsx`: Overhauled Manga Reader featuring burger navigation drawer, catalog return, keyboard navigation, Webtoon/Paginated mode switch, 3-layer switch (`v1 RAW` / `v2 Clean` / `v3 RUS`), prominent «Скачать главу (ZIP)» in header, and robust URL query (`?chapter=chapter_XXX`) & localStorage state persistence.
  - `src/app/api/studio/mangas/route.ts`: Fixed manga index endpoint correctly parsing `chapters_index.json`.
- **Infrastructure & Scripts**:
  - `start_service.bat`: One-click Windows launch script orchestrating FastAPI and Next.js with automated healthcheck polling.
  - `start_service.sh`: One-click POSIX launch script with process traps and healthcheck verification.

---

## Feature Inventory
Every feature from the Survey phase is mapped to a designated milestone.

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | `start_service.bat` | Windows turnkey launch script with dual-process orchestration & automated healthcheck polling | M1 | Survey (R1) |
| 2 | `start_service.sh` | Linux/macOS turnkey launch script with trap termination & automated healthcheck polling | M1 | Survey (R1) |
| 3 | `backend/cli.py` | Unified CLI tool supporting `--title`, `--chapters <range>` (`531-532`, `all`, comma lists), `--auto-deploy`, multi-threaded batch inference, ZIP packaging | M1 | Survey (R1) |
| 4 | Secure Credential Loading | Secure `.env` credential loading for Gemini, Groq, OpenRouter, DeepSeek without client leakage | M2 | Survey (R2) |
| 5 | Multi-Provider LLM Cascade | SOTA 4-provider failover cascade (OpenRouter -> Gemini 2.5 Flash -> Groq Qwen 3.6 -> Local Xianxia fallback) in `llm_translator.py` | M2 | Survey (R2) |
| 6 | 10-Chapter Terminology Injection | Injection of canonical glossary (`glossary_memory.json` / `glossary.json`) into LLM prompts with 1-based sequential ID contracts | M2 | Survey (R2) |
| 7 | FastAPI Server Consolidation | Merge `main.py` into unified `backend/server.py`, standardizing routes and mounting static data | M3 | Survey (R3) |
| 8 | Real-Time SSE Telemetry Endpoint | `GET /api/pipeline/stream/{task_id}` emitting live sub-step telemetry (`[Chapter X] [Page Y/Z] -> OCR -> Inpaint -> LLM -> Typeset`) | M3 | Survey (R3) |
| 9 | Honest Diagnostics & Error Handling | Transparent error reporting, retry handling on network blips, removal of fake 100% completion fallbacks | M3 | Survey (R3) |
| 10 | Production ZIP Release Generation | Automatic `{title}_Chapter_{num}_Russian.zip` generation and download routes (`/api/studio/download/...`) | M4 | Survey (R4) |
| 11 | Strict Anti-Patch Inpainting | Zero `cv2.rectangle` solid fills, per-pixel Telea inpainting, background SSIM >= 99.5%, cross-platform font fallbacks | M5 | Survey (R5) |
| 12 | Elliptical Typography Engine | Exact chord equation $W(y) = 2a\sqrt{1-(y/b)^2}$, binary search font sizing ($12\text{px} \to 38\text{px}$), safe oval containment (<=85%), dynamic auto-contrast | M5 | Survey (R5) |
| 13 | Studio Batch Launcher & Library Grid | Studio Dashboard overhaul: Batch range input (`start_chapter` to `end_chapter`), folder/ZIP dropzone, real SSE progress hook, interactive Chapter Library table with instant read/download actions | M6 | Survey (R6) |
| 14 | Reader Navigation & Persistence Overhaul | Manga Reader overhaul: Fix refresh race condition (URL `?chapter=chapter_XXX` + localStorage persistence), burger navigation drawer, prominent «Скачать главу (ZIP)» button in top bar, multi-layer switch (1/2/3) | M6 | Survey (R6) |
| 15 | Frontend API Bug Fixes | Fix JSON parsing in `src/app/api/studio/mangas/route.ts` and correct studio ZIP download links | M6 | Survey (R6) |
| 16 | Test Suite Optimization & Remediation | Fix `verify_pipeline.py` import, wrap `test_typesetter_layout.py` in `unittest.TestCase`, maintain 100/100 bubble benchmark and 18/18 unit tests | M7 | Survey (Tests) |
| 17 | Full Acceptance Verification & Git Deployment | Execute all AC guards (`anti_patch_guard.py --all`, `bubble_benchmark_100.py`, unit tests, TypeScript compile, CLI run on 531-532) and git commit + push to main | M7 | Survey (AC) |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | **CLI & Turnkey Launch Scripts** | Implement `backend/cli.py`, `start_service.bat`, and `start_service.sh` | None | PLANNED |
| 2 | **Multi-Provider LLM Cascade & Glossary** | Implement OpenRouter & DeepSeek in `llm_translator.py`, wire 4-tier cascade, reinforce 10-chapter terminology graph injection | None | PLANNED |
| 3 | **FastAPI Consolidation & Real-Time SSE Stream** | Consolidate `backend/server.py`, implement `GET /api/pipeline/stream/{task_id}` for live SSE telemetry, honest error diagnostics | M2 | PLANNED |
| 4 | **Production ZIP Packaging & Release Endpoints** | Verify `{title}_Chapter_{num}_Russian.zip` packaging and standard download routes | M1, M3 | PLANNED |
| 5 | **SOTA Anti-Patch Inpainting & Elliptical Typesetting** | Ensure zero `cv2.rectangle`, cross-platform font loading, verify SSIM >= 99.5% and elliptical math $W(y)$ | None | PLANNED |
| 6 | **Next.js Studio Dashboard & Reader Overhaul** | Overhaul `studio/page.tsx` (batch launcher, chapter library, SSE visualizer), overhaul `reader/[manga]/page.tsx` (refresh URL/localStorage persistence, burger drawer, top bar ZIP button), fix `api/studio/mangas/route.ts` | M3, M4 | PLANNED |
| 7 | **Final Verification, Test Track & Git Push** | Fix `verify_pipeline.py`, run all AC tests (Anti-Patch 13 chs, Bubble 100, unit tests, TypeScript compile, CLI execution 531-532), git commit & push to GitHub | M1, M2, M3, M4, M5, M6 | PLANNED |

---

## Interface Contracts

### CLI Contract (`backend/cli.py`)
- Invocation: `python backend/cli.py --title <str> --chapters <range_or_list_or_all> [--auto-deploy] [--workers <int>]`
- Example: `python backend/cli.py --title "The_Ultimate_of_All_Ages" --chapters 531-532 --auto-deploy`
- Exit Code: `0` on success, `1` on error.

### Healthcheck Contract (`backend/server.py`)
- Endpoint: `GET /api/health`
- Response: `{"status": "online", "version": "4.0.0", "storage": "backend/data/manga", "public_storage": "frontend/public/manga"}`
- Status code: `200 OK`

### SSE Telemetry Contract (`backend/server.py`)
- Endpoint: `GET /api/pipeline/stream/{task_id}`
- Content-Type: `text/event-stream`
- Event payload: `data: {"task_id": "...", "manga": "...", "chapter": "...", "page": 4, "total_pages": 15, "stage": "Telea Inpaint", "progress": 35, "status": "processing", "log": "[Chapter 532] [Page 4/15] -> Telea Inpaint"}\n\n`
- Completion event: `data: {"status": "completed", "progress": 100, "zip_url": "...", "read_url": "..."}\n\n`
- Error event: `data: {"status": "error", "error": "...", "log": "..."}\n\n`

### ZIP Download Contract
- Backend URL: `GET /api/studio/download/{manga}/{chapter}/v3` -> streams `{manga}_Chapter_{num}_Russian.zip`
- Frontend Static URL: `/manga/{manga}/chapter_{num}/{manga}_Chapter_{num}_Russian.zip`

### Reader URL & Storage Contract (`frontend/src/app/reader/[manga]/page.tsx`)
- URL Format: `/reader/{manga}?chapter=chapter_{num}`
- Storage Key: `manga_reader_chapter_{manga}`
- On Load: Prioritize URL `?chapter=...`, then `localStorage`, then default to first available chapter. Never overwrite URL on initial render before data resolves.

---

## Code Layout & Write Boundaries
- `backend/cli.py` -> Owned by M1 Worker
- `start_service.bat` & `start_service.sh` -> Owned by M1 Worker
- `backend/agents/llm_translator.py` -> Owned by M2 Worker
- `backend/server.py` & `backend/main.py` -> Owned by M3 Worker
- `backend/agents/cleaner_agent.py` & `backend/agents/translator_typesetter_agent.py` -> Owned by M5 Worker
- `frontend/src/app/studio/page.tsx` & `frontend/src/app/reader/[manga]/page.tsx` & `frontend/src/app/api/studio/mangas/route.ts` -> Owned by M6 Worker
- `backend/tests/verify_pipeline.py` & `backend/tests/test_typesetter_layout.py` -> Owned by M7 Worker
