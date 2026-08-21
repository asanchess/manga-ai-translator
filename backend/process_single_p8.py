# -*- coding: utf-8 -*-
import sys
import os
import torch
torch.set_num_threads(8)

import cv2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

orig_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v1_original", "page_008.webp")
clean_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v2_cleaned", "page_008.webp")
trans_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_531", "v3_translated", "page_008.webp")

print("1. Extracting OCR clusters for page_008 with Containment NMS...")
clusters = extract_text_and_bubbles(orig_p, use_cache=False)
for idx, c in enumerate(clusters):
    print(f"  Bubble [{idx+1}] at {c['box']}: '{c['text']}'")

print("2. Seamless cleaning...")
process_page_cleaning(orig_p, clean_p, clusters)

print("3. Typesetting with single-pass centered text...")
process_page_translation(clean_p, trans_p, clusters)

# Export comparison crops of the character panel
trans_img = cv2.imread(trans_p)
if trans_img is not None:
    # Character pointing finger is around y=5000:7200
    crop = trans_img[5000:7200, :]
    cv2.imwrite(os.path.join(os.path.dirname(__file__), "eval_p8_character_panel.png"), crop)
    print("Exported eval_p8_character_panel.png!")
