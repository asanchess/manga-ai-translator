import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

import cv2
from PIL import Image
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection

orig_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
clean_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v2_cleaned\page_002.webp"
trans_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_002.webp"

print("--- Running OCR on Page 2 ---")
clusters = extract_text_and_bubbles(orig_path)
for i, c in enumerate(clusters):
    print(f"Cluster {i+1}: text='{c['text']}', box={c['box']}, is_sfx={c['is_sfx']}")

print("--- Cleaning Page 2 ---")
process_page_cleaning(orig_path, clean_path, clusters)

print("--- Translating & Typesetting Page 2 ---")
process_page_translation(clean_path, trans_path, clusters)

print("--- QA Inspection ---")
qa = run_qa_inspection(orig_path, clean_path, trans_path, clusters)
print("QA Report:", qa)
