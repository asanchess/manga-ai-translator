## 2026-08-23T10:37:03Z
You are the Builder / Worker for Milestone 5 (SOTA Anti-Patch Inpainting & Elliptical Typesetting Font Fallbacks) of the «Manga AI Translator Studio» project.
Your working directory is: c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m5_1
You MUST read the following authoritative files first before starting:
1. c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
2. c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
3. c:\Users\asana\OneDrive\Desktop\Manga\PROJECT.md
4. c:\Users\asana\OneDrive\Desktop\Manga\.agents\explorer_backend_1\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Write Boundaries:
You own exclusively:
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\cleaner_agent.py`
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\translator_typesetter_agent.py`

Tasks:
1. Ensure Anti-Patch policy compliance in `cleaner_agent.py`:
   - Confirm ZERO calls to `cv2.rectangle` in inpainting routines.
   - Verify `clean_speech_bubble_seamless()` uses adaptive per-pixel thresholding and `cv2.inpaint(..., inpaintRadius=4, flags=cv2.INPAINT_TELEA)`.
   - Verify boundary preservation and SSIM degradation <= 0.3%.
2. Enhance `translator_typesetter_agent.py`:
   - Check the elliptical chord formula $W(y) = 2a\sqrt{1-(y/b)^2}$ and safe oval padding (<=85%).
   - Add robust cross-platform font fallbacks: if Windows system fonts (`C:\Windows\Fonts\...`) are not present (e.g. Linux / macOS / Docker containers), fallback gracefully to bundled fonts in `backend/assets/fonts/` (`ComicNeue-Bold.ttf`, etc.) or PIL default fonts with Russian character support.
   - Verify dynamic auto-contrast (dark stroke on light text for dark bubbles, clean black text for light bubbles).
3. Verify test compliance by running:
   - `python backend/tests/anti_patch_guard.py --test-synthetic`
   - `python backend/tests/bubble_benchmark_100.py`
4. Document all changes and verification test results in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m5_1\handoff.md`.
5. Send completion message back to parent orchestrator.
