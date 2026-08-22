## 2026-08-22T19:17:54Z
You are Worker 1 for the Manga & Manhua AI Translation and Inpainting Pipeline v4.0 project.
Working directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_1
Project root: c:\Users\asana\OneDrive\Desktop\Manga
User requirements: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Task:
1. Read ORIGINAL_REQUEST.md and AGENTS.md carefully.
2. Execute and verify all 9 Acceptance Criteria:
   - AC 1: Run python backend/tests/bubble_benchmark_100.py (Must pass 100/100 tests with 0 errors).
   - AC 2: Run python backend/tests/anti_patch_guard.py --all (Must pass all chapters with 0 solid rectangular patches and SSIM degradation <= 0.3%).
   - AC 3: Run python -m unittest discover -s backend/tests (Must pass 13/13 unit tests).
   - AC 4: Run cd frontend && npx tsc --noEmit (Must pass with 0 TypeScript compilation errors). Also check 
pm run build.
   - AC 5: Verify zero English words remaining in speech bubbles of translated chapters (v3).
   - AC 6: Verify zero text stamps or patches placed over background SFX / combat art.
   - AC 7: Verify proper Xianxia terminology consistently used in glossary_memory.json and translation prompts.
   - AC 8: Verify live publication and reader functional on https://manga-ai-translator-three.vercel.app.
   - AC 9: Verify git status. If there are any uncommitted changes, commit and push them to the git repository per AGENTS.md user rules.
3. If any issues, bugs, or missing files are found during test runs, fix them cleanly adhering to project guidelines.
4. Record all test outputs, verification logs, and commands executed in c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_1\worker_report.md and write a structured handoff.md.
5. Send a completion message back to orchestrator.
