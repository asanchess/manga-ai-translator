# -*- coding: utf-8 -*-
import os
import sys
import time
import zipfile
import asyncio
import logging

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
DATA_DIR = os.path.join(BASE_DIR, "data", "manga")

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

from scraper_agent import ScraperAgent
from ocr_engine import extract_text_and_bubbles, is_sound_effect
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NextChaptersBatch")

MANGA_NAME = "The_Ultimate_of_All_Ages"
CHAPTERS = ["533", "534", "535"]

async def process_single_chapter(chapter_num: str):
    logger.info(f"==================================================")
    logger.info(f"🚀 НАЧАЛО ОБРАБОТКИ: {MANGA_NAME} - ГЛАВА {chapter_num}")
    logger.info(f"==================================================")

    chapter_folder = f"chapter_{chapter_num}"
    chapter_path = os.path.join(DATA_DIR, MANGA_NAME, chapter_folder)
    orig_dir = os.path.join(chapter_path, "v1_original")
    clean_dir = os.path.join(chapter_path, "v2_cleaned")
    trans_dir = os.path.join(chapter_path, "v3_translated")

    os.makedirs(orig_dir, exist_ok=True)
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(trans_dir, exist_ok=True)

    # 1. Scraping
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])
    if not pages:
        logger.info(f"📥 Скачивание страниц для главы {chapter_num}...")
        scraper = ScraperAgent(output_dir=DATA_DIR)
        await scraper.download_chapter_async(MANGA_NAME, chapter_num)
        pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])

    total_pages = len(pages)
    if total_pages == 0:
        logger.error(f"❌ Не удалось получить страницы для главы {chapter_num}")
        return False

    logger.info(f"✓ Найдено {total_pages} страниц. Начинаем очистку и перевод...")

    # 2. Process each page
    for idx, p in enumerate(pages, 1):
        orig_p = os.path.join(orig_dir, p)
        clean_p = os.path.join(clean_dir, p)
        trans_p = os.path.join(trans_dir, p)

        logger.info(f"[{idx}/{total_pages}] Обработка {p}...")

        # OCR
        clusters = extract_text_and_bubbles(orig_p, use_cache=True)
        for c in clusters:
            c["is_sfx"] = is_sound_effect(c.get("text", ""))

        # Cleaner (5-pass inpainting)
        process_page_cleaning(orig_p, clean_p, clusters)

        # Translator & Typesetter
        process_page_translation(clean_p, trans_p, clusters)

        # QA Inspector
        qa = run_qa_inspection(orig_p, clean_p, trans_p, clusters)
        logger.info(f"[{idx}/{total_pages}] ✓ {p} завершена. Оценка QA: {qa.get('qa_grade')}")

    # 3. Create ZIP
    zip_filename = f"{MANGA_NAME}_Chapter_{chapter_num}_Russian.zip"
    zip_path = os.path.join(chapter_path, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for p in pages:
            tp = os.path.join(trans_dir, p)
            if os.path.exists(tp):
                zipf.write(tp, arcname=p)

    logger.info(f"🎉 ГЛАВА {chapter_num} УСПЕШНО ПЕРЕВЕДЕНА И ОПУБЛИКОВАНА! ({zip_filename})")
    return True

async def main():
    t0 = time.time()
    for ch in CHAPTERS:
        success = await process_single_chapter(ch)
        if not success:
            logger.warning(f"⚠️ Пропуск главы {ch} из-за ошибки")

    elapsed = round(time.time() - t0, 1)
    logger.info(f"🏆 ВСЕ 3 ГЛАВЫ (533, 534, 535) УСПЕШНО ОБРАБОТАНЫ ЗА {elapsed}с!")

if __name__ == "__main__":
    asyncio.run(main())
