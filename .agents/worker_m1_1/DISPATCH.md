## 2026-08-23T10:37:03Z
You are the Builder / Worker for Milestone 1 (CLI & Turnkey Launch Scripts) of the «Manga AI Translator Studio» project.
Your working directory is: c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m1_1
You MUST read the following authoritative files first before starting:
1. c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
2. c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
3. c:\Users\asana\OneDrive\Desktop\Manga\PROJECT.md
4. c:\Users\asana\OneDrive\Desktop\Manga\.agents\explorer_infra_1\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Write Boundaries:
You own exclusively:
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\cli.py`
- `c:\Users\asana\OneDrive\Desktop\Manga\start_service.bat`
- `c:\Users\asana\OneDrive\Desktop\Manga\start_service.sh`

Tasks:
1. Implement `backend/cli.py`:
   - Unified CLI for human and AI agents.
   - Command: `python backend/cli.py --title <title> --chapters <range_or_list_or_all> [--auto-deploy] [--workers <int>] [--force]`
   - Supports: `--title "The_Ultimate_of_All_Ages"` or `--title The_Ultimate_of_All_Ages`.
   - Supports `--chapters`: `531-532`, `531,532`, `531`, `all`.
   - Integrates with `MangaPipelineService` / `ModelInferenceManager` for concurrent batch processing.
   - Generates Schema v3.0.0 `pipeline_manifest.json` and `{title}_Chapter_{num}_Russian.zip` release archives.
   - When `--auto-deploy` is specified (or by default on successful completion), calls `sync_to_frontend()` and updates `frontend/public/manga/chapters_index.json`.
   - Provides clean terminal progress and proper exit codes (0 on success, 1 on error).
2. Implement `start_service.bat`:
   - Windows turnkey startup script.
   - Checks Python 3.10+ and virtualenv (`backend\venv`), installs requirements if missing.
   - Checks Node.js/npm and installs `frontend/node_modules` if missing.
   - Spawns FastAPI backend (`backend\server.py` on port 8000) and Next.js frontend (`npm run dev` on port 3000) in separate minimized or background cmd processes.
   - Performs automated healthcheck polling against `http://localhost:8000/api/health` and `http://localhost:3000` via PowerShell until online (with timeout).
   - Displays clean status banner and launches browser to `http://localhost:3000`.
3. Implement `start_service.sh`:
   - POSIX (Linux/macOS) turnkey startup script.
   - Checks python3, venv, node, npm.
   - Starts backend on 8000 and frontend on 3000 with process trapping (`trap 'kill ...' SIGINT SIGTERM EXIT`).
   - Polls healthcheck endpoints with curl.
4. Test and verify your implementations by running test invocations (e.g. `python backend/cli.py --help`, testing chapter range parsing).
5. Document all commands, code changes, and test outputs in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m1_1\handoff.md`.
6. Send completion message back to parent orchestrator.
