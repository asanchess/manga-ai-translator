# Handoff Report — Milestone M1: Layer Isolation & Programmatic Anti-Patch Guard

**Author**: teamwork_preview_worker_m1  
**Milestone**: M1 (Layer Isolation & Programmatic Anti-Patch Guard)  
**Date**: 2026-08-22  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

- **Stray Directories in Storage**: `frontend/public/manga/` contained stray root directories (`v2/`, `v2_cleaned/`, `v3/`, `v3_translated/`) which caused `update_global_chapters_index()` in `backend/agents/manga_pipeline_service.py` (lines 64–119) to create phantom manga entries with 0 chapters in `chapters_index.json`.
- **Pipeline Implementation**:
  - `backend/agents/cleaner_agent.py` implements `clean_speech_bubble_seamless()` using per-pixel Otsu thresholding + color distance masking + `cv2.inpaint(img, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)`. Zero occurrences of `cv2.rectangle` in active backend code.
  - `backend/agents/manga_pipeline_service.py` lines 198–207 strictly passes `v1_original` to Cleaner to yield `v2_cleaned`, and passes `v2_cleaned` to Typesetter to yield `v3_translated`.
  - `backend/agents/translator_typesetter_agent.py` renders text via vector drawing (`ImageDraw.Draw`) directly onto the cleaned canvas without opaque box pasting.
- **Verification Commands & Results**:
  - `python backend/tests/anti_patch_guard.py --test-synthetic`:
    - Clean Inpainting: MinVar = 40.12, SSIM = 0.9995 -> `[PASS]`
    - Solid Rectangle Injection: Flagged 1 violation with variance = 0.0 -> `[PASS]`
    - Background Corruption Injection: Flagged background degradation = 2.99% -> `[PASS]`
  - `python backend/tests/anti_patch_guard.py --chapter chapter_531 --pages 2 8`:
    - `page_002.webp`: Check A MinVar = `37.84` (PASS), Check B SSIM = `0.99951` (0.049% degradation $\le 0.5\%$) -> `[PASS]`
    - `page_008.webp`: Check A MinVar = `39.98` (PASS), Check B SSIM = `0.99950` (0.050% degradation $\le 0.5\%$) -> `[PASS]`
  - `python backend/tests/test_typesetter_layout.py`:
    - Circular bubble boundary test: Max text pixel distance `61.72px` $\le 63.75\text{px}$ (85% safe limit), 0 pixels leaked outside circle -> `[PASS]`
    - Dark bubble auto-contrast test: `[PASS]`

---

## 2. Logic Chain

1. **Layer Separation Guarantee**: Because `cleaner_agent.py` uses per-pixel morphological glyph extraction and Telea inpainting instead of coarse bounding box fills, cleaned bubbles preserve natural color gradients and textures without sharp rectangular step artifacts.
2. **Solid Patch Mathematical Signature**: A rectangular solid fill (e.g. `cv2.rectangle`) generates zero variance ($\sigma^2 = 0.0$) across all pixels in the filled box. Inpainting samples from surrounding perimeter pixels, generating color gradients with variance $\sigma^2 > 1.0$. Check A calculates $\sigma^2$ both across the bounding box and across sliding $16\times 16$ sub-patches, reliably identifying flat fills.
3. **Background Invariance Guarantee**: Because `translator_typesetter_agent.py` draws text solely within the detected speech bubble coordinates, non-bubble pixels remain unaltered between `v1_original` and `v3_translated`. By applying an inverted bubble mask, Check B computes SSIM over non-bubble background pixels. Real pages show SSIM $\approx 0.9995$ (degradation $\approx 0.050\%$), safely satisfying the $\le 0.5\%$ degradation boundary ($SSIM \ge 0.995$).
4. **Index Cleanliness**: Deleting the stray directories from `frontend/public/manga/` and rebuilding `chapters_index.json` eliminated phantom manga keys (`v2`, `v2_cleaned`, `v3`, `v3_translated`), restoring correct library metadata for frontend navigation.

---

## 3. Caveats

- In chapters where pages do not have a pre-existing `.ocr.json` sidecar or `meta.json` entry, `anti_patch_guard.py` automatically falls back to `ocr_engine.py` or full-image comparison.
- Chapters 536–542 in `frontend/public/manga` currently have 0 pages populated (deficit to be addressed in Milestone M3 / M5).

---

## 4. Conclusion

Milestone M1 is **100% COMPLETE**:
1. `backend/tests/anti_patch_guard.py` is fully implemented and tested with CLI support, Check A (Solid Patch Detector), Check B (Background SSIM Difference), and per-page JSON reporting.
2. Layer isolation in `backend/agents/cleaner_agent.py`, `backend/agents/translator_typesetter_agent.py`, and `backend/agents/manga_pipeline_service.py` is verified with 0 `cv2.rectangle` occurrences and strict $v1 \to v2 \to v3$ sequence.
3. Stray directories in `frontend/public/manga/` are eradicated, and `chapters_index.json` is clean and accurate.
4. All quality validation tests on test chapters (Ch. 531 pages 2 and 8) and layout tests pass with zero integrity violations.

---

## 5. Verification Method

To independently reproduce and verify this work:
1. Run synthetic validation:
   ```powershell
   python backend/tests/anti_patch_guard.py --test-synthetic
   ```
2. Run test chapter verification on Chapter 531 pages 2 & 8:
   ```powershell
   python backend/tests/anti_patch_guard.py --manga The_Ultimate_of_All_Ages --chapter chapter_531 --pages 2 8
   ```
3. Run typesetter layout unit tests:
   ```powershell
   python backend/tests/test_typesetter_layout.py
   ```
4. Verify `frontend/public/manga/chapters_index.json` contains only valid manga titles:
   ```powershell
   python -c "import json; d = json.load(open('frontend/public/manga/chapters_index.json')); print(list(d['mangas'].keys()))"
   ```
