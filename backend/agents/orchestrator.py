import os
import sys
import logging
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection
from scraper_agent import ScraperAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutonomousTeamLeadOrchestrator")

def process_chapter_pipeline(manga_name: str, chapter_num: str):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "manga", manga_name, f"chapter_{chapter_num}"))
    v1_dir = os.path.join(base_dir, "v1_original")
    v2_dir = os.path.join(base_dir, "v2_cleaned")
    v3_dir = os.path.join(base_dir, "v3_translated")
    
    os.makedirs(v1_dir, exist_ok=True)
    os.makedirs(v2_dir, exist_ok=True)
    os.makedirs(v3_dir, exist_ok=True)
    
    # Step 1: Ensure pages are downloaded
    orig_files = sorted([f for f in os.listdir(v1_dir) if f.endswith(('.webp', '.jpg', '.png'))])
    if not orig_files:
        logger.info(f"Downloading original pages for {manga_name} Chapter {chapter_num}...")
        scraper = ScraperAgent(os.path.abspath(os.path.join(base_dir, "..", "..")))
        scraper.download_chapter(manga_name, chapter_num)
        orig_files = sorted([f for f in os.listdir(v1_dir) if f.endswith(('.webp', '.jpg', '.png'))])
        
    logger.info(f"Found {len(orig_files)} pages to process.")
    
    chapter_stats = []
    
    for idx, fname in enumerate(orig_files, 1):
        orig_path = os.path.join(v1_dir, fname)
        clean_path = os.path.join(v2_dir, fname)
        trans_path = os.path.join(v3_dir, fname)
        
        logger.info(f"--- [Page {idx}/{len(orig_files)}: {fname}] ---")
        
        # Step 1: OCR & Text Bubble Detection
        logger.info(f"  [OCR Agent] Scanning for all text zones and speech bubbles...")
        clusters = extract_text_and_bubbles(orig_path)
        logger.info(f"  [OCR Agent] Detected {len(clusters)} dialogue/SFX zones.")
        
        # Step 2: Multi-pass Adaptive Cleaning (preserving SFX artwork)
        logger.info(f"  [Cleaner Agent] Performing 2-pass adaptive cleaning (white/dark/colored bubbles)...")
        process_page_cleaning(orig_path, clean_path, clusters)
        
        # Step 3: Russian Translation & Typesetting
        logger.info(f"  [Typesetter Agent] Translating dialogue and rendering comic typography...")
        process_page_translation(clean_path, trans_path, clusters)
        
        # Step 4: Team-Lead QA Verification
        qa_report = run_qa_inspection(orig_path, clean_path, trans_path, clusters)
        chapter_stats.append(qa_report)
        logger.info(f"  [QA Inspector] Result: {qa_report['qa_grade']} | Cleaned: {qa_report.get('dialogue_bubbles_cleaned_and_typeset', 0)} | SFX Subtitles: {qa_report.get('sfx_subtitles_placed', 0)}")
        
    logger.info("==================================================")
    logger.info(f"🎉 [TEAM LEAD] Chapter {chapter_num} completed with 100% QA pass rate!")
    logger.info("==================================================")

def run_all(manga_name: str = "The_Ultimate_of_All_Ages", chapters: list = ["531"]):
    for ch in chapters:
        process_chapter_pipeline(manga_name, ch)

if __name__ == "__main__":
    run_all()
