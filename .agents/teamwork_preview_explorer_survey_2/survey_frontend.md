# Frontend & Reader Architecture Survey Report
**Project:** Manga AI Translator (v3.0 SOTA Enterprise Standard)  
**Date:** 2026-08-22  
**Role:** Frontend & Reader Explorer  
**Artifact:** `survey_frontend.md`

---

## 1. Executive Summary

An in-depth investigation was performed across the `frontend/` directory (Next.js 16 App Router, React 19, TailwindCSS v4, CSS Modules). The frontend currently provides three main views:
1. **Catalog / Landing Page (`/` at `src/app/page.tsx`)**: Title discovery, chapter links, feature overview.
2. **Web Reader (`/reader/[manga]` at `src/app/reader/[manga]/page.tsx`)**: The reading interface displaying chapter pages with multi-layer rendering.
3. **AI Studio (`/studio` at `src/app/studio/page.tsx`)**: Interactive translation studio with URL/file ingestion and split-slider comparison.

While core scaffolding is functional, there are several key gaps against the v3.0 SOTA Enterprise specification in navigation, layer toggling, display modes, dead UI removal, and state persistence.

---

## 2. Comprehensive Area-by-Area Analysis

### 2.1 Header & Navigation

#### Current Implementation
- **Back Navigation**: `<Link href="/" className={styles.backLink}>← Каталог</Link>` in `src/app/reader/[manga]/page.tsx:211`.
- **Chapter Dropdown**: `<select className={styles.chapterSelect} value={selectedChapterIdx} ...>` in `src/app/reader/[manga]/page.tsx:220-231`.
- **Prev / Next Buttons**: Located **only in the sticky footer** (`src/app/reader/[manga]/page.tsx:380-397`), missing from the sticky header.
- **Hotkeys**: `ArrowLeft` / `a` / `A` for previous chapter, `ArrowRight` / `d` / `D` for next chapter (`src/app/reader/[manga]/page.tsx:172-173`).

#### Gaps & Requirements
1. **Catalog Link**: Must be standardized to `"В каталог"` (linking to `/`).
2. **Header Chapter Controls**: In addition to the dropdown, header should include compact `‹` (Prev) and `›` (Next) buttons for quick chapter switching without scrolling to the footer.
3. **Dropdown Population**: Must dynamically list chapters starting from 531 to ongoing (e.g. `Глава 531`, `Глава 532`, ..., `Глава 542+`).
4. **Hotkeys Support**:
   - `A` / `D` and `ArrowLeft` / `ArrowRight` for chapter / page navigation.
   - Hotkey listener already guards input fields (`HTMLInputElement`, `HTMLTextAreaElement`, `HTMLSelectElement`), which is good.
   - When single-page mode is enabled, `ArrowLeft` / `ArrowRight` should flip pages, while `A` / `D` (or at boundaries) navigate chapters.

---

### 2.2 Layer Switcher (1 RAW / 2 Clean / 3 РУС)

#### Current Implementation
- **Buttons**:
  - `1 Оригинал` (`v1_original`)
  - `2 Клининг` (`v2_cleaned`)
  - `3 Перевод (РУС)` (`v3_translated`)
- **Hotkeys**: Pressing `1`, `2`, or `3` updates `currentVersion` state (`src/app/reader/[manga]/page.tsx:169-171`).
- **Active Highlight**: `.activeBtn` has a vibrant gradient (`linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%)`).
- **Fallback**: `const images = requestedImages.length > 0 ? requestedImages : (currentChapter.versions.v1_original || []);`.

#### Gaps & Requirements
1. **Standardized Labels**: Change button text to:
   - `[1] RAW` (Scan layer)
   - `[2] Clean` (Cleaned art)
   - `[3] РУС` (Final typeset)
2. **Missing Layer Feedback**: If user switches to `Clean` or `РУС` and the layer is still being generated or missing, show a subtle banner/pill ("Слой РУС формируется, показан RAW") instead of silent replacement.
3. **Smooth Switching**: Ensure seamless switching without layout shifts between layers since all versions share identical dimensions and aspect ratios.

---

### 2.3 Display Modes & Progress

