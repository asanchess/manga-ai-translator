## 2026-08-22T12:57:07Z
You are the Builder / Worker for Milestone M3: High-Speed ML Inference Singleton & Chapter Integrity Checker.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m3
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
Project Spec: c:\Users\agents\teamwork_preview_orchestrator_1\PROJECT.md

Scope & Tasks for M3:
1. Implement `backend/agents/model_inference_manager.py`:
   - Singleton pattern holding EasyOCR reader, manga-ocr (if available), and inpainting model/weights loaded once at startup.
   - Dual executor setup: ThreadPoolExecutor for concurrent I/O / downloads / LLM calls and ProcessPoolExecutor (or optimized threading) for geometry and CPU-bound operations.
   - Provide clean inference methods: `get_ocr_reader()`, `get_inpainting_engine()`, `process_chapter_concurrent()`.
   - Target full chapter processing: 60–120s.
2. Implement `backend/agents/chapter_integrity_checker.py`:
   - Chapter parity and integrity auditor verifying all chapters from 531 to ongoing.
   - Ensure every chapter has >= 8 pages in v1_original.
   - Scraper mirror rotation (MangaKatana, Comick, MangaDex, or high-res fallbacks) to resolve page deficits for Ch. 537 (currently 4 pages) and Ch. 538 (currently 5 pages) so they have >= 8 pages.
   - Run pipeline processing on all chapters (531 to 542) ensuring `v1_original`, `v2_cleaned`, and `v3_translated` layers are properly generated and physically isolated.
   - Generate `pipeline_manifest.json` (v3.0.0 schema with layer counts, SHA-256 checksums, and quality metrics) inside each chapter directory.
   - Generate corresponding `.zip` translation archives for each chapter (e.g. `The_Ultimate_of_All_Ages_chapter_XXX_v3.zip`).
   - Sync all processed chapters to `frontend/public/manga/The_Ultimate_of_All_Ages/` and update `chapters_index.json`.
3. Create unit tests in `backend/tests/test_model_inference_and_integrity.py` to verify singleton initialization and chapter integrity verification logic.
4. Run tests:
   - `python backend/tests/test_model_inference_and_integrity.py`
   - `python backend/tests/anti_patch_guard.py --all`
5. Write `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m3\changes.md` and `handoff.md`.
6. Automatically commit and push all changes to Git per AGENTS.md rules.
7. Send a completion message to the parent orchestrator.
