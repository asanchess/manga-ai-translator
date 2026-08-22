# Specification: Manga & Manhua AI Translation & Inpainting Pipeline v4.0

## 1. Architectural Blueprint & Core Innovations

The Manga AI Translator v4.0 pipeline establishes an autonomous, scanlation-grade processing and delivery system for Manga & Manhua. It solves sound effect corruption, eliminates English leaks, dynamically mines multi-chapter terminology graphs, and serves publication-ready releases via a modern Next.js 14 web reader deployed live on Vercel.

```
                  +---------------------------------------------------+
                  |            v1_original (Scan Layer)               |
                  +---------------------------------------------------+
                                            |
                                            v
                  +---------------------------------------------------+
                  |         Comic Bubble & SFX Classifier             |
                  |  - Distinguish SPEECH_BUBBLE vs SFX_ART           |
                  |  - Filter onomatopoeia / combat art noise         |
                  +---------------------------------------------------+
                       /                                     \
                      /                                       \
          [SPEECH_BUBBLE]                                   [SFX_ART]
                 |                                              |
                 v                                              v
  +-------------------------------+             +-------------------------------+
  |  Per-Pixel Glyph Inpainting   |             |     100% Untouched Layer      |
  |  - Adaptive Otsu + Distance   |             |  - Zero canvas patches        |
  |  - cv2.inpaint (Telea / LaMa) |             |  - Zero OCR stamp corruption  |
  +-------------------------------+             +-------------------------------+
                 |                                              |
                 v                                              |
  +---------------------------------------------------+         |
  |          v2_cleaned (Cleaned Artwork)             | <-------+
  +---------------------------------------------------+
                 |
                 v
  +---------------------------------------------------+
  | 10-Chapter Scanlation Memory & Anti-Leak Shield   |
  | - Persistent Knowledge Graph (glossary_memory)    |
  | - SOTA LLM (Gemini 2.5 Flash / Groq Qwen / Fallback) |
  | - Anti-Leak Shield (Zero English words in output) |
  +---------------------------------------------------+
                 |
                 v
  +---------------------------------------------------+
  |           Vector Typography & Typesetting         |
  | - Elliptical Chord Equation W(y) = 2a*sqrt(1-y²/b²)|
  | - Dynamic Contrast (Black on Light / White Outline)|
  | - Cyrillic TTF (comicbd, arialbd, segoeuib)       |
  +---------------------------------------------------+
                 |
                 v
  +---------------------------------------------------+
  |          v3_translated (Final Publication)        |
  +---------------------------------------------------+
                 |
                 +------------------------------------+
                 |                                    |
                 v                                    v
  +-------------------------------+    +-------------------------------+
  |  Integrity & Manifest Engine  |    | Live Vercel Production Reader |
  |  - Anti-Patch Guard (SSIM)    |    |  - 3-Layer Switching (1/2/3)  |
  |  - Manifests v3.0.0 & ZIPs    |    |  - Webtoon & Single-Page      |
  +-------------------------------+    +-------------------------------+
```

---

## 2. Technical Requirements & Subsystem Specifications

### R1. Bubble & SFX Classification with Zero Background Art Corruption
* **Classifier Engine (`comic_bubble_detector.py`):** Differentiates dialogue bubbles (`SPEECH_BUBBLE`, `DARK_INVERTED`, `SPIKY_SHOUT`, `SYSTEM_WINDOW`, `THOUGHT_CLOUD`) from combat action strokes and sound effects (`SFX_ART`).
* **Noise Filter:** Filters OCR junk and onomatopoeia strokes (e.g. `G2`, `hx KY`, `0g09`, `ドドド`, `BOOM`) from entering speech translation pipelines.
* **Per-Pixel Inpainting (`cleaner_agent.py`):** Uses adaptive Otsu thresholding + color Euclidean distance inside bubble contours with `cv2.inpaint(..., flags=cv2.INPAINT_TELEA)` or LaMa. Strictly prohibits `cv2.rectangle` or solid color fills.

### R2. 100-Bubble Comprehensive Benchmark Verification
* **Benchmark Harness (`backend/tests/bubble_benchmark_100.py`):** Enforces automated testing across 100 diverse bubble archetypes:
  - 20/20 Standard Oval Light Bubbles
  - 20/20 Inverted Dark Bubbles
  - 15/15 Spiky Shout Bubbles
  - 15/15 Floating Borderless Narrations
  - 10/10 System Windows
  - 10/10 SFX & Combat Noise Artifacts (0 art corruption)
  - 10/10 Thought Clouds
