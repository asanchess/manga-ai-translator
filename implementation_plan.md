# Implementation Plan — «Manga AI Translator Studio»

## Proposed Implementation Plan

### Architecture & Strategy
Based on the survey of the backend, frontend, test suites, and infrastructure, the implementation will be executed systematically across 7 focused milestones:

- **M1. CLI & Turnkey Startup Scripts (R1)**:
  - Create `backend/cli.py` with multi-chapter range arguments, auto-deploy, and thread pool integration.
  - Create `start_service.bat` (Windows) and `start_service.sh` (Linux/macOS) with automated healthcheck loops.
- **M2. Multi-Provider LLM Cascade & 10-Chapter Terminology Graph (R2)**:
  - Add OpenRouter and DeepSeek provider adapters in `backend/agents/llm_translator.py`.
  - Establish resilient 4-tier cascade: OpenRouter -> Gemini 2.5 Flash -> Groq -> Local Xianxia fallback.
  - Inject 10-chapter terminology graph (`glossary_memory.json` / `glossary.json`).
- **M3. Consolidated FastAPI Server & Real-Time SSE Stream (R3)**:
  - Consolidate `backend/server.py` to unify all reader, studio, and health routes.
  - Implement real-time SSE stream endpoint `GET /api/pipeline/stream/{task_id}` emitting sub-step telemetry.
  - Remove fake completion logs; establish transparent error handling.
- **M4. Production ZIP Packaging & Releases (R4)**:
  - Verify standard release packaging `{title}_Chapter_{num}_Russian.zip` and download endpoints.
- **M5. SOTA Anti-Patch Inpainting & Elliptical Typesetting (R5)**:
  - Verify zero `cv2.rectangle` usage in inpainter; ensure background SSIM >= 99.5%.
  - Verify elliptical chord typography $W(y)=2a\sqrt{1-(y/b)^2}$ and cross-platform font fallbacks.
- **M6. Next.js Studio Dashboard & Web Reader Overhaul (R6)**:
  - Overhaul `frontend/src/app/studio/page.tsx`: batch range launcher (`start_chapter` to `end_chapter`), folder/ZIP drag & drop, real SSE visualizer, and chapter library table.
  - Overhaul `frontend/src/app/reader/[manga]/page.tsx`: fix refresh race condition (URL `?chapter=chapter_XXX` & localStorage persistence without reset to 531), burger navigation drawer, prominent top-bar «Скачать главу (ZIP)» button.
  - Fix `frontend/src/app/api/studio/mangas/route.ts` JSON parsing and broken ZIP download links.
- **M7. Test Suite Remediation, Full E2E Verification & Git Push**:
  - Fix `backend/tests/verify_pipeline.py` import and wrap `test_typesetter_layout.py`.
  - Run all quality guards and tests:
    - `anti_patch_guard.py --all` (13/13 chapters pass, SSIM >= 99.5%)
    - `bubble_benchmark_100.py` (100/100 pass)
    - `python -m unittest discover -s backend/tests` (18/18 pass)
    - `cd frontend && npx tsc --noEmit` (0 errors)
    - `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532` test execution
  - Commit all changes and push to GitHub repository main branch.

---

### User Review Required

> [!NOTE]
> Autonomous Execution Policy from `AGENTS.md` gives 100% full autonomy to execute commands, build, test, and push to Git. The team will now proceed with milestone execution.
