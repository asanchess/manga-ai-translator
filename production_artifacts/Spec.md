# Specification: Manga AI Translator v3.0 SOTA Enterprise Reconstruction

## 1. Architectural Blueprint
The Manga AI Translator v3.0 pipeline delivers high-fidelity end-to-end translation and reader UX:
- **Strict Layer Isolation**: `v1_original` (RAW) $\to$ `v2_cleaned` (Telea inpaint, 0 solid fills) $\to$ `v3_translated` (Pillow vector rendering on `v2_cleaned`).
- **Anti-Patch Quality Guard**: `backend/tests/anti_patch_guard.py` verifying $\sigma^2 \ge 1.0$ (no flat gray/white rectangles) and background structural similarity $\text{SSIM} \ge 0.995$ ($\le 0.5\%$ degradation).
- **Dialogue Topology & Glossary**: $y_{\text{center}} \times 10000 + x_{\text{center}}$ topological sorting, 1-based sequential integer IDs, batch JSON LLM translation, persistent `glossary.json` prompt injection.
- **Elliptical Typesetting**: Horizontal ellipse chord calculation $W(y) = 2a\sqrt{1-(y/b)^2}$, $\le 85\%$ safe oval bounds, binary search font scale ($38\to 12\text{px}$), Cyrillic TTF, auto-contrast.
- **ML Singleton & Integrity Checker**: `ModelInferenceManager` for weights caching, `ChapterIntegrityChecker` with mirror rotation for Ch. 537 & 538 ($\ge 8$ pages), `pipeline_manifest.json` v3.0.0, and `.zip` archives.
- **Next.js Reader Overhaul**: Multi-layer switching (1/2/3), keyboard navigation (A/D, ArrowLeft/Right), width presets (700, 900, 1200, 100%), Webtoon / Single-Page modes, dead UI removal, URL (`?chapter=chapter_XXX`) and `localStorage` persistence.

## 2. API & Data Contracts
### Chapter Directory Standard
```
backend/data/manga/{title}/
├── glossary.json
└── {chapter}/
    ├── v1_original/ (page_001.webp, ...)
    ├── v2_cleaned/ (page_001.webp, ...)
    ├── v3_translated/ (page_001.webp, ...)
    └── pipeline_manifest.json
```

### Manifest Schema (v3.0.0)
```json
{
  "version": "3.0.0",
  "manga": "The_Ultimate_of_All_Ages",
  "chapter": "chapter_531",
  "total_pages": 12,
  "layers": {
    "v1_original": {"page_count": 12, "sha256": "..."},
    "v2_cleaned": {"page_count": 12, "sha256": "..."},
    "v3_translated": {"page_count": 12, "sha256": "..."}
  },
  "quality_metrics": {
    "avg_background_ssim": 0.99945,
    "max_degradation_pct": 0.055,
    "solid_patches_detected": 0
  },
  "zip_archive": "The_Ultimate_of_All_Ages_chapter_531_v3.zip",
  "timestamp": "2026-08-22T17:45:00Z"
}
```

## 3. Milestones & Execution Plan
- **M1**: Layer Isolation, Directory Hygiene & Anti-Patch Guard Test Suite.
- **M2**: Persistent Glossary, Dialogue Topology Sorting & Elliptical Typesetting.
- **M3**: ML Inference Singleton, Chapter Integrity Checker, Mirror Rotation, Chapter Processing (531–542) & Manifests.
- **M4**: Next.js Web Reader Overhaul, Layer Hotkeys, Width Toggles, Single-Page Mode & Persistence.
- **M5**: E2E Verification Suite, Anti-Patch Guard Execution, `Ongoing_Sync_Report.md`, QA Report & Git Hygiene.
