# E2E Test Infra: Manga AI Translator Studio

## Test Philosophy
- Opaque-box and automated requirement-driven validation.
- Methodology: Strict Anti-Patch Guard (SSIM >= 99.5%, zero solid rectangles) + 100-Bubble Archetype Benchmark + 18 Unit Tests + Frontend TypeScript Clean Compilation + CLI & Reader E2E Execution.

## Feature Inventory & Test Mapping
| # | Feature | Requirement | Verification Method | Pass Criteria |
|---|---------|-------------|---------------------|---------------|
| 1 | Turnkey Launch Scripts | R1 | Script inspection & healthcheck curl | `start_service.bat` & `start_service.sh` launch backend + frontend, healthcheck returns 200 |
| 2 | Unified CLI Tool | R1 | `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532 --auto-deploy` | Exit code 0, releases generated in `v3_translated/` & ZIP |
| 3 | LLM Cascade & Failover | R2 | `test_glossary_and_topology.py` + provider cascade tests | OpenRouter -> Gemini -> Groq -> Xianxia fallback, 0 leaks |
| 4 | Terminology Graph | R2 | `test_glossary_and_topology.py` | 100% canonical entities translated consistently |
| 5 | Real-Time SSE Stream | R3 | `backend/server.py` `/api/pipeline/stream/{task_id}` test | Emits structured SSE data events with sub-step logs |
| 6 | Production ZIP Releases | R4 | Inspection of 13 chapter ZIPs & download endpoint | `{title}_Chapter_{num}_Russian.zip` download verified |
| 7 | Anti-Patch Inpainting | R5 | `python backend/tests/anti_patch_guard.py --all` | 13/13 chapters pass, 0 violations, background SSIM >= 99.5% |
| 8 | 100-Bubble Benchmark | R5 | `python backend/tests/bubble_benchmark_100.py` | 100/100 archetypes pass across 7 categories |
| 9 | Typesetting & Typography | R5 | `test_typesetter_layout.py` | Russian text within $r \le 88\%$ oval radius, auto-contrast active |
| 10 | Reader Navigation & Persistence | R6 | Next.js Reader navigation test | Refresh with `?chapter=chapter_538` stays on 538, burger drawer, ZIP button |
| 11 | Studio Batch Launcher | R6 | Next.js Studio batch test | Batch range launcher, real SSE progress visualizer, chapter library grid |
| 12 | TypeScript Compilation | R6 | `cd frontend && npx tsc --noEmit` | 0 TypeScript errors |
| 13 | Unit Test Discovery | All | `python -m unittest discover -s backend/tests` | 18/18 discoverable unit tests passing |

## Acceptance Test Suite Thresholds
- **Tier 1 (Anti-Patch Guard)**: 13/13 chapters with 0 violations and background SSIM $\ge 99.5\%$.
- **Tier 2 (Bubble Benchmark)**: 100/100 bubble archetypes passing with 0 art corruption on combat SFX.
- **Tier 3 (Unit Tests)**: 18/18 unit tests passing in `backend/tests/`.
- **Tier 4 (TypeScript)**: 0 TypeScript compilation errors in `frontend/`.
- **Tier 5 (CLI & E2E Run)**: `python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532` executes and creates valid release packages.
