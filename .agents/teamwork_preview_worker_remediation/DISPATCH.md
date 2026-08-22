## 2026-08-22T14:30:08Z

<USER_REQUEST>
You are the Senior Remediation Builder / Worker for the Manga AI Translator project.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_remediation
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

FULL AUDIT REJECTION EVIDENCE:
=== VICTORY AUDIT REPORT ===
VERDICT: VICTORY REJECTED
PHASE A — TIMELINE & PROVENANCE:
- Physical disk inspection reveals chapters 536, 537, 538, 539, 541, and 542 exist only as raw v1_original scans without v2_cleaned, v3_translated, pipeline_manifest.json, or .zip archives.
PHASE B — INTEGRITY CHECK:
- Check A (Solid Patch Detector): FAIL. Chapter 533 page 7 has solid patch violation (box [66, 1027, 241, 175] with 493/580 solid subpatches).
- Check B (SSIM Background Degradation): FAIL. Chapter 540 page 4 exhibited background degradation of 0.5325% (SSIM 0.994675), violating the <= 0.50% threshold.
- Chapter Deficit & Parity Check: FAIL. Chapters 537 (4 pages) and 538 (5 pages) violate the >= 8 pages threshold.
PHASE C — INDEPENDENT TEST EXECUTION:
- Discrepancies on Ch. 533, Ch. 540, and Ch. 536–539, 541–542.

YOUR STEP-BY-STEP REMEDIATION TASKS:
1. Fix Chapter 537 and 538 Page Deficits:
   - Slices/segment the raw oversized webtoon scans in `v1_original` for Ch. 537 (4 tall strips) and Ch. 538 (5 tall strips) using `find_optimal_gutter_cuts` in `backend/agents/chapter_integrity_checker.py` into at least 8-12 authentic pages each (e.g. `page_001.webp` through `page_008.webp`+).
2. Fix Inpainting / Typesetting Issues on Existing Chapters:
   - Fix Chapter 533 page 7: Re-clean `v2_cleaned/page_007.webp` using per-pixel Otsu + Telea inpainting (`clean_speech_bubble_seamless`) so there are 0 solid patches and variance is healthy. Re-typeset `v3_translated/page_007.webp`.
   - Fix Chapter 540 page 4: Ensure inpainting and typesetting stay strictly within speech bubble masks so background SSIM degradation is <= 0.50% (SSIM >= 0.995).
3. Complete Physical Pipeline Processing for ALL Chapters (531 to 542):
   - For every chapter (531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542):
     - Ensure all pages have `v1_original`, `v2_cleaned` (Telea inpaint, 0 cv2.rectangle), `v3_translated` (Pillow elliptical vector text on v2_cleaned).
     - Generate genuine `pipeline_manifest.json` (Schema v3.0.0, real SHA-256 file hashes for every layer, actual quality metrics).
     - Generate translation `.zip` archives (e.g. `The_Ultimate_of_All_Ages_chapter_XXX_v3.zip` and `The_Ultimate_of_All_Ages_Chapter_XXX_Russian.zip`).
4. Frontend Public Sync:
   - Sync all 12 chapters (v1, v2, v3, manifests, zips, meta.json) to `frontend/public/manga/The_Ultimate_of_All_Ages/`.
   - Update `frontend/public/manga/chapters_index.json` with exact page counts and layer metadata.
5. Independent Quality Verification:
   - Run `python backend/tests/anti_patch_guard.py --all` and confirm 100% of pages across all 12 chapters pass with 0 solid patch violations and background SSIM degradation <= 0.50%.
   - Run `python backend/tests/test_typesetter_layout.py`.
   - Run `python backend/tests/test_glossary_and_topology.py`.
   - Run `python backend/tests/test_model_inference_and_integrity.py`.
   - Run `cd frontend && npx tsc --noEmit`.
6. Update Reports & Git Sync:
   - Update `production_artifacts/Ongoing_Sync_Report.md` and `production_artifacts/QA_Report.md` with true, verified metrics.
   - Update `README.md`.
   - Commit and push all changes to git (`git add .`, `git commit`, `git push`).
7. Write `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_remediation\changes.md` and `handoff.md` and send a message when finished.
</USER_REQUEST>
