# Comprehensive Frontend Codebase Survey Report: «Manga AI Translator Studio»

**Date**: 2026-08-23  
**Audience**: Lead Architect, Builder, QA & Auditor  
**Scope**: Next.js App Router Frontend (`frontend/`) in `c:\Users\asana\OneDrive\Desktop\Manga\frontend`  
**Status**: Exploration Complete & Verified  

---

## 1. Executive Summary

A comprehensive architectural and functional survey of the Next.js frontend codebase (`frontend/`) was performed. The frontend is built on **Next.js 16.3.1 (App Router)**, **React 19.2.8**, **Tailwind CSS v4**, and **TypeScript 5**. TypeScript compilation (`npx tsc --noEmit`) and production build (`npm run build`) succeed without fatal syntax errors. 

However, deep-dive inspection revealed **critical functional gaps, UI omissions, and logic bugs** relative to the project requirements (**R6, R4, R3**):

1. **Chapter State Reset Race Condition on Page Refresh (Acceptance Criteria Guard)**:  
   In `src/app/reader/[manga]/page.tsx`, an uncontrolled `useEffect` synchronization loop triggers `window.history.replaceState` with `chapter_531` before the async chapter index and URL search parameters finish parsing, causing refreshed pages to reset back to Chapter 531 instead of retaining the user's selected chapter.
2. **Missing Prominent «Скачать главу (ZIP)» in Reader Top Bar (R4 & R6)**:  
   The reader header lacks the required chapter ZIP download button. Readers currently have no direct way to download translation packages from the reader interface.
3. **Missing Burger Navigation Drawer in Reader (R6)**:  
   The reader lacks a slide-out / dropdown burger navigation menu for rapid chapter jumping, quick settings, and catalog return.
4. **Missing Title & Chapter Range Batch Launcher in Studio (R6)**:  
   The Studio Dashboard (`src/app/studio/page.tsx`) only provides single-chapter translation and lacks a batch range launcher (`start_chapter` to `end_chapter`, e.g., `531–542`).
5. **No SSE Progress Visualizer (Fake Polling Fallback) (R3 & R6)**:  
   Studio currently uses `setInterval` polling to `http://localhost:8000` every 1500ms and fakes a `completed` state with hardcoded logs when the backend is offline, violating R3 ("Report true status and honest error logs rather than false completion indicators"). Real Server-Sent Events (SSE) streaming is not implemented.
6. **Missing Chapter Library Grid in Studio (R6)**:  
   The Studio page lacks an interactive chapter library overview table/grid for browsing all processed chapters with status badges, page counts, instant ZIP downloads, and direct reader launch buttons.
7. **Runtime Crash Bug in `/api/studio/mangas` Route**:  
   `src/app/api/studio/mangas/route.ts` incorrectly iterates over top-level keys of `chapters_index.json` (`title`, `last_synced`, `mangas`), causing an uncaught `TypeError` when reading `.chapters` on string properties and silently falling back to a hardcoded chapter list.
8. **Broken ZIP Download Link in Studio Results Bar**:  
   The download button links to `/manga/${mangaName}/chapter_${chapterNum}.zip` which returns 404 because release archives are named `{title}_Chapter_{num}_Russian.zip`.

---

## 2. Codebase Architecture & File Tree

### 2.1 File Map

```
frontend/
├── package.json                    # Next.js 16.3.1, React 19.2.8, Tailwind CSS v4, ai SDK
├── tsconfig.json                   # Path alias @/* -> ./src/*, target ES2017
├── next.config.ts                  # Standard Next config
├── public/
│   ├── manga/                      # Static manga files, meta.json, and release ZIPs
│   │   ├── The_Ultimate_of_All_Ages/
│   │   │   ├── chapter_531/ ... chapter_542/
│   │   │   │   ├── v1/, v2/, v3/
│   │   │   │   ├── v1_original/, v2_cleaned/, v3_translated/
│   │   │   │   ├── meta.json
│   │   │   │   └── The_Ultimate_of_All_Ages_Chapter_XXX_Russian.zip
│   │   └── chapters_index.json     # Global registry of mangas and chapters
└── src/
    └── app/
        ├── layout.tsx              # Root HTML/Body, fonts, global AssistantChat
        ├── globals.css             # Theme variables, resets, custom scrollbars
        ├── page.tsx                # Catalog / Landing page
        ├── page.module.css
        ├── studio/
        │   ├── page.tsx            # Studio Dashboard (Upload, OCR options, split slider)
        │   └── page.module.css
        ├── reader/[manga]/
        │   ├── page.tsx            # Manga Reader (Webtoon / Paginated, 3 layers)
        │   └── page.module.css
        ├── components/
        │   └── AssistantChat.tsx   # Floating AI Assistant widget (ai SDK)
        └── api/
            ├── chapters/[manga]/   # Dynamic chapter & page scanner route
            │   └── route.ts
            ├── studio/mangas/      # Manga list API route (has runtime bug)
            │   └── route.ts
            ├── pipeline/run/       # Proxy/Mock route for pipeline launch
            │   └── route.ts
            ├── pipeline/status/    # Proxy/Mock route for pipeline status
            │   └── route.ts
            └── chat/               # Ollama streaming endpoint for AssistantChat
                └── route.ts
```

