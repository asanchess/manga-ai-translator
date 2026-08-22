# -*- coding: utf-8 -*-
"""
M3 Batch Runner & Full Repair Script.
Runs chapter integrity checker, resolves page deficits for Ch. 537 & 538,
processes all chapters (531 to 542) with ModelInferenceManager,
generates v3.0.0 manifests, .zip archives, and syncs frontend public directory.
"""
import os
import sys
import time
import json
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from chapter_integrity_checker import ChapterIntegrityChecker
from model_inference_manager import ModelInferenceManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] M3Runner: %(message)s")
logger = logging.getLogger("M3Runner")


def main():
    logger.info("=== Starting Milestone M3 Processing & Chapter Repair Pipeline ===")
    t_start = time.time()

    checker = ChapterIntegrityChecker()
    manga_title = "The_Ultimate_of_All_Ages"
    manga_dir = os.path.join(checker.data_root, manga_title)

    # 1. First audit existing state
    logger.info("--- Phase 1: Pre-Audit of Chapters 531 to 542 ---")
    initial_audit = checker.audit_all_chapters(manga_title=manga_title)
    for ch in initial_audit.get("chapters", []):
        logger.info(f"Chapter {ch['chapter']}: v1={ch['v1_count']}, v2={ch['v2_count']}, v3={ch['v3_count']}, status={ch['status']}")

    # 2. Deficit Resolution: ensure >= 8 pages in v1_original for all chapters
    logger.info("--- Phase 2: Resolving Page Deficits (< 8 pages) ---")
    for ch_num in range(531, 543):
        ch_name = f"chapter_{ch_num}"
        ch_dir = os.path.join(manga_dir, ch_name)
        os.makedirs(ch_dir, exist_ok=True)
        count = checker.resolve_chapter_deficit(ch_dir, manga_title=manga_title, min_pages=8)
        logger.info(f"{ch_name} v1 page count: {count}")

    # 3. Model Inference Pipeline: Process all chapters (531 to 542)
    logger.info("--- Phase 3: High-Speed ML Inference on All Chapters (531 to 542) ---")
    mgr = ModelInferenceManager.get_instance()

    for ch_num in range(531, 543):
        ch_name = f"chapter_{ch_num}"
        ch_dir = os.path.join(manga_dir, ch_name)
        v1_dir = os.path.join(ch_dir, "v1_original")
        v2_dir = os.path.join(ch_dir, "v2_cleaned")
        v3_dir = os.path.join(ch_dir, "v3_translated")

        v1_files = sorted([f for f in os.listdir(v1_dir) if f.lower().endswith((".webp", ".png", ".jpg", ".jpeg")) and not f.endswith(".ocr.json")])
        v3_files = sorted([f for f in os.listdir(v3_dir) if f.lower().endswith((".webp", ".png", ".jpg", ".jpeg")) and not f.endswith(".ocr.json")]) if os.path.exists(v3_dir) else []

        # Process if missing v3 pages or if re-cleaning required
        needs_proc = (len(v3_files) != len(v1_files)) or (len(v1_files) == 0)

        if needs_proc:
            logger.info(f"Processing {ch_name} ({len(v1_files)} pages) via ModelInferenceManager...")
            res = mgr.process_chapter_concurrent(
                input_dir=v1_dir,
                manga_title=manga_title,
                chapter_num=str(ch_num),
                output_root=checker.public_root,
                max_workers=4
            )
            logger.info(f"{ch_name} finished in {res['elapsed_seconds']}s ({res['pages_per_second']} p/s)")
        else:
            logger.info(f"{ch_name} already has {len(v3_files)} v3 pages. Skipping re-inference.")

        # 4. Generate Manifests & Zip Archives
        logger.info(f"Generating manifest v3.0.0 & zip archives for {ch_name}...")
        checker.generate_pipeline_manifest(ch_dir, manga_title=manga_title, chapter_num=str(ch_num))
        checker.create_chapter_zip(ch_dir, manga_title=manga_title, chapter_num=str(ch_num))

    # 5. Frontend Public Sync
    logger.info("--- Phase 4: Syncing to Frontend Public Directory ---")
    synced_count = checker.sync_to_frontend(manga_title=manga_title)
    logger.info(f"Synced {synced_count} chapters to {checker.public_root}.")

    # 6. Post-Audit
    logger.info("--- Phase 5: Final Comprehensive Audit ---")
    final_audit = checker.audit_all_chapters(manga_title=manga_title)
    logger.info(f"All Chapters Passed: {final_audit['all_passed']}, Total Translated Pages: {final_audit['total_translated_pages']}")

    elapsed = time.time() - t_start
    logger.info(f"=== Milestone M3 Pipeline Finished in {elapsed:.2f}s ===")
    return final_audit


if __name__ == "__main__":
    main()
