## 2026-08-23T10:43:52Z

You are the Builder / Worker for Milestone 3 & Milestone 4 (Consolidated FastAPI Server, Real-Time SSE Telemetry & ZIP Downloads) of the «Manga AI Translator Studio» project.
Your working directory is: c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m3_m4_1
You MUST read the following authoritative files first before starting:
1. c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
2. c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
3. c:\Users\asana\OneDrive\Desktop\Manga\PROJECT.md
4. c:\Users\asana\OneDrive\Desktop\Manga\.agents\explorer_backend_1\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Write Boundaries:
You own exclusively:
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\server.py`
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\manga_pipeline_service.py`

Tasks:
1. Unify `backend/server.py` to be the single, complete FastAPI application serving all API routes:
   - `GET /api/health` -> returns health status, version 4.0.0, storage paths.
   - `GET /api/chapters/{manga}` -> lists chapters with page counts and layer availability.
   - `GET /api/studio/mangas` -> lists all manga titles and available chapter numbers.
   - `POST /api/studio/translate` -> triggers async chapter translation (single or batch range).
   - `POST /api/studio/upload` -> handles upload of raw ZIPs or multi-image chapter folders.
   - `GET /api/studio/tasks/{id}` / `GET /api/status/{id}` -> REST status polling.
   - `GET /api/studio/download/{manga}/{chapter}/v3` (and `{layer}`) -> serves `{manga}_Chapter_{num}_Russian.zip` or layer ZIPs with proper Content-Disposition and MIME type `application/zip`.
   - Mount static files for `/data/manga` and `frontend/public/manga`.
2. Implement Real-Time Server-Sent Events (SSE) streaming endpoint:
   - `GET /api/pipeline/stream/{task_id}`
   - Emits `text/event-stream` with fine-grained sub-step telemetry:
     `data: {"task_id": "...", "manga": "...", "chapter": "...", "page": 4, "total_pages": 15, "stage": "Telea Inpaint", "progress": 35, "status": "processing", "log": "[Chapter 532] [Page 4/15] -> Telea Inpaint"}\n\n`
   - Final completion event with `zip_url` and `read_url`.
   - Error event with honest error diagnostic message.
3. Enhance `backend/agents/manga_pipeline_service.py`:
   - Add fine-grained progress callback hooks per page and per processing sub-step (2-Pass OCR -> Telea Inpaint -> Batch LLM -> Elliptical Typeset -> Manifest).
   - Provide an async queue / event generator for active tasks so SSE subscribers receive live events immediately.
4. Verify your implementation by running unit tests and checking server route initialization.
5. Document all changes and verification in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m3_m4_1\handoff.md`.
6. Send completion message back to parent orchestrator.

## 2026-08-23T11:00:07Z
**Context**: Orchestration Status Check
**Content**: Checking in on Milestone 3 & Milestone 4 progress. Please let me know your current progress on server.py unification and SSE streaming.
**Action**: Reply with your current progress and ETA.