---

## 3. Detailed Component Analysis

### 3.1 Studio Dashboard (`src/app/studio/page.tsx`)

#### Implemented Features:
- **Options Configuration Bar**: Dropdowns for manga selection, single chapter number, source language (`auto`, `en`, `zh`, `ja`, `ko`), target language (`ru`, `en`), detector mode (`CTD`, `EagleEye`, `Hybrid`), and font style (`auto`, `anime_ace`, `cultivation`).
- **Ingestion Tabs**: Switch between URL import (`activeTab === 'url'`) and drag-and-drop file upload (`activeTab === 'upload'`).
- **Interactive Split-Slider Comparison**: Draggable comparison slider between RAW (v1) and Russian Translation (v3) or Cleaned (v2).
- **Single Chapter Actions Bar**: Footer with links to read the chapter and download ZIP.

#### Deficiencies & Defect Log:

| ID | Issue Description | Impact | Relevant Rule / Requirement |
|---|---|---|---|
| **ST-01** | **No Batch Range Launcher**: Studio only accepts a single chapter number (`chapterNum`). Users cannot trigger batch translation for ranges like `531-542`. | High | R6 ("title & chapter range batch launcher") |
| **ST-02** | **Polling instead of Server-Sent Events (SSE)**: Uses `setInterval` polling `http://localhost:8000/api/studio/tasks/${taskId}` every 1500ms rather than SSE telemetry stream. | Medium | R3 ("Stream live real-time pipeline telemetry via SSE") |
| **ST-03** | **False Completion Indicator on Error**: When fetch to backend fails, `handleStartTranslate` sets fake completed status (`status: 'completed', progress: 100`) with simulated log entries. | High | R3 ("Report true status and honest error logs rather than false completion indicators") |
| **ST-04** | **Missing Chapter Library Grid**: The studio has no overview list/table of all chapters with page counts, status pills, read buttons, and download buttons. | High | R6 ("chapter library with instant download/read actions") |
| **ST-05** | **Broken ZIP Download Link**: Studio results bar links to `/manga/${mangaName}/chapter_${chapterNum}.zip`, which results in HTTP 404 (actual files are `{title}_Chapter_{num}_Russian.zip`). | High | R4 & R6 |
| **ST-06** | **Folder Upload Missing `webkitdirectory`**: Dropzone only has `<input type="file" multiple accept="image/*,.zip">` without folder drag-and-drop / directory picker support. | Medium | R6 ("upload zone for ZIPs/raw folders") |
| **ST-07** | **Hardcoded `http://localhost:8000` URLs**: Direct `fetch` calls to `http://localhost:8000` in browser context cause CORS and portability issues when running on different hosts/ports. | Medium | Software Quality |

---

### 3.2 Manga Reader (`src/app/reader/[manga]/page.tsx`)

#### Implemented Features:
- **3-Layer Switcher**: Seamless switching between `v1_original` (RAW), `v2_cleaned` (Clean), and `v3_translated` (РУС).
- **Keyboard Shortcuts**:
  - `1`, `2`, `3`: Instant layer switching.
  - `A`, `D`: Previous / Next chapter.
  - `ArrowLeft`, `ArrowRight`: Page navigation (single mode) or chapter navigation (webtoon mode).
- **Dual Reading Modes**: Continuous vertical scroll (`webtoon`) and single page flip (`single`) with floating side arrows and left/right click zones.
- **Width Presets**: `700px`, `900px`, `1200px`, `100%`.
- **Top Scroll Progress Bar**: 3px gradient progress bar at the top of the viewport.
- **Sticky Bottom Navigation Bar**: Displays current chapter, active layer, page count, and jump to top button.

#### Deficiencies & Defect Log:

