import os
import asyncio
import logging
import urllib.request
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperAgent:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def download_chapter_async(self, manga_name: str, chapter_number: str):
        logger.info(f"--- [Scraper] Initiating Multi-Source Download: {manga_name} Chapter {chapter_number} ---")
        
        chapter_dir = os.path.join(self.output_dir, manga_name, f"chapter_{chapter_number}", "v1_original")
        os.makedirs(chapter_dir, exist_ok=True)
        
        # Clean previous dummy files if any
        for f in os.listdir(chapter_dir):
            if f.startswith("page_") and os.path.getsize(os.path.join(chapter_dir, f)) < 50000:
                try:
                    os.remove(os.path.join(chapter_dir, f))
                except Exception:
                    pass
                    
        sources = [
            f"https://theultimateofallages.com/manga/the-ultimate-of-all-ages-chapter-{chapter_number}/",
            f"https://manhuatop.org/manhua/the-ultimate-of-all-ages/chapter-{chapter_number}/",
            f"https://manhwatop.com/manga/the-ultimate-of-all-ages/chapter-{chapter_number}/",
            f"https://mangakatana.com/manga/the-ultimate-of-all-ages.24987/c{chapter_number}",
        ]
        
        downloaded_count = 0
        
        # Strategy 1: Fast direct CDN download if available
        try:
            logger.info("Attempting direct high-speed CDN scrape...")
            cdn_base = f"https://cdn.black-clover.org/file/leveling/the-ultimate-of-all-ages/chapter-{chapter_number}"
            for page_idx in range(1, 35):
                img_url = f"{cdn_base}/{page_idx}.webp"
                req = urllib.request.Request(
                    img_url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://theultimateofallages.com/'}
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        content = resp.read()
                        if len(content) > 10000:
                            out_path = os.path.join(chapter_dir, f"page_{page_idx:03d}.webp")
                            with open(out_path, 'wb') as out_f:
                                out_f.write(content)
                            downloaded_count += 1
                        else:
                            break
                except Exception:
                    break
            if downloaded_count > 0:
                logger.info(f"Direct CDN download succeeded: {downloaded_count} pages downloaded!")
                return chapter_dir
        except Exception as cdn_err:
            logger.warning(f"Direct CDN attempt error: {cdn_err}")

        # Strategy 2: Headless Playwright multi-site scraper
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            for source_url in sources:
                logger.info(f"Checking source: {source_url}")
                try:
                    resp = await page.goto(source_url, wait_until="domcontentloaded", timeout=25000)
                    if not resp or resp.status != 200:
                        logger.warning(f"Source {source_url} returned status {resp.status if resp else 'None'}")
                        continue
                        
                    # Scroll down to trigger lazy loading
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    await page.wait_for_timeout(1000)
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)
                    
                    img_elements = await page.query_selector_all("img")
                    img_urls = []
                    for el in img_elements:
                        src = await el.get_attribute("src") or await el.get_attribute("data-src") or await el.get_attribute("data-lazy-src")
                        if src and any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                            # Filter out icons / avatars
                            if not any(ignore in src.lower() for ignore in ["avatar", "logo", "icon", "banner", "coming_soon", "wp-content/themes"]):
                                img_urls.append(src)
                                
                    if len(img_urls) >= 3:
                        logger.info(f"Found {len(img_urls)} candidate manga pages on {source_url}")
                        for i, img_url in enumerate(img_urls):
                            try:
                                ext = ".webp" if ".webp" in img_url.lower() else ".jpg"
                                out_path = os.path.join(chapter_dir, f"page_{i+1:03d}{ext}")
                                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': source_url})
                                with urllib.request.urlopen(req, timeout=10) as r, open(out_path, 'wb') as f:
                                    f.write(r.read())
                                downloaded_count += 1
                            except Exception as dl_err:
                                logger.error(f"Failed to download image {img_url}: {dl_err}")
                        if downloaded_count > 0:
                            logger.info(f"Successfully scraped {downloaded_count} pages from {source_url}")
                            break
                except Exception as src_err:
                    logger.warning(f"Error scraping {source_url}: {src_err}")
                    
            await browser.close()
            
        logger.info(f"Total downloaded pages for Chapter {chapter_number}: {downloaded_count}")
        return chapter_dir

    def download_chapter(self, manga_name: str, chapter_number: str):
        return asyncio.run(self.download_chapter_async(manga_name, chapter_number))

if __name__ == "__main__":
    agent = ScraperAgent(output_dir="../data/manga")
    agent.download_chapter("The_Ultimate_of_All_Ages", "531")
