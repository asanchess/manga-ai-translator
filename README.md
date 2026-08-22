# Manga AI Translator v3.0 SOTA Enterprise

An enterprise-grade, fully automated AI translation and typesetting pipeline for Chinese Manhua, Korean Manhwa, and Japanese Manga into Russian, accompanied by a high-performance Next.js 14 Web Reader.

---

## 🌟 Key Architecture & Capabilities

1. **Strict 3-Layer Physical Isolation:**
   - `v1_original`: Authentic high-resolution raw scans (Read-Only).
   - `v2_cleaned`: Inpainted background art generated via Telea/LaMa morphology. Zero solid rectangle wipes (`cv2.rectangle` strictly prohibited).
   - `v3_translated`: Vector typesetting layer consuming `v2_cleaned` with mathematical elliptical text centering and Cyrillic typography.

2. **Programmatic Anti-Patch Guard Quality Validation:**
   - **Check A (Solid Patch Detector):** Detects zero/low-variance fills ($\sigma^2 < 1.0$) in bounding boxes to prevent canvas destruction.
   - **Check B (Background SSIM Difference):** Enforces Structural Similarity $\text{SSIM} \ge 0.995$ (background degradation $\le 0.50\%$) on non-bubble canvas.

3. **Persistent Xianxia Terminology & Batch LLM Translation:**
   - Dedicated `glossary.json` loaded for accurate Xianxia character names (*Гу Фэйян*, *Ли Юньсяо*), factions (*Клан Бэймин*, *Святилище*), and cultivation realms (*Боевой Владыка*, *Даньтянь*, *Ци*).
   - Automatic prompt injection and strict 1-based sequential dialogue ID pairing.

4. **Mathematical Dialogue Topology & Elliptical Chord Typesetting:**
   - Reading order topological sort: $y_{\text{center}} \times 10000 + x_{\text{center}}$.
   - Elliptical chord text wrapping: $w(y) = 2a\sqrt{1 - (y/b)^2}$ bounded within $\le 85\%$ safe oval limit.
   - Dynamic auto-contrast: crisp black font on light bubbles, bright white font with outline on dark/action bubbles.

5. **High-Speed ML Inference Singleton & Deficit Resolver:**
   - `ModelInferenceManager` singleton holding EasyOCR / Inpainting models in memory with dual ThreadPool / ProcessPool executors.
   - `ChapterIntegrityChecker` featuring scraper mirror rotation and intelligent gutter-aware panel segmenter (`find_optimal_gutter_cuts`) to ensure $\ge 8$ pages per chapter.
   - Pipeline Manifests v3.0.0 (`pipeline_manifest.json`) with SHA-256 layer checksums and standalone chapter `.zip` translation archives.

6. **Next.js 14 Modern Web Reader UX:**
   - **Instant Layer Switching:** Hotkeys `1` (RAW), `2` (Cleaned), `3` (Russian Translation).
   - **Dual Reading Modes:** Seamless Webtoon scroll (with 3px top reading progress bar and viewport page tracker) and Single Page flipbook mode.
   - **Keyboard Navigation:** `A`/`D` and `←`/`→` for chapters and pages.
   - **Width Presets:** `700px`, `900px`, `1200px`, `100%`.
   - **State Persistence:** URL query sync (`?chapter=chapter_532`) and `localStorage` caching resilient to browser refreshes (F5).

---

## 📁 Repository Structure

```
Manga/
├── backend/
│   ├── agents/
│   │   ├── cleaner_agent.py               # Inpainting & glyph removal (Telea/LaMa)
│   │   ├── translator_typesetter_agent.py # Elliptical chord wrapping & vector typography
│   │   ├── ocr_engine.py                  # 2-pass OCR & topological bubble sorting
│   │   ├── llm_translator.py              # Batch JSON translation & glossary prompt injection
│   │   ├── model_inference_manager.py     # High-speed ML inference singleton
│   │   ├── chapter_integrity_checker.py   # Chapter audit, deficit resolver, manifests & zips
│   │   └── manga_pipeline_service.py      # Unified end-to-end orchestration service
│   ├── tests/
│   │   ├── anti_patch_guard.py            # Programmatic Anti-Patch Guard test harness
│   │   ├── test_typesetter_layout.py      # Elliptical typesetting unit tests
│   │   ├── test_glossary_and_topology.py  # Glossary & reading order unit tests
│   │   └── test_model_inference_and_integrity.py # Singleton & chapter parity tests
│   └── data/manga/The_Ultimate_of_All_Ages/
│       ├── glossary.json                  # Persistent Xianxia terminology dictionary
│       └── chapter_XXX/                   # v1_original/, v2_cleaned/, v3_translated/, pipeline_manifest.json, *.zip
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                       # Catalog & chapter selection
│   │   ├── studio/page.tsx                # Interactive AI translation studio
│   │   └── reader/[manga]/page.tsx        # Next.js Web Reader with layer switcher & hotkeys
│   └── public/manga/                      # Synchronized public reader assets & chapters_index.json
├── production_artifacts/
│   ├── Spec.md                            # Architectural Specification
│   ├── Ongoing_Sync_Report.md             # Chapter sync & quality matrix
│   └── QA_Report.md                       # Comprehensive QA and audit log
├── AGENTS.md                              # Lean agent system guidelines & domain rules
└── README.md                              # Enterprise documentation
```

---

## 🚀 Getting Started

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn opencv-python easyocr pillow numpy scikit-image requests
   ```

2. Run backend test suites:
   ```bash
   # 1. Anti-Patch Guard Full Audit
   python backend/tests/anti_patch_guard.py --all

   # 2. Typesetter Layout & Elliptical Boundary Tests
   python backend/tests/test_typesetter_layout.py

   # 3. Glossary & Topology Tests
   python backend/tests/test_glossary_and_topology.py

   # 4. ML Singleton & Chapter Integrity Tests
   python backend/tests/test_model_inference_and_integrity.py
   ```

3. Launch FastAPI backend server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

### Frontend Setup

1. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Typecheck and build:
   ```bash
   npx tsc --noEmit
   npm run build
   ```

3. Launch Next.js development reader:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` to browse the catalog and read chapters with instant layer switching (`1`/`2`/`3`).

---

## 🧪 Quality Standards & Guarantees

* **Zero Rectangular Wipes:** No `cv2.rectangle` artifacts in production artwork.
* **SSIM Background Preservation:** $\ge 99.5\%$ structural similarity outside bubble masks.
* **Typographic Legibility:** Cyrillic TTF fonts with dynamic oval font scaling ($38\text{px} \to 12\text{px}$).
* **F5 Resilience:** Full state and URL synchronization across page refreshes.
