## 2026-08-22T12:57:07Z
You are the Builder / Worker for Milestone M4: Next.js Web Reader Overhaul & UI Persistence.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m4
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
Project Spec: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_orchestrator_1\PROJECT.md

Scope & Tasks for M4:
1. Overhaul `frontend/src/app/reader/[manga]/page.tsx` and its CSS module (`reader.module.css`):
   - **Header & Navigation**:
     - "В каталог" (`/`) back link.
     - Chapter dropdown listing all chapters (531 to ongoing).
     - "Предыдущая" / "Следующая" chapter navigation buttons in header and footer with hotkeys (`A`/`D` and `ArrowLeft`/`ArrowRight`).
   - **Layer Switcher**:
     - Standardized buttons: `1 RAW`, `2 Clean`, `3 РУС` with active highlight styling.
     - Keyboard shortcuts: `1`, `2`, `3` keys seamlessly toggle between layers.
   - **Display Modes & Progress**:
     - 4 width presets: `700px`, `900px`, `1200px`, `100%` (or narrow 700px / standard 900px / wide 1200px / full 100%).
     - Dual reading modes: `Webtoon` (vertical continuous scroll) vs `Single Page` (page-by-page flip mode with click zones and keyboard arrow navigation).
     - Dynamic "Страница X из Y" indicator (tracked via IntersectionObserver in Webtoon mode or active index in Single Page mode).
     - Top reading scroll progress bar (3px height indicating scroll percentage).
   - **Dead UI Removal**:
     - Remove "⚡ Авто-перевод главы" button and pipeline mission control/debug logs runner from reader view.
     - Audit and clean stubs in AI Studio (`frontend/src/app/studio/page.tsx`).
   - **URL & State Persistence**:
     - Read initial chapter from query parameter `?chapter=chapter_XXX`.
     - Sync chapter change via `window.history.replaceState` and `localStorage.setItem('last_read_chapter', currentChapter)`.
     - Ensure refreshing the page (F5) stays on the exact current chapter without reset.
     - Persist user preferences (layer, width, reading mode) in `localStorage`.
2. Verify TypeScript compilation:
   - Run `cd frontend && npx tsc --noEmit` to ensure 0 type errors.
3. Write `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m4\changes.md` and `handoff.md`.
4. Automatically commit and push all changes to Git per AGENTS.md rules.
5. Send a completion message to the parent orchestrator.
