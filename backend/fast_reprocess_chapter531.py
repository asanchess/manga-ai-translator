# -*- coding: utf-8 -*-
import sys
import os
import torch
torch.set_num_threads(8)

import cv2
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

def run_fast_chapter_531():
    base_dir = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531")
    orig_dir = os.path.join(base_dir, "v1_original")
    clean_dir = os.path.join(base_dir, "v2_cleaned")
    trans_dir = os.path.join(base_dir, "v3_translated")
    
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith('.webp')])
    print(f"Reprocessing {len(pages)} pages of Chapter 531...")
    
    for idx, p in enumerate(pages):
        print(f"\n[Page {idx+1}/{len(pages)}: {p}]")
        orig_p = os.path.join(orig_dir, p)
        clean_p = os.path.join(clean_dir, p)
        trans_p = os.path.join(trans_dir, p)
        
        # 1. OCR (force recalculate with Containment NMS)
        clusters = extract_text_and_bubbles(orig_p, use_cache=False)
        print(f"  Extracted {len(clusters)} deduplicated clusters.")
        
        # 2. Seamless Cleaning
        process_page_cleaning(orig_p, clean_p, clusters)
        
        # 3. Translation & Typesetting
        process_page_translation(clean_p, trans_p, clusters)
        print(f"  ✓ {p} completed cleanly!")

if __name__ == "__main__":
    run_fast_chapter_531()
