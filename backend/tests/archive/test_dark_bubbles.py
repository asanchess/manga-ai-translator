# -*- coding: utf-8 -*-
import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)
img = cv2.imread('data/manga/The_Ultimate_of_All_Ages/chapter_531/v1_original/page_004.webp')
top_crop = img[0:350, 0:img.shape[1]]

results = reader.readtext(top_crop, paragraph=False)
print("=== TOP CROP DETECTIONS ===")
for r in results:
    bbox, text, conf = r
    print(f"Conf {conf:.2f} | BBox: {bbox} | Text: '{text}'")
