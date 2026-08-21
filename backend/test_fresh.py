import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

import cv2
from PIL import Image
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

orig_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
clean_test = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\test_clean_002.webp"
trans_test = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\test_trans_002.webp"

clusters = extract_text_and_bubbles(orig_path)
print(f"Extracted {len(clusters)} clusters from fresh v1_original:")
for c in clusters:
    print(" ", c["text"], "box:", c["box"])

process_page_cleaning(orig_path, clean_test, clusters)
process_page_translation(clean_test, trans_test, clusters)

# Crop middle section and save
img = Image.open(trans_test)
crop = img.crop((0, 3800, img.width, 8800))
crop_out = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\fresh_test_crop.png"
crop.save(crop_out)
print("Saved fresh test crop:", crop_out)