| ID | Issue Description | Impact | Relevant Rule / Requirement |
|---|---|---|---|
| **RD-01** | **Chapter State Reset to 531 on Refresh (Race Condition)**: When refreshing a URL like `?chapter=chapter_538`, `selectedChapterIdx` is initialized to `0`. Before `fetchChapterData` resolves and parses `window.location.search`, the sync effect runs `window.history.replaceState` with chapter index 0 (`chapter_531`), wiping the query parameter and resetting the chapter. | Critical | Acceptance Criteria ("Reader URL routing and localStorage persistence keep selected chapter on page refresh (no reset to 531)") |
| **RD-02** | **Missing Prominent «Скачать главу (ZIP)» in Header**: The reader header has no button to download the chapter release package. | High | R4 & R6 ("Prominent «Скачать главу (ZIP)» button in reader top bar") |
| **RD-03** | **Missing Burger Navigation Drawer**: The reader only has inline horizontal header buttons; it lacks a burger menu toggle (`☰`) with an overlay sidebar for navigating chapters, switching modes, and accessing settings. | Medium | R6 ("Burger navigation bar with catalog return, chapter dropdown selector...") |
| **RD-04** | **Unwrapped Params Usage in Client Component**: Line 26 uses `React.use(params)` with `{ params: Promise<{ manga: string }> }`, which can cause hydration or timing quirks during direct navigation in Next.js 15/16. Using `useParams()` or standard Props pattern is safer. | Low | Code Hygiene |
| **RD-05** | **Fallback Page Image Loading Errors**: In single mode, if `images[currentSinglePageIdx]` is empty or index is out of bounds during chapter transition, a broken image icon briefly flashes. | Low | UX |

---

### 3.3 Catalog / Landing Page (`src/app/page.tsx`)

#### Implemented Features:
- Dynamic chapter grid loaded from `/manga/chapters_index.json` with fallback to chapters 531–542.
- Hero banner with CTA buttons («📖 Читать с Главы 531 →» and «🔥 Свежая Глава 542»).
- Manga showcase card with tags, version pills (`RAW (v1)`, `Клининг (v2)`, `Перевод (v3)`), and cover image error fallback.
- Features section detailing the 3 translation & cleaning layers.
- Link to `/studio` in header.

#### Deficiencies & Defect Log:
- Static cover image hardcodes `v3/page_001.webp` with `v1/page_001.webp` fallback; does not link to studio quick launch.
- No direct batch download action for all chapters on the catalog page.

---

### 3.4 API Routes & Backend Integration

#### 1. `src/app/api/studio/mangas/route.ts` (CRITICAL BUG)
```typescript
// Current buggy code (lines 9-13):
const data = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
const mangas = Object.keys(data).map(m => ({
  name: m,
  chapters: data[m].chapters.map((c: any) => c.number)
}));
```
**Why it fails**: `chapters_index.json` has `{ "title": "...", "last_synced": ..., "mangas": { "The_Ultimate_of_All_Ages": { "chapters": [...] } } }`. Iterating `Object.keys(data)` reads `data["title"].chapters` which is `undefined`, throwing `TypeError: Cannot read properties of undefined (reading 'map')`.
**Fix**: Extract `data.mangas` and map `c.chapter || c.number`.

#### 2. `src/app/api/chapters/[manga]/route.ts`
- Scans both `public/manga` filesystem and fallback proxy to FastAPI `http://localhost:8000/api/chapters/[manga]`.
- Correctly parses `v1/v1_original`, `v2/v2_cleaned`, and `v3/v3_translated`.
- Working well.

#### 3. `src/app/api/chat/route.ts` & `AssistantChat.tsx`
- Connects to Ollama `http://localhost:11434/v1` with model `llama3`.
- Tool `deploy_manga_chapter` attempts to call `http://localhost:8000/api/deploy`.
- If Ollama or backend is not active, the assistant widget fails with an unhandled stream error.

---

## 4. Requirements Compliance Matrix

