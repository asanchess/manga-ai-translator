# -*- coding: utf-8 -*-
"""
Rebuild all chapters (531-542) with Manga AI Translator v4.0 SOTA Pipeline.
Uses:
- ComicBubbleDetector (separating bubbles from SFX, 0 noise stamps)
- ScanlationMemoryMiner (10-chapter entity memory injection)
- Live Google Gemini 2.5 Flash / Groq Qwen 3.6 SOTA translation
- High-fidelity Telea inpainting
- Elliptical Cyrillic typography
"""
import os
import sys
import time
import shutil
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scanlation_memory_miner import get_memory_miner
from chapter_integrity_checker import ChapterIntegrityChecker
from model_inference_manager import ModelInferenceManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] SOTARebuilder: %(message)s")
logger = logging.getLogger("SOTARebuilder")


def run_rebuild():
    manga_title = "The_Ultimate_of_All_Ages"
    logger.info(f"=== Starting SOTA v4.0 Translation Rebuild for '{manga_title}' ===")
    t0 = time.time()

    # 1. Mine memory graph from 10 chapters
    miner = get_memory_miner()
    miner.mine_manga_memory(manga_title, lookback_chapters=10)

    checker = ChapterIntegrityChecker()
    manga_dir = os.path.join(checker.data_root, manga_title)
    mgr = ModelInferenceManager.get_instance()

    total_chapters = 0
    total_pages = 0

    for ch_num in range(531, 543):
        ch_name = f"chapter_{ch_num}"
        ch_dir = os.path.join(manga_dir, ch_name)
        v1_dir = os.path.join(ch_dir, "v1_original")
        v2_dir = os.path.join(ch_dir, "v2_cleaned")
        v3_dir = os.path.join(ch_dir, "v3_translated")

        if not os.path.exists(v1_dir):
            continue

        # Clean old v2 and v3 to ensure pristine re-processing
        for d in (v2_dir, v3_dir):
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d, exist_ok=True)

        logger.info(f"\n--- Processing {ch_name} (SOTA v4.0 Pipeline) ---")
        res = mgr.process_chapter_concurrent(
            input_dir=v1_dir,
            manga_title=manga_title,
            chapter_num=str(ch_num),
            output_root=checker.public_root,
            max_workers=4
        )

        total_chapters += 1
        total_pages += res.get("pages_processed", 0)

        # Generate manifest and zip archive
        checker.generate_pipeline_manifest(ch_dir, manga_title=manga_title, chapter_num=str(ch_num))
        checker.create_chapter_zip(ch_dir, manga_title=manga_title, chapter_num=str(ch_num))

    # Sync to frontend public directory
    synced = checker.sync_to_frontend(manga_title=manga_title)
    elapsed = time.time() - t0

    logger.info(f"\n=======================================================")
    logger.info(f"SOTA v4.0 Rebuild Completed in {elapsed:.2f}s!")
    logger.info(f"Chapters Rebuilt: {total_chapters}, Pages: {total_pages}, Synced: {synced}")
    logger.info(f"=======================================================")


if __name__ == "__main__":
    run_rebuild()