* **Success Criteria:** 100/100 passing tests, 0 false-positive SFX modifications, background SSIM $\ge 0.998$.

### R3. 10-Chapter Scanlation Memory Mining
* **Knowledge Graph (`glossary_memory.json` / `glossary.json`):** Dynamic terminology graph mined from the preceding 10 chapters. Captures:
  - Character Names (Gu Feiyang -> Гу Фэйян, Li Yunxiao -> Ли Юньсяо, Luo Yunshang -> Ло Юньшан)
  - Cultivation Realms & Anatomy (Dantian -> Даньтянь, Qi -> Ци, Martial Sovereign -> Боевой Владыка)
  - Sects & Factions (Beimin Clan -> Клан Бэймин, Sanctuary -> Святилище, Heavenly Water Nation -> Страна Небесной Воды)
* **Prompt Injection (`llm_translator.py`):** Formatted terminology graph injected into all LLM translation contexts with strict 1-based sequential dialogue ID contracts.

### R4. SOTA Contextual Translation & Anti-Leak Shield
* **Translation Providers:** Multi-tier failover routing across Google Gemini 2.5 Flash, Groq Qwen 3.6, and free local/external routers.
* **Anti-Leak Shield:** Post-processing validation rejecting un-translated English tokens, hallucinated tags (`*[ ]*`), or machine translation artifacts.

### R5. Vector Typography, Typesetting & Online Delivery
* **Elliptical Text Fitting:** Calculates maximal chord width $W(y) = 2a\sqrt{1 - (y/b)^2}$ bounded within $\le 85\%$ safe oval zone.
* **Dynamic Contrast & Typography:** Binary search font scaling ($38\text{px} \to 12\text{px}$), Cyrillic TTF font suite (`comicbd.ttf`, `arialbd.ttf`, `segoeuib.ttf`), black text on light backgrounds, white text with $1.5\text{px}$ black outline on dark backgrounds.
* **Live Vercel Web Reader:** Hosted at `https://manga-ai-translator-three.vercel.app`. Full support for 3-layer hotkey switching (`1`, `2`, `3`), Webtoon vertical scroll with reading progress bar, Single-Page flipbook mode, width toggles (`700px`, `900px`, `1200px`, `100%`), and persistent URL state (`?chapter=chapter_XXX`).

---

## 3. Data Schema & Interface Contracts

### Chapter Storage Layout
```
backend/data/manga/{manga_title}/
├── glossary.json
├── glossary_memory.json
└── {chapter_id}/
    ├── v1_original/
    │   ├── page_001.webp
    │   └── ...
    ├── v2_cleaned/
    │   ├── page_001.webp
    │   └── ...
    ├── v3_translated/
    │   ├── page_001.webp
    │   └── ...
    ├── pipeline_manifest.json
    ├── {manga_title}_{chapter_id}_v3.zip
    └── {manga_title}_{chapter_id}_Russian.zip
```

### Pipeline Manifest Schema (v3.0.0)
```json
{
  "version": "3.0.0",
  "manga": "The_Ultimate_of_All_Ages",
  "chapter": "chapter_531",
  "total_pages": 12,
  "layers": {
    "v1_original": { "page_count": 12, "sha256": "..." },
    "v2_cleaned": { "page_count": 12, "sha256": "..." },
    "v3_translated": { "page_count": 12, "sha256": "..." }
  },
  "quality_metrics": {
    "avg_background_ssim": 0.99953,
    "max_degradation_pct": 0.047,
    "solid_patches_detected": 0
  },
  "zip_archive": "The_Ultimate_of_All_Ages_chapter_531_v3.zip",
  "timestamp": "2026-08-23T02:15:00Z"
}
```

---

## 4. Verification Suite & Quality Assurance

| Verification Suite | Target | Criteria |
|---|---|---|
| `bubble_benchmark_100.py` | 100 Bubble Archetypes | 100/100 pass, 0 SFX false positives |
| `anti_patch_guard.py --all` | All 13 Chapters | 0 solid patches, background SSIM $\ge 0.995$ |
| `unittest discover -s backend/tests` | Core Pipeline Units | 18/18 unit tests passing |
| `npx tsc --noEmit` | Frontend Next.js 14 | 0 compilation errors |
