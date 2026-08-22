import os
import sys
import logging

sys.path.insert(0, os.path.abspath('backend'))
from agents.scraper_agent import ScraperAgent
from agents.manga_pipeline_service import MangaPipelineService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BatchOngoing")

def run_batch():
    manga_name = "The_Ultimate_of_All_Ages"
    start_chapter = 531
    max_chapters_to_process = 3 # Limiting to 3 chapters per batch run to prevent CPU overheating
    
    scraper = ScraperAgent(output_dir="backend/data/manga")
    
    processed_count = 0
    current_chapter = start_chapter
    
    while processed_count < max_chapters_to_process:
        chapter_str = str(current_chapter)
        logger.info(f"=== Checking Chapter {chapter_str} ===")
        
        # Idempotency check: check if v3 directory exists and has files in frontend
        frontend_v3_dir = os.path.abspath(f"frontend/public/manga/{manga_name}/chapter_{chapter_str}/v3")
        if os.path.exists(frontend_v3_dir) and len(os.listdir(frontend_v3_dir)) >= 5:
            logger.info(f"Chapter {chapter_str} already exists in {frontend_v3_dir}. Skipping.")
            current_chapter += 1
            continue
            
        # Download new chapter
        logger.info(f"Downloading Chapter {chapter_str}...")
        chapter_dir = scraper.download_chapter(manga_name, chapter_str)
        
        if not chapter_dir or not os.path.exists(chapter_dir):
            logger.info(f"Could not download chapter {chapter_str}. Reached the latest ongoing!")
            break
            
        pages = [f for f in os.listdir(chapter_dir) if f.endswith(".webp") or f.endswith(".jpg")]
        if not pages:
            logger.info(f"No pages found for chapter {chapter_str}. Reached the latest ongoing!")
            break
            
        logger.info(f"Downloaded {len(pages)} pages for Chapter {chapter_str}. Starting processing pipeline...")
        
        # Run pipeline
        try:
            MangaPipelineService.process_chapter(chapter_dir, manga_name, current_chapter)
            logger.info(f"Successfully processed chapter {chapter_str}.")
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing chapter {chapter_str}: {e}")
            break
            
        current_chapter += 1

    logger.info(f"Batch processing complete. Processed {processed_count} new chapters.")

if __name__ == "__main__":
    run_batch()
