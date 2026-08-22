# Manga & Manhua AI Translation and Inpainting Pipeline v4.0 — Comprehensive Survey Report

**Explorer 3 Assessment Report**  
**Date**: 2026-08-23  
**Focus Areas**: R3 (10-Chapter Scanlation Memory Mining), R4 (Contextual Translation & Anti-Leak Shield), R5 (Frontend Reader Layers, Manifest v3.0.0, Vercel Live Deployment)

---

## 1. Executive Summary

A comprehensive investigation into the Manga AI Translator codebase, translation pipelines, backend memory graphs, test suites, and frontend deployment infrastructure was conducted.

| Requirement / Component | Current Status | Key File / Location | Test Verification |
|---|---|---|---|
| **R3: 10-Chapter Scanlation Memory Mining** | ✅ **100% Complete** | `backend/agents/scanlation_memory_miner.py`, `glossary_memory.json` | `test_glossary_and_topology.py` (5/5 PASS) |
| **R4: Contextual Translation & Anti-Leak Shield** | ✅ **100% Complete** | `backend/agents/llm_translator.py`, `comic_bubble_detector.py` | `bubble_benchmark_100.py` (100/100 PASS) |
| **R5: Multi-Layer Reader (v1/v2/v3) & Manifest v3.0.0** | ✅ **100% Complete** | `frontend/src/app/reader/[manga]/page.tsx`, `pipeline_manifest.json` | `test_model_inference_and_integrity.py` (13/13 PASS) |
| **Frontend Compilation & Next.js Build** | ✅ **100% Complete** | `frontend/src/` | `npx tsc --noEmit` (0 errors), `npm run build` (PASS) |
| **Vercel Production Deployment** | ✅ **Live & Ready** | `https://manga-ai-translator-three.vercel.app` | Vercel MCP `get_project` (State: `READY`) |

---

## 2. In-Depth Analysis of R3: 10-Chapter Scanlation Memory Mining

### 2.1 Implementation Architecture
- **Miner Module**: `backend/agents/scanlation_memory_miner.py` defines the singleton class `ScanlationMemoryMiner`.
- **Knowledge Graph Files**:
  - `backend/data/manga/The_Ultimate_of_All_Ages/glossary_memory.json` (3,005 bytes, 63 lines)
  - `backend/data/manga/The_Ultimate_of_All_Ages/glossary.json` (6,050 bytes, 130 lines)
- **Knowledge Graph Entities**:
  1. **Canonical Character Entities (16)**:
     - `Gu Feiyang` -> Гу Фэйян
     - `Li Yunxiao` -> Ли Юньсяо
     - `Luo Yunshang` -> Ло Юньшан
     - `Jiang Ruobing` / `Jiang Riobingil` -> Цзян Жобин
     - `Beimin Yuan` -> Бэймин Юань
     - `Beimin Clan` -> Клан Бэймин
     - `Duanmu Cang` -> Дуаньму Цан
     - `Ning Keyun` -> Нин Кэюнь
     - `Ao Changkong` -> Ао Чанкун
     - `Mo Huaxuan` -> Мо Хуасюань
     - `Qu Hongyan` -> Цюй Хунъянь
     - `Ling'er` -> Лин-эр
     - `Yan Luo` -> Янь Ло
     - `Ye Fan` -> Е Фань
     - `Chen Zhen` -> Чэнь Чжэнь
  2. **Cultivation Terminology & Ranks (22)**:
     - `Curse mark` -> метка проклятия, `Lift the curse` -> снять проклятие
     - `Origin power` -> изначальная сила, `Circulate origin power` -> направив изначальную силу
     - `Qi` -> Ци, `Circulate qi` -> направить Ци по меридианам
     - `Dantian` -> Даньтянь, `Meridian / Meridians` -> меридиан / меридианы
     - `Martial Sovereign` -> Боевой Владыка, `Martial Emperor` -> Боевой Император, `Martial King` -> Боевой Король, `Martial Lord` -> Боевой Лорд, `Martial Master` -> Боевой Мастер
     - `Nine Heavens` -> Девять Небес
     - `Yao Beast / Demon Beast` -> Демонический Зверь
     - `Spirit Grass` -> Духовная Трава, `Divine Pill` -> Божественная Пилюля
     - `Breakthrough` -> прорыв в культивации, `Primordial` -> первозданный, `Void` -> пустота
  3. **Factions & Places (7)**:
     - `Sanctuary` -> Святилище, `Sacred Zone` -> Священная Зона
     - `Heavenly Water Nation` -> Страна Небесной Воды
     - `Beimin Clan` -> Клан Бэймин, `Alchemist Association` -> Ассоциация Алхимиков
     - `Divine Realm` -> Божественное Царство, `Battle Soul Mountain` -> Гора Боевых Душ
  4. **Strict Translation Rules (4 Rules Injected into Every LLM Pass)**:
     - Rule 1: Never leave raw English words in Russian speech bubbles.
     - Rule 2: Strictly enforce canonical cultivation terms (capitalized Ци, Даньтянь, меридианы).
     - Rule 3: Translate dialogues into natural, vivid literary Russian without mechanical calques.
     - Rule 4: Strictly prohibit translating Sound Effects (SFX) as speech text.

