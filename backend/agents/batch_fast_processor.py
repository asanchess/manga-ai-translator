# -*- coding: utf-8 -*-
import os
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection

def run_fast_chapter(chapter_dir: str):
    t_start = time.time()
    orig_dir = os.path.join(chapter_dir, "v1_original")
    clean_dir = os.path.join(chapter_dir, "v2_cleaned")
    trans_dir = os.path.join(chapter_dir, "v3_translated")
    
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(trans_dir, exist_ok=True)
    
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg'))])
    total_pages = len(pages)
    print(f"FAST SCANLATION PIPELINE: Processing {total_pages} pages in {chapter_dir}...", flush=True)
    
    results = []
    for idx, page in enumerate(pages, start=1):
        t0 = time.time()
        orig_p = os.path.join(orig_dir, page)
        clean_p = os.path.join(clean_dir, page)
        trans_p = os.path.join(trans_dir, page)
        
        # 1. OCR (cached / fast)
        clusters = extract_text_and_bubbles(orig_p, use_cache=True)
        
        # 2. Inpainting / cleaning
        process_page_cleaning(orig_p, clean_p, clusters)
        
        # 3. Translation & Typesetting
        process_page_translation(clean_p, trans_p, clusters)
        
        # 4. QA check
        qa = run_qa_inspection(orig_p, clean_p, trans_p, clusters)
        dt = time.time() - t0
        print(f"[{idx:02d}/{total_pages:02d}] {page} -> QA: {qa.get('qa_grade', 'Passed')} (Clusters: {qa.get('total_clusters', 0)}) in {dt:.2f}s", flush=True)
        results.append(qa)
        
    total_dt = time.time() - t_start
    print(f"CHAPTER 531 COMPLETED IN {total_dt:.2f} SECONDS with {len(results)} pages verified!", flush=True)

if __name__ == "__main__":
    chapter_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531"
    run_fast_chapter(chapter_path)
