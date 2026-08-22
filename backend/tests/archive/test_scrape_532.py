# -*- coding: utf-8 -*-
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from scraper_agent import ScraperAgent

async def run_download():
    out_dir = os.path.join(os.path.dirname(__file__), "data", "manga")
    scraper = ScraperAgent(output_dir=out_dir)
    res = await scraper.download_chapter_async("The_Ultimate_of_All_Ages", "532")
    print(f"Downloaded chapter to: {res}")
    
    # List downloaded files
    if res and os.path.exists(res):
        files = sorted(os.listdir(res))
        print(f"Files ({len(files)}): {files}")

if __name__ == "__main__":
    asyncio.run(run_download())
