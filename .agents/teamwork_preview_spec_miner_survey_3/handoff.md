# 📋 Handoff Report: Test & Data Specifications
**Agent:** Test & Data Spec Miner  
**Directory:** `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_spec_miner_survey_3`  
**Handoff Type:** Hard (Complete)

---

## 1. Observation

1. **Test Suite Status & Structure:**
   - Existing automated suite: `backend/tests/verify_pipeline.py` (327 lines) tests OCR topological sorting, smart inpainting, LLM batch schema, and typesetting bounds.
   - Typesetter layout unit test: `backend/tests/test_typesetter_layout.py` (102 lines) enforces 85% safe bounds on circular and dark speech bubbles.
   - Historical anti-pattern observed in `backend/tests/archive/test_clean_p2.py:25`: `cv2.rectangle(img, ..., fill_col, -1)` which produced solid box defects.
   - `backend/tests/anti_patch_guard.py` was not yet created; requirements specified for 2 checks: Check A (Solid Patch Detector) and Check B (Background SSIM Diff $\le 0.5\%$).

2. **Chapter Data & Layer Parity Audit:**
   - Audited 12 chapters in `backend/data/manga/The_Ultimate_of_All_Ages/`:
     - `chapter_531`: 12/12/12 (v1/v2/v3), ZIP present (13.8 MB), Complete.
     - `chapter_532`: 13/13/13, ZIP present, Complete.
     - `chapter_533`: 14/14/14, ZIP missing.
     - `chapter_534`: 11/11/11, ZIP missing.
     - `chapter_535`: 13/13/13, ZIP missing.
     - `chapter_536`: 14/0/0, RAW scraped.
     - `chapter_537`: 4/0/0, **Deficit (4 pages < 8 pages)**.
     - `chapter_538`: 5/0/0, **Deficit (5 pages < 8 pages)**.
     - `chapter_539`: 9/0/0, RAW scraped.
     - `chapter_540`: 8/8/8, ZIP present, Complete.
     - `chapter_541`: 12/0/0, RAW scraped.
     - `chapter_542`: 8/0/0, RAW scraped.

3. **Empirical Benchmark on Chapter 531 Pages 2 & 8:**
   - Page 2 ($800 \times 9880\text{px}$, 5 clusters): Background SSIM = $0.999450$, Degradation = $0.0550\%$ (**PASS**, threshold $\le 0.5\%$).
   - Page 8 ($800 \times 9835\text{px}$, 5 clusters): Background SSIM = $0.999459$, Degradation = $0.0541\%$ (**PASS**, threshold $\le 0.5\%$).
   - Solid rectangular patches detected: $0$.

4. **Persistent Glossary & Manifest Artifacts:**
   - `backend/data/manga/The_Ultimate_of_All_Ages/glossary.json` required for character names, factions, and cultivation terms.
   - `pipeline_manifest.json` schema v3.0.0 required for chapter integrity and checksum verification.

---

## 2. Logic Chain

1. From `ORIGINAL_REQUEST.md` R1 and domain rules in `AGENTS.md`, solid rectangle fills (`cv2.rectangle`) must be permanently prohibited and programmatically blocked.
2. The Anti-Patch Guard requires two quantitative checks:
   - Check A: Color variance $\sigma^2 < 1.0$ within bounding boxes where $v1$ had texture $\sigma_{v1}^2 > 25.0$ indicates an artificial solid patch.
   - Check B: Background SSIM outside speech bubbles $\ge 0.995$ ensures zero pixel bleed outside text regions.
3. Our empirical tests on Ch. 531 p. 2 & p. 8 proved that per-pixel Telea inpainting achieves $0.055\%$ and $0.054\%$ degradation, easily satisfying the $\le 0.5\%$ specification.
4. From R2, dialogue topology requires sequential 1-based IDs and the coordinate sorting formula $\text{sort\_key} = \lfloor \frac{y_{\text{center}}}{50} \rfloor \times 10000 + x_{\text{center}}$, batch JSON translation, and horizontal chord equation $W(y) = 2 a \sqrt{1 - (y/b)^2}$ with $\le 85\%$ safe oval bounds.
5. From R3, chapters with page counts $< 8$ (Ch. 537 with 4 pages, Ch. 538 with 5 pages) must trigger scraper mirror rotation (MangaKatana, Comick, MangaDex).

---

## 3. Caveats

1. Chapters 537 and 538 currently have incomplete page counts (4 and 5 pages) from initial scrape attempts and require mirror rotation during batch processing.
2. Chapters 533, 534, and 535 have all 3 layers rendered (14/14/14, 11/11/11, 13/13/13) but are missing the corresponding `.zip` translation archives.
3. `glossary.json` and `anti_patch_guard.py` must be instantiated in their exact paths according to the specifications provided in `survey_specs.md`.

---

## 4. Conclusion

All specifications, mathematical formulas, acceptance criteria, data structures, and edge cases have been mined, empirically tested, and documented in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_spec_miner_survey_3\survey_specs.md`. The Lead Architect and Builder can immediately use these contracts to implement the v3.0 SOTA Enterprise pipeline and Next.js reader overhaul.

---

## 5. Verification Method

1. **Run Ch. 531 Benchmark Verification:**
   ```powershell
   python .agents\teamwork_preview_spec_miner_survey_3\probe_p2_p8.py
   ```
   *Expected output:* Background SSIM > 0.999, Degradation < 0.06%, 0 solid patches.

2. **Run Chapter Data & Layer Audit:**
   ```powershell
   python .agents\teamwork_preview_spec_miner_survey_3\probe_all_chapters.py
   ```
   *Expected output:* Full 12-chapter matrix matching Section 5 in `survey_specs.md`.

3. **Run Regression Verification Test Suite:**
   ```powershell
   python backend\tests\verify_pipeline.py
   ```
   *Expected output:* 5 PASSED / 0 FAILED.