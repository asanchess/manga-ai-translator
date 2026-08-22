# Manga AI Translator v3.0 SOTA Enterprise Reconstruction

## Architecture Overview
The Manga AI Translator is structured as a decoupled, multi-tier system:
1. **Backend**: FastAPI + OpenCV + EasyOCR / manga-ocr + Telea Inpainting + Ollama/OpenRouter LLM + Pillow vector typesetter.
2. **Data Layer**: Strict 3-layer filesystem storage under `backend/data/manga/{title}/{chapter}/` with `v1_original`, `v2_cleaned`, `v3_translated`, accompanied by `pipeline_manifest.json` and chapter `.zip` archives.
3. **Frontend**: Next.js 14 / React Web Reader with multi-layer switching (1/2/3), keyboard navigation, dual reading modes (Webtoon / Single Page), width presets, and URL + LocalStorage persistence.
4. **Quality & Integrity**: Anti-Patch Guard programmatic test harness with solid patch color variance detection and SSIM $\le 0.5\%$ degradation boundary checks.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1: Layer Isolation & Storage Standardization | Strict v1/v2/v3 folder isolation, v3 strictly consumes v2, cleanup stray dirs, index synchronization | M1 | ORIGINAL_REQUEST §R1 |
| 2 | F2: Programmatic Anti-Patch Guard | Solid patch detector ($\sigma^2 < 1.0$), SSIM background degradation $\le 0.5\%$, automated test suite | M1 | ORIGINAL_REQUEST §R1 |
| 3 | F3: Persistent Glossary & LLM Injection | `glossary.json` with Xianxia terms, automatic prompt injection for all translations | M2 | ORIGINAL_REQUEST §R2 |
| 4 | F4: Dialogue Topology & Sequential ID Contract | Bubble sorting $y_{\text{center}} \times 10000 + x_{\text{center}}$, 1-based sequential IDs, batch JSON LLM translation | M2 | ORIGINAL_REQUEST §R2 |
| 5 | F5: Elliptical Typesetting & Typography | Mathematical chord wrapping $2a\sqrt{1-(y/b)^2}$, $\le 85\%$ safe oval bounds, binary search font scale ($38\to 12\text{px}$), Cyrillic TTF, auto-contrast | M2 | ORIGINAL_REQUEST §R2 |
| 6 | F6: High-Speed ML Inference Singleton | `ModelInferenceManager` holding EasyOCR/manga-ocr/Inpainting models once, ThreadPool/ProcessPool dual executor | M3 | ORIGINAL_REQUEST §R3 |
| 7 | F7: Chapter Integrity Checker & Mirror Rotation | Verify Ch. 531–ongoing ($\ge 8$ pages), scraper mirror rotation for Ch. 537 & 538 deficits, manifests, `.zip` generation | M3 | ORIGINAL_REQUEST §R3 |
| 8 | F8: Next.js Web Reader UX Overhaul | Header/navigation, layer hotkeys 1/2/3, width toggles, single/scroll modes, dead UI removal, URL & localStorage persistence | M4 | ORIGINAL_REQUEST §R4 |
| 9 | F9: E2E Verification & Sync Reporting | Automated anti-patch guard verification, `Ongoing_Sync_Report.md`, QA Report, README update, git hygiene | M5 | ORIGINAL_REQUEST §R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Layer Isolation & Anti-Patch Guard | Physical v1/v2/v3 separation, `anti_patch_guard.py` test harness, stray directories cleanup | None | IN_PROGRESS |
| M2 | Dialogue Topology, Batch JSON & Persistent Glossary | `glossary.json`, LLM prompt injection, $y\times 10000+x$ sorting, 1-based IDs, elliptical chord wrapping, auto-contrast | M1 | PLANNED |
| M3 | ML Inference Singleton & Chapter Integrity Checker | `ModelInferenceManager` singleton, `ChapterIntegrityChecker`, deficit resolution for Ch. 537/538, chapter processing (531–542), manifests & zips | M1, M2 | PLANNED |
| M4 | Next.js Web Reader Overhaul & UI Persistence | Reader page overhaul, layer switcher, width presets, single-page/webtoon modes, hotkeys, dead UI removal, URL sync | M1 | PLANNED |
| M5 | E2E Verification & Sync Reporting | Full test pass, Anti-Patch Guard execution on all chapters, `Ongoing_Sync_Report.md`, `QA_Report.md`, Git commit & push | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Cleaner ↔ Typesetter Layer Contract
- `v1_original`: Source RAW image (e.g. `page_001.png` / `page_001.webp`). Read-only for cleaner.
- `v2_cleaned`: Cleaned image output from `cleaner_agent.py`. Pure background art with glyphs inpainted via Telea/LaMa. 0 occurrences of `cv2.rectangle` or solid fills.
- `v3_translated`: Final image output from `translator_typesetter_agent.py`. Strictly takes `v2_cleaned` as background and draws vector text overlays. Never reads `v1_original`.

### Anti-Patch Guard Contract
- Function `audit_page_quality(v1_path, v2_path, v3_path, bubble_masks)`:
  - Check A: Scans non-text bounding boxes for solid uniform patches ($\text{variance} < 1.0$). Rejects solid fills.
  - Check B: Calculates structural similarity index ($\text{SSIM}$) on non-bubble background between `v1_original` and `v3_translated`. Asserts $\text{SSIM} \ge 0.995$ (degradation $\le 0.50\%$).

### LLM Translation & Dialogue JSON Contract
- Input Prompt: Injects terms from `glossary.json` into system prompt.
- Request payload:
  ```json
  [
    {"id": 1, "text": "Who are you?", "type": "speech"},
    {"id": 2, "text": "I am Li Yunxiao!", "type": "speech"}
  ]
  ```
- Output payload:
  ```json
  [
    {"id": 1, "translation": "Кто ты такой?"},
    {"id": 2, "translation": "Я — Ли Юньсяо!"}
  ]
  ```
- Typesetting mapping: Strictly pairs `translation` to bubble where `dialogue.id == bubble.id`.

### Code Layout
- `backend/agents/`:
  - `cleaner_agent.py` — Inpainting and glyph removal (Telea / LaMa, no cv2.rectangle).
  - `translator_typesetter_agent.py` — Elliptical typesetting, auto-contrast, font scaling.
  - `ocr_engine.py` — 2-pass OCR, topological bubble sorting.
  - `llm_translator.py` — Batch JSON translation with glossary injection.
  - `model_inference_manager.py` — High-speed ML inference singleton.
  - `chapter_integrity_checker.py` — Scraper mirror rotation, chapter parity audit, manifest and zip builder.
  - `manga_pipeline_service.py` — Unified orchestration pipeline for manga translation.
- `backend/tests/`:
  - `anti_patch_guard.py` — Programmatic Anti-Patch Guard test harness.
  - `test_typesetter_layout.py` — Elliptical layout and bounding box unit tests.
- `backend/data/manga/The_Ultimate_of_All_Ages/`:
  - `glossary.json` — Persistent Xianxia terminology dictionary.
  - `chapter_XXX/`: `v1_original/`, `v2_cleaned/`, `v3_translated/`, `pipeline_manifest.json`.
- `frontend/src/app/reader/[manga]/page.tsx` — Next.js Reader view with layer switching, dual modes, hotkeys, width controls, and persistence.
- `production_artifacts/`:
  - `Spec.md` — Architectural specification.
  - `Ongoing_Sync_Report.md` — Chapter sync and QA report.
  - `QA_Report.md` — Verification test logs.
