import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import easyocr
import cv2

reader = easyocr.Reader(['en'], gpu=False, verbose=False)
img = cv2.imread(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_003.webp")
h, w, _ = img.shape
print(f"Page 3 shape: {w}x{h}")

# Let's inspect the bottom section where 'YOUNG MASTER, BE CAREFUL!' is located (around y=5000-6000)
slice_img = img[4500:6000, :]
results = reader.readtext(slice_img, text_threshold=0.2, low_text=0.2, link_threshold=0.2)
print(f"Detections in slice [4500:6000]: {len(results)}")
for bbox, text, prob in results:
    print(f"  [{prob:.2f}] '{text}' at {bbox}")
