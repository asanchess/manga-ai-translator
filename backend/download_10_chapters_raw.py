# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import logging

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from scraper_agent import ScraperAgent

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "manga")
MANGA_NAME = "The_Ultimate_of_All_Ages"
CHAPTERS = [str(i) for i in range(533, 543)] # 533 to 542 (10 chapters)

async def download_all():
    scraper = ScraperAgent(output_dir=DATA_DIR)
    for ch in CHAPTERS:
        orig_dir = os.path.join(DATA_DIR, MANGA_NAME, f"chapter_{ch}", "v1_original")
        os.makedirs(orig_dir, exist_ok=True)
        pages = [f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')]
        if len(pages) >= 5:
            print(f"✓ Глава {ch} уже скачана ({len(pages)} страниц)", flush=True)
            continue
            
        print(f"📥 Скачивание главы {ch}...", flush=True)
        res = await scraper.download_chapter_async(MANGA_NAME, ch)
        downloaded = [f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')]
        print(f"✓ Глава {ch} скачана: {len(downloaded)} страниц", flush=True)

if __name__ == "__main__":
    asyncio.run(download_all())
