import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import easyocr
import cv2
import numpy as np

reader = easyocr.Reader(['en'], gpu=False, verbose=False)

def detect_manga_text(img_path):
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    print(f"Loaded image: {img_path} ({w}x{h})")
    
    # Process in vertical chunks to maximize OCR resolution and accuracy
    chunk_h = 1200
    overlap = 200
    all_detections = []
    
    y = 0
    while y < h:
        y_end = min(y + chunk_h, h)
        slice_img = img[y:y_end, :]
        results = reader.readtext(slice_img, paragraph=False, min_size=10, text_threshold=0.3, low_text=0.3)
        
        for bbox, text, prob in results:
            if prob > 0.2 and len(text.strip()) > 1:
                # adjust coordinates by y
                pts = [[int(pt[0]), int(pt[1] + y)] for pt in bbox]
                all_detections.append({
                    "bbox": pts,
                    "text": text.strip(),
                    "prob": prob,
                    "y_center": sum(pt[1] for pt in pts) / 4.0,
                    "x_center": sum(pt[0] for pt in pts) / 4.0
                })
        
        if y_end >= h:
            break
        y += (chunk_h - overlap)
        
    print(f"Total raw text items detected: {len(all_detections)}")
    for d in all_detections[:15]:
        print(f"  [{d['prob']:.2f}] (y={int(d['y_center'])}) \"{d['text']}\"")
        
test_img_path = r'c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp'
if os.path.exists(test_img_path):
    detect_manga_text(test_img_path)
