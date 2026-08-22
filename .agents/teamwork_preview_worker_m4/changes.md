# Changes Made — Milestone M4: Next.js Web Reader Overhaul & UI Persistence

## 1. `frontend/src/app/reader/[manga]/page.tsx`
- **Header & Navigation**:
  - Added "В каталог" (`/`) back link and `⚡ Studio` direct link.
  - Formatted manga title and dynamic chapter `<select>` dropdown.
  - Added "Предыдущая" / "Следующая" chapter navigation buttons in the sticky header and bottom footer.
  - Supported hotkeys `A` / `D` and `ArrowLeft` / `ArrowRight` (in Webtoon mode) for chapter navigation.
- **Layer Switcher**:
  - Implemented standardized `1 RAW` (`v1_original`), `2 Clean` (`v2_cleaned`), and `3 РУС` (`v3_translated`) toggle buttons with active highlight styling and badges.
  - Implemented keyboard shortcuts `1`, `2`, and `3` to instantly switch layers.
  - Persisted selected layer in `localStorage` (`manga_reader_layer`).
- **Display Modes & Width Presets**:
  - Implemented 4 width presets: `700px`, `900px`, `1200px`, and `100%` (full screen).
  - Implemented dual reading modes: `Webtoon` (vertical continuous scroll) vs `Single Page` (page-by-page flip mode).
  - In Single Page mode: click zones (left 45% / right 45%), floating chevron buttons (`‹` / `›`), keyboard arrow navigation (`ArrowLeft` / `ArrowRight`), and quick page dropdown jumper.
  - In Webtoon mode: dynamic "Страница X из Y" indicator driven by `IntersectionObserver` observing pages as they enter the reading viewport.
  - Top reading scroll progress bar (3px height) displaying exact scroll / page completion percentage with gradient styling.
- **Dead UI Removal**:
  - Completely removed "⚡ Авто-перевод главы" trigger button.
  - Removed pipeline mission control cards, progress bar for pipeline, and debug agent logs drawer from the reader view.
- **URL & State Persistence**:
  - Initial chapter is loaded from `?chapter=chapter_XXX` query parameter.
  - Fallback to `localStorage.getItem('manga_${manga}_last_chapter')` or `localStorage.getItem('last_read_chapter')`.
  - Chapter transitions update URL via `window.history.replaceState` and save to `localStorage`.
  - Refreshing with F5 stays on the exact current chapter without reset.
  - User preferences (layer, width preset, reading mode) persist in `localStorage`.

## 2. `frontend/src/app/reader/[manga]/page.module.css`
- Added styles for the top 3px scroll progress bar with glow and gradient.
- Added responsive layout for header, version selector pills, mode controls, and width preset controls.
- Added styles for sub-bar, page indicator, single page flip controls, interactive click zones (`cursor: w-resize` / `cursor: e-resize`), and floating navigation buttons.
- Styled the sticky bottom footer with chapter navigation buttons, reading progress summary, and scroll-to-top action.
- Added responsive breakpoints for desktop, tablet, and mobile views.

## 3. `frontend/src/app/studio/page.tsx`
- Audited and cleaned stubs and mock types.
- Defined explicit `StudioTaskData` and `MangaOption` interfaces.
- Dynamically fetches available mangas and chapters from `/api/studio/mangas`.
- Added image fallback error handling for split-slider comparison.
- Added direct download link to chapter `.zip` archives.
