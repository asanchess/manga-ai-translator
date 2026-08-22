# Original User Request

## 2026-08-22T12:40:13Z

<USER_REQUEST>
Reconstruct the Manga AI Translator pipeline and Next.js web reader to v3.0 SOTA Enterprise standard: strict v1/v2/v3 layer isolation, programmatic Anti-Patch Guard, persistent title glossary, singleton ML inference manager, chapter integrity auditor, and reader UX overhaul.

Working directory: c:/Users/asana/OneDrive/Desktop/Manga
Integrity mode: development

## Requirements

### R1. Layer Isolation & Programmatic Anti-Patch Guard
- **v1_original (RAW)**: Immutable scan layer. Accessible only to Scraper and Cleaner.
- **v2_cleaned (Cleaned Art)**: Processed by `backend/agents/cleaner_agent.py` using per-pixel text glyph binarization (`cv2.threshold` + 2px dilation) and `cv2.inpaint(img, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)` or LaMa. Strictly prohibit `cv2.rectangle` or solid color fills.
- **v3_translated (Final Typeset)**: Processed by `backend/agents/translator_typesetter_agent.py`. Strictly consumes `v2_cleaned` (physical isolation from `v1_original`). Text is applied via vector `ImageDraw.Draw` or transparent RGBA compositing without opaque sub-box canvas pasting.
- **Anti-Patch Guard (`backend/tests/anti_patch_guard.py`)**: Programmatic quality validator enforcing:
  - Check A: Solid patch detector (zero/low color variance bounding boxes outside text masks).
  - Check B: Background SSIM diff outside speech bubbles between `v3_translated` and `v1_original` must not exceed 0.5% pixel degradation.

### R2. Dialogue Topology, Batch JSON & Persistent Glossary
- **Persistent Glossary (`backend/data/manga/The_Ultimate_of_All_Ages/glossary.json`)**: Terminology dictionary for characters (Gu Feiyang -> Гу Фэйян, Li Yunxiao -> Ли Юньсяо), factions (Beimin Clan -> Клан Бэймин, Sanctuary -> Святилище), and cultivation terms (Yao Beast -> Демонический Зверь, Dantian -> Даньтянь, Qi -> Ци) injected into every LLM request.
- **Topological Sorting & Strict ID Contract**: Sort bubbles top-to-bottom, right-to-left (manga) / left-to-right (manhua) (`y_center * 10000 + x_center`), assign sequential integer IDs, and send whole page dialogue in a single batch JSON request. Typeset strictly where `dialogue.id == bubble.id`.
- **Elliptical Text Fitting**: Calculate maximum line width using horizontal ellipse chord equation (`2 * a * sqrt(1 - (y/b)^2)`), enforce <= 85% safe box, binary search font size (38px to 12px) with 1.15 * font_size line step, Cyrillic fonts (`comicbd.ttf`, `arialbd.ttf`), and auto-contrast (black on light, white with 1.5px black outline on dark).

### R3. High-Speed ML Inference Singleton & Integrity Checker
- **ModelInferenceManager**: Singleton pattern in `backend/agents/` holding EasyOCR / manga-ocr / Inpainting weights in memory once at startup. ThreadPoolExecutor for I/O and ProcessPoolExecutor for non-neural geometry. Full chapter processing target: 60–120s.
- **ChapterIntegrityChecker**: Verify chapters 531 to ongoing. Ensure >= 8 pages per chapter with scraper mirror rotation (MangaKatana, Comick, MangaDex) on deficit. Write `pipeline_manifest.json` (v3.0.0, layer checksums) and generate `.zip` archives.

### R4. Next.js Web Reader Overhaul & UI Persistence
- **Header & Navigation**: "В каталог" (`/`) link, chapter dropdown (531 to ongoing), "Предыдущая" / "Следующая" (hotkeys A/D and ArrowLeft/ArrowRight).
- **Layer Switcher**: 1 RAW / 2 Clean / 3 РУС with active highlights and hotkeys 1, 2, 3.
- **Display Modes & Progress**: Width toggles (700px, 900px, 1200px, 100%), Webtoon scroll vs single-page mode, "Страница X из Y" indicator and scroll progress bar.
- **Dead UI Removal**: Remove "Авто-перевод главы" button from reader; audit and clean stubs in AI Studio.
- **URL & State Persistence**: Read chapter from `?chapter=chapter_XXX`, sync via `window.history.replaceState` and `localStorage.setItem('last_read_chapter', currentChapter)`. Preserves exact chapter on F5 refresh.

### R5. Verification & Sync Reporting
- Automated execution of `backend/tests/anti_patch_guard.py` verifying 0px gray patches and passing background SSIM diff.
- Complete summary report in `production_artifacts/Ongoing_Sync_Report.md`.

