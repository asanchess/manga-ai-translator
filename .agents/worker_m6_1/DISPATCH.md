## 2026-08-23T10:44:00Z
You are the Builder / Worker for Milestone 6 (Next.js Studio Dashboard & Manga Reader Overhaul) of the «Manga AI Translator Studio» project.
Your working directory is: c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m6_1
You MUST read the following authoritative files first before starting:
1. c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
2. c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
3. c:\Users\asana\OneDrive\Desktop\Manga\PROJECT.md
4. c:\Users\asana\OneDrive\Desktop\Manga\.agents\explorer_frontend_1\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Write Boundaries:
You own exclusively:
- `c:\Users\asana\OneDrive\Desktop\Manga\frontend\src\app\reader\[manga]\page.tsx`
- `c:\Users\asana\OneDrive\Desktop\Manga\frontend\src\app\reader\[manga]\page.module.css` (if needed)
- `c:\Users\asana\OneDrive\Desktop\Manga\frontend\src\app\studio\page.tsx`
- `c:\Users\asana\OneDrive\Desktop\Manga\frontend\src\app\studio\page.module.css` (if needed)
- `c:\Users\asana\OneDrive\Desktop\Manga\frontend\src\app\api\studio\mangas\route.ts`

Tasks:
1. Overhaul Manga Reader (`src/app/reader/[manga]/page.tsx`):
   - Fix URL Query & LocalStorage State Persistence: on page load / refresh, immediately parse `?chapter=chapter_XXX` from `window.location.search` or `localStorage`. Guard `window.history.replaceState` so refreshing on `?chapter=chapter_538` stays on Chapter 538.
   - Prominent «Скачать главу (ZIP)» button in top bar: linking to `/manga/${cleanManga}/chapter_${currentChapter.number}/${cleanManga}_Chapter_${currentChapter.number}_Russian.zip` with backend fallback `http://localhost:8000/api/studio/download/...`.
   - Burger Navigation Drawer: `☰` burger button opening drawer with manga title, total chapters badge, «← В каталог», chapter jump list with completion badges (v1, v2, v3), reader mode selector (Webtoon vs Paginated), width preset buttons, shortcuts cheat sheet.
   - Multi-layer switch: visual pill toggles for `1 RAW`, `2 Clean`, `3 RUS` + hotkeys 1, 2, 3.
   - Keyboard Navigation: A/D for chapter, ArrowLeft/ArrowRight for pages.
   - Clean up defunct buttons: ensure no broken or defunct auto-translate buttons exist in reader view.

2. Overhaul Studio Dashboard (`src/app/studio/page.tsx`):
   - Batch Range Launcher: Mode selector (single vs batch range 531-542), inputs, run button triggering backend batch API.
   - Drag & Drop Upload Zone: accept files and folders.
   - Real-Time SSE Progress Visualizer: connect to `/api/pipeline/stream/{taskId}` using EventSource or SSE stream reader. Display multi-stage progress bar, honest error logs / retry states.
   - Interactive Chapter Library Grid: table/card grid with chapters (531-542), columns: Chapter number, pages count, layer indicators (v1 RAW, v2 Clean, v3 РУС), actions: «📖 Читать» and «📥 Скачать .ZIP».

3. Fix `src/app/api/studio/mangas/route.ts`:
   - Parse `data.mangas` properly from `chapters_index.json` to prevent runtime `TypeError`.

4. Verification:
   - Run `cd frontend && npx tsc --noEmit` (must exit 0 with 0 errors).
   - Run `cd frontend && npm run build` (must complete successfully).
5. Document all changes and verification results in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m6_1\handoff.md`.
6. Send completion message back to parent orchestrator.
