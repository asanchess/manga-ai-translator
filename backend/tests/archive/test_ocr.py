import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import easyocr
import cv2

print('Initializing EasyOCR Reader...')
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

test_img_path = r'c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp'
if os.path.exists(test_img_path):
    img = cv2.imread(test_img_path)
    print('Testing OCR on page 2 (height, width):', img.shape)
    
    # Run OCR on top 3000 pixels slice to test
    slice_img = img[0:3000, :]
    results = reader.readtext(slice_img)
    print(f'Detected {len(results)} text blocks in top slice:')
    for bbox, text, prob in results:
        if prob > 0.2:
            print(f'  - [{prob:.2f}] "{text}" at bbox: {bbox}')