| Requirement | Requirement Description | Current Frontend Status | Verdict | Missing Items / Action Required |
|---|---|---|---|---|
| **R1** | Autonomous Turnkey Launch & Healthcheck | Next.js builds clean (`next build`). `package.json` scripts configured. | ✅ Compliant | Ensure dev/prod scripts match root `start_service.bat/.sh`. |
| **R3** | Live SSE Progress & Honest Diagnostics | Studio uses 1.5s polling. When offline, simulates fake 100% completion. | ❌ Non-Compliant | Implement real SSE streaming hook (`useSSE`), remove fake log simulation, surface honest error states. |
| **R4** | Production ZIP Packaging & Instant Downloads | Reader top bar has no download button. Studio download button 404s. | ❌ Non-Compliant | Add prominent «Скачать главу (ZIP)» in reader top bar and fix download link to `/manga/{manga}/{chapter}/{title}_Chapter_{num}_Russian.zip` or backend download route. |
| **R6.1** | Studio Drag-and-Drop Upload Zone | Implemented for files/ZIPs; missing folder directory drop. | ⚠️ Partial | Add folder drop support and format validation. |
| **R6.2** | Title & Chapter Range Batch Launcher | Only single chapter selection is available in Studio. | ❌ Non-Compliant | Add batch range input controls (`Start Chapter` – `End Chapter`, e.g. 531–542) and batch launch action. |
| **R6.3** | Live SSE Progress Visualizer | Polling with simulated completion fallback. | ❌ Non-Compliant | Build unified SSE progress component with 5-stage progress indicator. |
| **R6.4** | Chapter Library with Instant Download/Read | Studio lacks a full chapter library table/grid. | ❌ Non-Compliant | Add interactive Chapter Library grid with chapter stats, download ZIP buttons, and reader links. |
| **R6.5** | Reader Burger Navigation Bar | Reader only has basic top bar without burger drawer. | ❌ Non-Compliant | Add responsive burger menu with slide-out sidebar for chapter index and reader controls. |
| **R6.6** | Reader Catalog Return & Chapter Dropdown | Present in reader header. | ✅ Compliant | Refine styling and integrate into burger drawer for mobile. |
| **R6.7** | Reader Keyboard Navigation (A/D, Arrows, 1/2/3) | Fully implemented with input element guard. | ✅ Compliant | Works as specified. |
| **R6.8** | Webtoon vs Paginated Mode Toggle | Implemented (`📜 Лента` vs `📄 Постранично`). | ✅ Compliant | Fully functional. |
| **R6.9** | Multi-Layer Switch (1 RAW / 2 Clean / 3 RUS) | Implemented with hotkeys and visual pills. | ✅ Compliant | Fully functional. |
| **R6.10** | Reader Prominent «Скачать главу (ZIP)» Button | Missing from reader header. | ❌ Non-Compliant | Add prominent green/blue download button in reader top bar. |
| **R6.11** | Removal of Defunct Auto-Translate Button | No defunct button present. | ✅ Compliant | Verified. |
| **R6.12** | URL Query & LocalStorage State Persistence | Buggy race condition resets chapter to 531 on refresh. | ❌ Non-Compliant | Fix state initialization and URL sync order to prevent reset on refresh. |

---

## 5. Architectural Recommendations & Fix Plan

### 5.1 Reader Overhaul Plan (`src/app/reader/[manga]/page.tsx`)
1. **Fix URL & LocalStorage Initialization**:
   - Initialize `selectedChapterIdx` by immediately reading `window.location.search` or `localStorage` during initial state setup or guard the `history.replaceState` effect with an `isInitialized` flag so it only runs *after* the initial chapter has been identified and loaded.
2. **Add Prominent «Скачать главу (ZIP)» Button in Top Bar**:
   - Add a high-visibility download button in `.headerRight` / `.headerLeft` linking to `/manga/${cleanManga}/chapter_${currentChapter.number}/${cleanManga}_Chapter_${currentChapter.number}_Russian.zip` with fallback to `http://localhost:8000/api/studio/download/${cleanManga}/chapter_${currentChapter.number}/v3_translated`.
3. **Add Burger Navigation Drawer**:
   - Add a `☰` burger button in the header that slides open a side drawer showing:
     - Title overview and total chapter count.
     - Direct jump list to all chapters with completion badges.
     - Reading mode switcher and width presets.
     - Hotkey quick cheat-sheet (`A`/`D`, `1`/`2`/`3`, `←`/`→`).
     - «← В каталог» navigation link.

### 5.2 Studio Dashboard Overhaul Plan (`src/app/studio/page.tsx`)
1. **Add Batch Range Launcher**:
   - Add a mode switch: `Single Chapter` vs `Batch Range (от N до M)`.
   - Inputs for `start_chapter` (e.g. `531`) and `end_chapter` (e.g. `542`).
   - Button «🚀 Запустить пакетный перевод глав [531–542]».
2. **Add Chapter Library Table / Grid**:
   - Render a card grid or data table listing all chapters (531 to 542).
   - Display columns: Chapter Number, Page Count, Status (`v1 RAW`, `v2 Clean`, `v3 РУС`), Actions («📖 Читать», «📥 Скачать .ZIP»).
3. **Integrate Honest Real-Time Diagnostics & SSE Hook**:
   - Connect to `/api/pipeline/status` or SSE endpoint.
   - Remove fake simulation fallback on error; show actual server status or retry banner.
4. **Fix `/api/studio/mangas/route.ts`**:
   - Correctly parse `data.mangas` from `chapters_index.json`.

---

## 6. Verification Method

To verify all findings and fixes:
1. **TypeScript Check**: `cd frontend && npx tsc --noEmit` (must exit 0 with 0 errors).
2. **Production Build**: `cd frontend && npm run build` (must complete successfully).
3. **URL Persistence Test**: Navigate to `http://localhost:3000/reader/The_Ultimate_of_All_Ages?chapter=chapter_538` and hit `F5` / Refresh. The page must stay on Chapter 538 and not reset to 531.
4. **ZIP Download Test**: Click «Скачать главу (ZIP)» in the reader header and verify that `The_Ultimate_of_All_Ages_Chapter_XXX_Russian.zip` downloads immediately.
5. **Studio Batch & Library Test**: Verify `/studio` displays the batch launcher and the full interactive chapter list.
