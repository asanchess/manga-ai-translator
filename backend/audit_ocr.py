import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import easyocr
import cv2

reader = easyocr.Reader(['en'], gpu=False, verbose=False)
base = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original"

for i in range(1, 13):
    fname = f"page_{i:03d}.webp"
    fpath = os.path.join(base, fname)
    img = cv2.imread(fpath)
    h, w, _ = img.shape
    
    # Run OCR on 2000px slices
    found = []
    for y in range(0, h, 1200):
        y_end = min(y + 1400, h)
        res = reader.readtext(img[y:y_end, :], paragraph=False, text_threshold=0.2, low_text=0.2)
        for bbox, text, prob in res:
            if len(text.strip()) > 1:
                found.append((f"y={int(bbox[0][1]+y)}", text, f"{prob:.2f}"))
    print(f"\n=== {fname} ({w}x{h}) - Raw OCR items found: {len(found)} ===")
    for item in found[:10]:
        print(" ", item)
