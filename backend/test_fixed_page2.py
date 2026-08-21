# -*- coding: utf-8 -*-
import sys
import os
import cv2
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

img_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v1_original", "page_002.webp")
clean_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v2_cleaned", "page_002.webp")
trans_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v3_translated", "page_002.webp")

# 1. Extract clusters with new strict deduplication
clusters = extract_text_and_bubbles(img_p, use_cache=False)
print("=== NEW DEDUPLICATED CLUSTERS ===")
for i, c in enumerate(clusters):
    print(f"Bubble {i+1}: box={c['box']} dark={c.get('is_dark')} text=\"{c['text'][:40]}\"")

# 2. Clean with seamless inpainting
process_page_cleaning(img_p, clean_p, clusters)

# 3. Translate & Typeset
process_page_translation(clean_p, trans_p, clusters)
print("=== PAGE 2 REPROCESSED SUCCESSFULLY ===")