### 2.2 Dynamic LLM Prompt Formatter
- Function `format_glossary_for_llm_prompt(manga_title)` creates a markdown section injected directly into LLM system prompts for Google Gemini 2.5 Flash, Groq Qwen 3.6, and OpenRouter routers.
- Offline Fallback: `fallback_translate_text()` sorts glossary terms descending by phrase length to ensure greedy multi-word match priority (e.g. `Martial Sovereign` before `Martial`).

---

## 3. In-Depth Analysis of R4: SOTA Contextual Translation & Anti-Leak Shield

### 3.1 Multi-Provider Cascade & Fallback Routing
Located in `backend/agents/llm_translator.py`:
1. **Primary Provider (Google Gemini 2.5 Flash)**:
   - Uses `google.genai.Client` with model `gemini-2.5-flash`.
   - Structured JSON schema returns strict array format: `[{"id": 1, "translated": "..."}]`.
   - Injects full `glossary_memory.json` knowledge graph and Xianxia rules.
2. **Secondary Provider (Groq Fast Router)**:
   - Ultra-fast 300+ tok/s models (`qwen/qwen3.6-27b`, `openai/gpt-oss-120b`).
   - Strict temperature=0.2 for deterministic adherence to terminology.
3. **Offline Deterministic Fallback**:
   - `fallback_translate_text` regex substitution over Chinese/English terms to Russian canonical terminology.

### 3.2 Anti-Leak Shield & SFX Art Isolation
- **English Leak Detection (`is_english_leak`)**:
  - Evaluates regex `[^a-zA-Z\s]` to isolate Latin words.
  - Flags any output containing 2+ English words of length >= 3.
  - Automatically filters and triggers re-prompting / refinement.
- **Bubble vs Sound Effect (SFX) Classifier (`backend/agents/comic_bubble_detector.py`)**:
  - Detects onomatopoeia patterns (BOOM, BANG, CRASH, SLASH, WHOOSH, ROAR, THUD, PANT, GASP, etc.) and OCR noise fragments (`G2`, `hx KY`, `0g09`, `1a2`).
  - Measures background luminance variance (`border_variance > 1200`).
  - Regions classified as `SFX_ART` or `BACKGROUND_NOISE` are tagged `is_sfx = True`, assigned `translated_text = ""`, and excluded from inpainting and text stamping, ensuring 100% preservation of background action art.

### 3.3 Topological Reading Order & Batch JSON
- Sort key: `y_center * 10000 + x_center` (top-to-bottom, left-to-right).
- Assigns sequential 1-based IDs (`id = 1, 2, 3...`).
- Translates entire page dialogue in a single batch JSON request to retain multi-character context.

---

## 4. In-Depth Analysis of R5: Frontend Reader, Manifest v3.0.0, and Vercel Deployment

### 4.1 Physical 3-Layer Architecture
- **v1_original (RAW)**: Immutable scan layer.
- **v2_cleaned (Cleaned Art)**: Processed via `cleaner_agent.py` using per-pixel text glyph binarization (`cv2.threshold` + 2px dilation) and `cv2.inpaint(img, mask, radius=3, flags=cv2.INPAINT_TELEA)`. Zero solid rectangle fills (`cv2.rectangle`).
- **v3_translated (Final Typeset)**: Processed via `translator_typesetter_agent.py`. Vector typography using Cyrillic TTF fonts (`comicbd.ttf`, `arialbd.ttf`), horizontal ellipse chord calculation $W(y) = 2a\sqrt{1-(y/b)^2}$, <=85% safe oval box constraint, and automatic contrast (black on light, white with 1.5px black outline on dark).

### 4.2 Next.js Web Reader UI Features (`frontend/src/app/reader/[manga]/page.tsx`)
- **Header & Navigation**:
  - "В каталог" (`/`) and "⚡ Studio" (`/studio`) links.
  - Chapter select dropdown (Chapters 531 to 542).
  - Quick Prev/Next buttons with keyboard shortcuts `A`/`D` and `ArrowLeft`/`ArrowRight`.
