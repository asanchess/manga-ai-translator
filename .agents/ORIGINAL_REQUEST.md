# Original User Request

## 2026-08-23T10:28:29Z

Build and package an end-to-end autonomous, turnkey software product «Manga AI Translator Studio» (FastAPI + Next.js + SOTA Pipeline v4.0 + AI/Human Dual Interface) that translates manga chapters completely autonomously with one-click web dashboard, CLI, smart multi-provider LLM cascade, live SSE progress tracking, zero-rectangle anti-patch inpainting, and an overhauled reader with instant ZIP downloads.

Working directory: c:/Users/asana/OneDrive/Desktop/Manga
Integrity mode: development

## Requirements

### R1. Autonomous Turnkey Launch & AI-Ready CLI
- Provide one-click startup scripts (start_service.bat for Windows and start_service.sh for Linux/macOS) that launch both FastAPI backend and Next.js frontend with automated healthchecks.
- Provide a unified CLI interface python backend/cli.py --title <title> --chapters <range> [--auto-deploy] enabling both human power users and Antigravity AI agents to process multi-chapter translation batches without chat overhead.

### R2. Zero-Config Invisible LLM Cascade Failover
- Securely read API credentials from local .env (Gemini, OpenRouter, Groq, DeepSeek) without exposing keys to the client browser.
- Automatically and transparently route batch translations through available SOTA providers (OpenRouter / Gemini 2.5 Flash / Groq Qwen 3.6 / Local Xianxia fallback) with automatic error recovery and zero English dialogue leaks.
- Inject 10-chapter terminology graph (glossary_memory.json / glossary.json) into all translation prompts.

### R3. Real-Time Pipeline Progress & Transparent Diagnostics
- Stream live real-time pipeline telemetry via Server-Sent Events (SSE) / WebSockets to the web dashboard ([Chapter 532] [Page 4/15] -> 2-Pass OCR -> Telea Inpaint -> Batch LLM -> Typeset).
- Report true status and honest error logs with automatic retries on network blips rather than false completion indicators.

### R4. Production ZIP Packaging & Instant Downloads
- Automatically generate high-fidelity Russian release packages {title}_Chapter_{num}_Russian.zip upon chapter completion.
- Expose direct download endpoints and prominent UI download buttons both on the dashboard and in the reader header.

### R5. SOTA Glyph Inpainting & Elliptical Typesetting
- Maintain strict Anti-Patch policy: zero rectangular fills (cv2.rectangle), per-pixel glyph inpainting (Telea / LaMa) with background preservation (SSIM degradation <= 0.3%).
- Restrict typesetting strictly to v2_cleaned layers using Russian TTF fonts (comicbd.ttf, segoeuib.ttf, arialbd.ttf) with elliptical chord word wrapping W(y) = 2a*sqrt(1-(y/b)^2) and dynamic auto-contrast.
- Maintain singleton model inference with execution speed <= 1-2 minutes per full chapter.

### R6. Overhauled Next.js Web Reader & Studio Dashboard
- Studio Dashboard: Drag-and-drop upload zone for ZIPs/raw folders, title & chapter range batch launcher, live SSE progress visualizer, and chapter library with instant download/read actions.
- Manga Reader Overhaul:
  - Burger navigation bar with catalog return, chapter dropdown selector, keyboard navigation (A/D and arrow keys), and vertical Webtoon vs paginated mode toggle.
  - Multi-layer switch (1 RAW / 2 Clean / 3 RUS).
  - Prominent «Скачать главу (ZIP)» button in reader top bar.
  - Remove defunct  auto-translate button from reader view.
  - Full chapter state persistence across URL query parameters (?chapter=chapter_XXX) and localStorage.

## Acceptance Criteria

### Automated Tests & Quality Guards
- [ ] python backend/tests/anti_patch_guard.py --all passes all 13 chapters with 0 violations and background SSIM >= 99.5%.
- [ ] python backend/tests/bubble_benchmark_100.py passes 100/100 bubble archetypes across all 7 categories with 0 art corruptions.
- [ ] python -m unittest discover -s backend/tests passes 18/18 unit tests.
- [ ] cd frontend && npx tsc --noEmit passes with 0 TypeScript compilation errors.

### Service, CLI & UI Integration
- [ ] python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532 executes completely and generates verified releases.
- [ ] start_service.bat and start_service.sh are generated and verified.
- [ ] Reader URL routing and localStorage persistence keep selected chapter on page refresh (no reset to 531).
- [ ] ZIP download API and UI buttons trigger download of {title}_Chapter_{num}_Russian.zip.
- [ ] All code committed and pushed to GitHub repository main branch.