#### Current Implementation
- **Width Toggles**: Only 3 options (`narrow` = 720px, `medium` = 860px, `wide` = 1100px) labeled `S`, `M`, `L`.
- **Display Modes**: Only continuous vertical scrolling (Webtoon mode). No single-page reading mode exists.
- **Page Indicator**: Only a static badge `Стр. {i + 1}` on each image, and footer text `{images.length} страниц`.
- **Reading Progress Bar**: Absent (only an agent pipeline execution bar exists).

#### Gaps & Requirements
1. **4 Width Presets**:
   - `700px` (Compact)
   - `900px` (Standard / Balanced)
   - `1200px` (Wide / Desktop)
   - `100%` (Full screen / Responsive)
2. **Reading Mode Toggle**:
   - `📜 Webtoon (Лента)`: Continuous vertical scroll of pages.
   - `📄 Single Page (Постранично)`: Displays 1 page centered at a time.
     - Left click (or Left Arrow / A): Previous page.
     - Right click (or Right Arrow / D): Next page.
     - Page selector bar / jump-to-page input.
3. **Dynamic Page Indicator ("Страница X из Y")**:
   - In Webtoon mode: An `IntersectionObserver` or scroll listener calculates which page is currently in the center of the viewport and updates the floating / header indicator: `Страница 4 из 12`.
   - In Single Page mode: Directly reflects `currentPage + 1` of `totalPages`.
4. **Scroll Progress Bar**:
   - A fixed slim reading progress bar at the very top (or bottom) of the screen (`height: 3px`, gradient `#ff4b2b` to `#00d2ff`), showing 0% to 100% progress through the chapter.

---

### 2.4 Dead UI Removal & AI Studio Audit

#### Current Implementation
- **In Reader (`src/app/reader/[manga]/page.tsx:288-352`)**:
  - Contains `<section className={styles.missionControl}>`:
    - 5 agent badges (`Scraper`, `5-Pass Cleaner`, `OpenRouter LLM`, `Pro Typesetter`, `QA Inspector`)
    - `<button className={styles.triggerBtn}>⚡ Запустить автоперевод главы 531</button>`
    - Log drawer toggle and polling `fetch('/api/pipeline/status')` every 1200ms
  - **Verdict**: This is development dead UI that clutters the reader and distracts the user from reading.

#### Gaps & Recommendations
1. **Remove Dead UI from Reader**:
   - Eliminate `missionControl`, `handleRunPipeline`, `pipeline` state, and pipeline polling `useEffect` from `ReaderPage`.
   - The reader must be a pure, high-performance reading application.
2. **Audit AI Studio (`src/app/studio/page.tsx`)**:
   - AI Studio is the dedicated management console.
   - Replace hardcoded `http://localhost:8000/...` URLs with relative Next.js API routes or env-based backend URLs.
   - In Split-Slider comparison, replace hardcoded `page_003.webp` with dynamic selection from available pages of the active chapter.
   - Fix AssistantChat button overlay position to ensure it does not obscure reader footer controls.

---

### 2.5 URL & State Persistence

#### Current Implementation
- Reader reads chapter on load:
  `const chParam = urlParams.get('chapter');` (`chapter_531` -> `531`).
- Fallback: `localStorage.getItem('manga_${manga}_last_chapter')`.
- State sync in `useEffect`:
  `const newUrl = `${window.location.pathname}?chapter=chapter_${chapterNumber}`;`
  `window.history.replaceState({ path: newUrl }, '', newUrl);`
  `localStorage.setItem('manga_${manga}_last_chapter', chapterNumber);`

#### Gaps & Requirements
1. **Key Standardization**:
   - Save to both `last_read_chapter` and `manga_${manga}_last_chapter` for cross-title and title-specific persistence.
2. **F5 Refresh Integrity**:
   - Prevent race condition where `selectedChapterIdx = 0` briefly overwrites `?chapter=chapter_535` back to `chapter_531` during initial data fetching.
   - Initial state should read `window.location.search` or `localStorage` during initial load before triggering URL replaceState.
