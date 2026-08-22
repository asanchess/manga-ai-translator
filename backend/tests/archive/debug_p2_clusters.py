import cv2
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles

img = cv2.imread(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp")
clusters = extract_text_and_bubbles(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp")

for i, c in enumerate(clusters):
    x, y, w, h = c["box"]
    crop = img[y:y+h, x:x+w]
    print(f"Cluster {i}: text={c['text']}, box={c['box']}, is_sfx={c.get('is_sfx')}")
