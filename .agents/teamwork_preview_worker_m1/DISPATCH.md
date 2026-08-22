## 2026-08-22T12:45:42Z

You are the Builder / Worker for Milestone M1: Layer Isolation & Programmatic Anti-Patch Guard.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m1
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
Project Spec: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_orchestrator_1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Tasks for M1:
1. Read `ORIGINAL_REQUEST.md`, `AGENTS.md`, and `PROJECT.md`.
2. Implement `backend/tests/anti_patch_guard.py`:
   - Programmatic quality validator implementing:
     - Check A (Solid Patch Detector): Detect solid / uniform color fills (e.g. low variance $\sigma^2 < 1.0$) in bounding boxes outside text glyphs.
     - Check B (Background SSIM Difference): Calculate structural similarity index (SSIM) on non-bubble background between `v3_translated` and `v1_original`. Verify degradation $\le 0.5\%$ (SSIM $\ge 0.995$).
     - CLI execution mode: `python backend/tests/anti_patch_guard.py --manga The_Ultimate_of_All_Ages --chapter chapter_531 --pages 2 8` and `--all`.
     - Output JSON report with metrics per page.
3. Clean up stray directories in `frontend/public/manga/` (such as `v2/`, `v2_cleaned/`, `v3/`, `v3_translated/` at the manga root) to prevent phantom manga entries in `chapters_index.json`.
4. Verify layer isolation in `backend/agents/cleaner_agent.py` and `backend/agents/manga_pipeline_service.py` (ensure 0 occurrences of `cv2.rectangle`, ensure `v3_translated` strictly takes `v2_cleaned` as input).
5. Run tests:
   - `python backend/tests/anti_patch_guard.py --chapter chapter_531 --pages 2 8`
   - `python backend/tests/test_typesetter_layout.py`
6. Write a comprehensive report in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m1\changes.md` and `handoff.md`.
7. Send a completion message to the parent orchestrator with your results and test outputs.
