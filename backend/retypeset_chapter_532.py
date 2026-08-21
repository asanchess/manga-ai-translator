# -*- coding: utf-8 -*-
import os
import sys
import json
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

def reclean_and_retypeset():
    ch_dir = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_532")
    orig_dir = os.path.join(ch_dir, "v1_original")
    clean_dir = os.path.join(ch_dir, "v2_cleaned")
    trans_dir = os.path.join(ch_dir, "v3_translated")
    
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith('.webp') and not f.endswith('.ocr.json')])
    print(f"Re-cleaning and Re-typesetting {len(pages)} pages of Chapter 532...")
    
    for p in pages:
        orig_file = os.path.join(orig_dir, p)
        ocr_file = os.path.join(orig_dir, p + ".ocr.json")
        cleaned_file = os.path.join(clean_dir, p)
        out_file = os.path.join(trans_dir, p)
        
        if os.path.exists(ocr_file) and os.path.exists(orig_file):
            with open(ocr_file, "r", encoding="utf-8") as f:
                clusters = json.load(f)
            # Re-clean using updated 5-pass cleaner
            process_page_cleaning(orig_file, cleaned_file, clusters)
            # Re-typeset with Cyrillic Comic Sans font
            process_page_translation(cleaned_file, out_file, clusters)
            print(f"[OK] Re-processed {p} (clean + typeset).")

    # Re-package zip
    zip_name = "The_Ultimate_of_All_Ages_Chapter_532_Russian.zip"
    zip_path = os.path.join(trans_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in os.listdir(trans_dir):
            if f.endswith('.webp'):
                zipf.write(os.path.join(trans_dir, f), arcname=f)
    print(f"[OK] Re-packaged ZIP: {zip_path}")

if __name__ == "__main__":
    reclean_and_retypeset()
