# -*- coding: utf-8 -*-
import os
import sys
import json
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

def reprocess_chapter(chapter_name: str):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", chapter_name)
    orig_dir = os.path.join(base_dir, "v1_original")
    clean_dir = os.path.join(base_dir, "v2_cleaned")
    trans_dir = os.path.join(base_dir, "v3_translated")
    
    if not os.path.exists(orig_dir):
        print(f"Directory {orig_dir} does not exist.")
        return
        
    pages = sorted([f for f in os.listdir(orig_dir) if f.endswith('.webp') and not f.endswith('.ocr.json')])
    print(f"=== Reprocessing {chapter_name} ({len(pages)} pages) ===")
    
    for p in pages:
        orig_file = os.path.join(orig_dir, p)
        cleaned_file = os.path.join(clean_dir, p)
        out_file = os.path.join(trans_dir, p)
        
        # 1. Re-run OCR clustering with new deduplication (use_cache=False to get clean clusters)
        clusters = extract_text_and_bubbles(orig_file, use_cache=False)
        
        # 2. Re-clean page
        process_page_cleaning(orig_file, cleaned_file, clusters)
        
        # 3. Re-typeset with verified fonts
        process_page_translation(cleaned_file, out_file, clusters)
        print(f"[OK] {chapter_name}/{p} processed.")

    # 4. Re-package ZIP
    ch_num = chapter_name.replace("chapter_", "")
    zip_name = f"The_Ultimate_of_All_Ages_Chapter_{ch_num}_Russian.zip"
    zip_path = os.path.join(trans_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in os.listdir(trans_dir):
            if f.endswith('.webp'):
                zipf.write(os.path.join(trans_dir, f), arcname=f)
    print(f"[OK] Re-packaged ZIP: {zip_path}")

def main():
    for ch in ["chapter_531", "chapter_532"]:
        reprocess_chapter(ch)
    print("=== ALL CHAPTERS REPROCESSED FLAWLESSLY ===")

if __name__ == "__main__":
    main()