## Acceptance Criteria

### Layer Isolation & Anti-Patch Guard
- [ ] `v2_cleaned` contains 0 solid rectangular fills (`cv2.rectangle` absent in cleaning code).
- [ ] `v3_translated` only receives `v2_cleaned` as input.
- [ ] `backend/tests/anti_patch_guard.py` passes with 0 solid patch detections on test chapters (Ch. 531 p. 2 & 8) and SSIM background difference <= 0.5%.

### Glossary & Batch Translation
- [ ] `glossary.json` exists and is injected into prompts for all LLM translation passes.
- [ ] OCR bubbles are sorted by `y_center * 10000 + x_center` with sequential 1-based IDs and translated in batch JSON.
- [ ] Typesetting fits <= 85% safe oval bounds with auto-contrast.

### Performance & Integrity
- [ ] `ModelInferenceManager` initializes weights once (singleton).
- [ ] All processed chapters have >= 8 pages, `pipeline_manifest.json`, and corresponding `.zip` translation archives.
- [ ] Reader URL stays persistent on F5 (`?chapter=chapter_XXX`).
- [ ] Layer hotkeys 1, 2, 3 and chapter navigation A/D, ArrowLeft/ArrowRight work seamlessly.
- [ ] "Авто-перевод главы" button removed from reader view.
- [ ] `Ongoing_Sync_Report.md` is populated with chapter status table.
</USER_REQUEST>

## 2026-08-22T19:11:37Z

<USER_REQUEST>
Build and execute an autonomous, scanlation-grade Manga & Manhua AI Translation and Inpainting Pipeline v4.0 that separates speech bubbles from sound effects (SFX), eliminates all English leaks, mines 10-chapter terminology graphs, and generates publication-ready Russian releases on Vercel.

Working directory: c:/Users/asana/OneDrive/Desktop/Manga
Integrity mode: development

## Requirements

### R1. Bubble & SFX Classification with Zero Background Art Corruption
- Distinguish dialogue speech bubbles (SPEECH_BUBBLE) from sound effects / combat art (SFX_ART).
- Generate per-pixel glyph masks inside detected bubble contours without rectangular fills or border erasure.
- Sound effects (SFX) and background action strokes must remain 100% untouched (never stamped with OCR artifacts like "G2", "hx KY", "0g09").

### R2. 100-Bubble Comprehensive Benchmark Verification
- Enforce automated testing against 100 diverse bubble archetypes (light oval, dark inverted, spiky scream, borderless floating, system windows, SFX onomatopoeia, thought clouds).
- Passing threshold: 100/100 correct detections, 0 false positive SFX text stamps, background SSIM preservation >= 99.8%.

### R3. 10-Chapter Scanlation Memory Mining
- Mine preceding 10 chapters to build and maintain persistent knowledge graph glossary_memory.json (character names, cultivation realms, sects, artifacts, speech tone).
- Inject mined terminology and translation rules into every downstream LLM prompt.

### R4. SOTA Contextual Translation & Anti-Leak Shield
- Localize dialogues into natural literary Russian matching Xianxia genre conventions using live SOTA LLMs (Google Gemini 2.5 Flash / Groq Qwen 3.6 / No-Auth Free Routers).
- Reject and re-prompt any output containing raw English dialogue leaks or machine translation artifacts.

### R5. Vector Typography, Typesetting & Online Delivery
- Apply elliptical chord word wrapping W(y) = 2a*sqrt(1-(y/b)^2) with Cyrillic TTF fonts (comicbd.ttf, arialbd.ttf, segoeuib.ttf) centered with dynamic contrast.
- Maintain physical 3-layer architecture (v1_original, v2_cleaned, v3_translated), generate v3.0.0 manifests, and deploy live to Vercel reader.

## Acceptance Criteria

### Automated Benchmark & Safety Guards
- [ ] python backend/tests/bubble_benchmark_100.py passes 100/100 tests with 0 errors.
- [ ] python backend/tests/anti_patch_guard.py --all passes all chapters (0 solid rectangular patches, SSIM degradation <= 0.3%).
- [ ] python -m unittest discover -s backend/tests passes 13/13 unit tests.
- [ ] cd frontend && npx tsc --noEmit passes with 0 TypeScript compilation errors.

### Visual Quality & Translation Fidelity
- [ ] Zero English words remaining in speech bubbles of translated chapters (v3).
- [ ] Zero text stamps or patches placed over background SFX / combat art.
- [ ] Proper Xianxia terminology consistently used (Ли Юньсяо, Гу Фэйян, Даньтянь, Ци, Святилище).
- [ ] Live publication and reader functional on https://manga-ai-translator-three.vercel.app.

</USER_REQUEST>