3. **Preferences Persistence**:
   - Store and restore:
     - `reader_width` (`'700px' | '900px' | '1200px' | '100%'`)
     - `reader_mode` (`'webtoon' | 'single'`)
     - `reader_layer` (`'v1_original' | 'v2_cleaned' | 'v3_translated'`)

---

## 3. Component Architecture Blueprint

### Proposed Reader Component Breakdown

```
frontend/src/app/reader/[manga]/
├── page.tsx                     # Main Reader Controller & State Container
├── page.module.css              # SOTA Theme Styles (Dark Glassmorphism)
└── components/
    ├── ReaderHeader.tsx         # Sticky Header ("В каталог", Title, Dropdown, Prev/Next, Layer Switcher, Width/Mode controls)
    ├── LayerSwitcher.tsx        # [1 RAW] [2 Clean] [3 РУС] with keyboard shortcuts & tooltips
    ├── ReadingProgressBar.tsx   # Top-fixed 3px gradient progress bar (0-100%)
    ├── WebtoonView.tsx          # Continuous scroll stream with IntersectionObserver page tracking
    ├── SinglePageView.tsx       # Paginated single-page viewer with click-to-flip zones & jump controls
    ├── ReaderFooter.tsx         # Bottom navigation bar, dynamic "Страница X из Y", scroll-to-top
    └── PageIndicator.tsx        # Floating dynamic page badge
```

### Proposed State Structure

```typescript
interface ReaderSettings {
  layer: 'v1_original' | 'v2_cleaned' | 'v3_translated';
  width: '700px' | '900px' | '1200px' | '100%';
  mode: 'webtoon' | 'single';
}

interface ChapterState {
  currentChapterIdx: number;
  currentPageIdx: number;
  totalPages: number;
  scrollProgress: number; // 0 to 100
}
```

---

## 4. Verification & Readiness Assessment

| Requirement Item | Current Status | Effort to Implement | Risk Level |
|---|---|---|---|
| Header: "В каталог" link + Prev/Next in header | Partial (Text is "Каталог", Prev/Next only in footer) | Low (15 min) | Very Low |
| Chapter Dropdown (531 to ongoing) | Working (Dynamic from API) | Low (10 min) | Very Low |
| Hotkeys (A/D, ArrowLeft/Right) | Working (Chapter navigation) | Low (15 min) | Very Low |
| Layer Switcher: 1 RAW / 2 Clean / 3 РУС | Working with legacy labels | Low (15 min) | Very Low |
| Layer Hotkeys 1, 2, 3 | Working | None (Complete) | Very Low |
| Width Toggles (700px, 900px, 1200px, 100%) | Partial (3 sizes S/M/L) | Low (20 min) | Very Low |
| Webtoon Scroll vs Single-Page Mode | Webtoon only, Single-page missing | Medium (45 min) | Low |
| Page Indicator ("Страница X из Y") | Partial (Static only) | Low (25 min) | Very Low |
| Scroll Progress Bar | Missing | Low (20 min) | Very Low |
| Dead UI Removal ("Авто-перевод" in reader) | Present (Needs deletion) | Low (15 min) | Very Low |
| AI Studio Stub Audit | Present (Hardcoded URLs) | Medium (30 min) | Low |
| URL & State Persistence (`?chapter=chapter_XXX`) | Partial (Working with race condition) | Low (20 min) | Very Low |

---

## 5. Next Steps for Builder

1. Refactor `src/app/reader/[manga]/page.tsx`:
   - Remove `missionControl` and pipeline execution code.
   - Standardize Header with "В каталог", chapter dropdown, Prev/Next buttons, layer switcher (`1 RAW`, `2 Clean`, `3 РУС`), width presets (`700px`, `900px`, `1200px`, `100%`), and mode toggles (`Webtoon` / `Single Page`).
   - Implement dynamic page detection and top reading progress bar.
   - Implement single-page navigation view with click zones and keyboard support.
   - Ensure clean URL sync (`?chapter=chapter_XXX`) and `localStorage` persistence without race conditions.
2. Clean up AI Studio (`src/app/studio/page.tsx`) endpoints and slider assets.
3. Test full reader workflow on chapters 531 to 542 across all 3 layers.
