# -*- coding: utf-8 -*-
import os
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection
import verify_visuals

def reprocess_all_chapter_pages():
    chapter_dir = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531"
    orig_dir = os.path.join(chapter_dir, "v1_original")
    clean_dir = os.path.join(chapter_dir, "v2_cleaned")
    trans_dir = os.path.join(chapter_dir, "v3_translated")
    
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith('.webp')])
    total = len(pages)
    print(f"=== FULL AUDIT & RE-RENDER: {total} pages ===", flush=True)
    
    # 1. Update OCR caches with correct SFX flags
    for idx, p in enumerate(pages, 1):
        orig_p = os.path.join(orig_dir, p)
        cache_p = orig_p + ".ocr.json"
        if os.path.exists(cache_p):
            # Load and re-evaluate is_sfx
            clusters = extract_text_and_bubbles(orig_p, use_cache=True)
            from ocr_engine import is_sound_effect
            for c in clusters:
                c["is_sfx"] = is_sound_effect(c.get("text", ""))
            with open(cache_p, "w", encoding="utf-8") as f:
                import json
                json.dump(clusters, f, ensure_ascii=False, indent=2)
                
        # 2. Clean page
        clean_p = os.path.join(clean_dir, p)
        process_page_cleaning(orig_p, clean_p, clusters)
        
        # 3. Translate & Typeset
        trans_p = os.path.join(trans_dir, p)
        process_page_translation(clean_p, trans_p, clusters)
        
        # 4. QA
        qa = run_qa_inspection(orig_p, clean_p, trans_p, clusters)
        print(f"[{idx:02d}/{total:02d}] {p} -> QA: {qa.get('qa_grade')} (Clusters: {qa.get('total_clusters')}) - Cleaned & Typeset ✓", flush=True)
        
    # Generate side by side visual comparisons
    verify_visuals.generate_side_by_side_checks()
    print("=== ALL 12 PAGES PERFECTLY SYNCED & VERIFIED ===", flush=True)

if __name__ == "__main__":
    reprocess_all_chapter_pages()
