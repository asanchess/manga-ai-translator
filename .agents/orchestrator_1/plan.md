# Orchestrator Plan — Manga AI Translator Studio

## Phase 0: Survey & Architecture Audit
1. Spawn 3 specialized Explorers/Spec Miners in parallel:
   - `teamwork_preview_explorer_backend`: Audit FastAPI backend, pipeline services (`backend/agents/manga_pipeline_service.py`), inpainting logic, LLM cascade, terminology graph, and existing endpoints.
   - `teamwork_preview_explorer_frontend`: Audit Next.js frontend (`frontend/`), reader components, dashboard, SSE integration, state persistence, multi-layer toggle, and ZIP download buttons.
   - `teamwork_preview_explorer_infra`: Audit test suites (`backend/tests/`), CLI (`backend/cli.py`), startup scripts (`start_service.bat`, `start_service.sh`), and current benchmark statuses.
2. Synthesize findings into `PROJECT.md` (Feature Inventory, Architecture, Milestones, Interface Contracts, Code Layout).
3. Spawn E2E Testing Orchestrator to establish `TEST_INFRA.md` and test fixtures.

## Phase 1: Milestones Implementation & Verification Track
- **M1: CLI & Turnkey Scripts (R1)**:
  - `start_service.bat` & `start_service.sh` with healthchecks.
  - `python backend/cli.py --title <title> --chapters <range> [--auto-deploy]`.
- **M2: Multi-Provider LLM Cascade & Failover (R2)**:
  - Multi-provider cascade (OpenRouter / Gemini 2.5 Flash / Groq Qwen / Xianxia fallback) reading `.env`.
  - 10-chapter terminology graph injection (`glossary_memory.json` / `glossary.json`).
- **M3: Real-Time SSE Pipeline & Transparent Diagnostics (R3)**:
  - SSE/WebSocket telemetry per stage and page.
  - Honest error logs, retry handling.
- **M4: Production ZIP Packaging & Instant Downloads (R4)**:
  - Auto-generate `{title}_Chapter_{num}_Russian.zip`.
  - Download endpoints and UI triggers.
- **M5: SOTA Glyph Inpainting & Elliptical Typesetting (R5)**:
  - Zero rectangular fills; per-pixel glyph inpainting (Telea/LaMa), background SSIM >= 99.5%.
  - Typeset on `v2_cleaned` with Russian TTF fonts, elliptical chord formula $W(y) = 2a\sqrt{1-(y/b)^2}$, auto-contrast.
- **M6: Overhauled Next.js Web Reader & Studio Dashboard (R6)**:
  - Drag-and-drop upload zone, chapter range launcher, SSE visualizer, library view.
  - Reader: burger menu, catalog return, keyboard navigation, multi-layer switch (1/2/3), ZIP download, URL query + localStorage persistence, removal of defunct buttons.

## Phase 2: Final Verification, Acceptance Testing & Git Push
- Run `anti_patch_guard.py --all` across all 13 chapters (SSIM >= 99.5%, 0 violations).
- Run `bubble_benchmark_100.py` (100/100 archetypes).
- Run `python -m unittest discover -s backend/tests` (18/18 tests pass).
- Run `cd frontend && npx tsc --noEmit` (0 errors).
- Execute CLI test run on "The_Ultimate_of_All_Ages" chapters 531-532.
- Verify start scripts and reader persistence.
- Auto-commit and push all changes to GitHub.
- Deliver comprehensive handoff to Sentinel.