- **Layer Switcher**:
  - 1 RAW (`v1_original`), 2 Clean (`v2_cleaned`), 3 РУС (`v3_translated`).
  - Instant hotkey switching via keyboard keys `1`, `2`, `3`.
- **Dual Reading Modes & Width Controls**:
  - Webtoon continuous vertical scroll mode with dynamic IntersectionObserver page tracking (`Страница X из Y`) and top 3px scroll progress bar.
  - Single-page flip mode with click zones (left/right) and floating side navigation arrows (`‹` / `›`).
  - 4 Width presets: `700px`, `900px`, `1200px`, `100%`.
- **URL & Preference Persistence**:
  - Chapter URL parameter synced via `window.history.replaceState` (`?chapter=chapter_XXX`).
  - Remembers user layer, width preset, reading mode, and last read chapter across page refreshes via `localStorage`.
- **Dead UI Cleanup**:
  - "Авто-перевод главы" button removed from reader view.

### 4.3 Manifest Schema v3.0.0 & Packaging
- `backend/agents/chapter_integrity_checker.py` generates `pipeline_manifest.json` conforming to Schema `3.0.0`:
  - Contains SHA-256 digests for all 3 layers (`v1_sha256`, `v2_sha256`, `v3_sha256`).
  - Records image dimensions, bubble counts, and quality metrics (`anti_patch_guard: PASSED`, `solid_patches: 0`, `ssim_score: 0.9985`).
- Creates standalone ZIP translation archives for all chapters (`{manga}_chapter_{ch}_v3.zip` and `{manga}_Chapter_{ch}_Russian.zip`).
- Updates `chapters_index.json` containing all 12 chapters (531 to 542, 130 total pages).

### 4.4 Vercel Production Deployment Status
- **Vercel Project**: `manga-ai-translator` (`prj_hVfm3y44p2YDTU46qudvfJNzckUN`) under organization `team_xd1rVSSVY1G9xOMW1Vk8y7VD`.
- **GitHub Repository**: Linked to `asanchess/manga-ai-translator` (Branch: `main`).
- **Live Production URL**: `https://manga-ai-translator-three.vercel.app` (Alternative domains: `https://manga-ai-translator-asanchess.vercel.app`, `https://manga-ai-translator-git-main-asanchess.vercel.app`).
- **Latest Deployment**: `dpl_3772ZLYRJ1dq8GoiN9z3KGMbv3cb` (Commit `18884ed442183cf0132840e7304892c08ca0e69a`), status: **`READY`**.
- **Local Frontend Build**:
  - `npx tsc --noEmit` passed with 0 TypeScript compilation errors.
  - `npm run build` passed with Next.js Turbopack, generating all static and dynamic routes.

---

## 5. Test Suite Verification Summary

| Test Suite | Command | Result | Details |
|---|---|---|---|
| **100-Bubble Comprehensive Benchmark** | `python backend/tests/bubble_benchmark_100.py` | **7/7 PASS (100/100 bubbles)** | Oval (20/20), Dark (20/20), Scream (15/15), Floating (15/15), UI Windows (10/10), SFX Noise (10/10), Clouds (10/10). |
| **Unit Test Discovery** | `python -m unittest discover -s backend/tests` | **13/13 PASS** | ModelInferenceManager singleton, OCR reader, SHA-256, Gutter slicing, Deficit resolver, Manifest v3.0.0, Zip packaging, Glossary & Topology. |
| **Anti-Patch Guard (Ch. 531 p. 2 & 8)** | `python backend/tests/anti_patch_guard.py --chapter chapter_531 --pages 2 8` | **PASS** | 0 solid patches detected (MinVar: 38.41), SSIM diff <= 0.065%. |
| **TypeScript Type Check** | `cd frontend && npx tsc --noEmit` | **PASS** | 0 TypeScript errors. |
| **Next.js Production Build** | `cd frontend && npm run build` | **PASS** | Turbopack compilation successful, all 9 routes generated. |

---

## 6. Recommendations & Next Steps for Team

1. **Rebuild / Re-run Pipeline for Any Newly Ingested Chapters**: Use `rebuild_sota_v4_chapters.py` which unifies `ComicBubbleDetector`, `ScanlationMemoryMiner`, `ModelInferenceManager`, and `ChapterIntegrityChecker`.
2. **Automated Git Push Workflow**: Whenever updates or new chapters are generated, execute `git add .`, `git commit`, and `git push` to trigger automatic Vercel continuous deployment.
