import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

import traceback
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection

base_dir = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531"
v1_dir = os.path.join(base_dir, "v1_original")
v2_dir = os.path.join(base_dir, "v2_cleaned")
v3_dir = os.path.join(base_dir, "v3_translated")

orig_files = sorted([f for f in os.listdir(v1_dir) if f.endswith(('.webp', '.jpg', '.png'))])

for fname in orig_files:
    orig_path = os.path.join(v1_dir, fname)
    clean_path = os.path.join(v2_dir, fname)
    trans_path = os.path.join(v3_dir, fname)
    
    print(f"\nProcessing {fname}...")
    try:
        clusters = extract_text_and_bubbles(orig_path)
        print(f"  Clusters found: {len(clusters)}")
        for c in clusters:
            print(f"    - text: '{c['text']}', box: {c['box']}, sfx: {c['is_sfx']}")
        
        c_res = process_page_cleaning(orig_path, clean_path, clusters)
        print(f"  Cleaned -> {clean_path} (exists={os.path.exists(clean_path)})")
        
        t_res = process_page_translation(clean_path, trans_path, clusters)
        print(f"  Translated -> {trans_path} (exists={os.path.exists(trans_path)})")
        
        qa = run_qa_inspection(orig_path, clean_path, trans_path, clusters)
        print(f"  QA: {qa['qa_grade']}")
    except Exception as e:
        print(f"  ERROR on {fname}: {e}")
        traceback.print_exc()
