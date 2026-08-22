# -*- coding: utf-8 -*-
import sys
import os
import cv2
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

def evaluate_page(chapter_num, page_name):
    print(f"\n==========================================")
    print(f"EVALUATING: Chapter {chapter_num} - {page_name}")
    print(f"==========================================")
    
    base_dir = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", f"chapter_{chapter_num}")
    orig_p = os.path.join(base_dir, "v1_original", page_name)
    clean_p = os.path.join(base_dir, "v2_cleaned", page_name)
    trans_p = os.path.join(base_dir, "v3_translated", page_name)
    
    os.makedirs(os.path.dirname(clean_p), exist_ok=True)
    os.makedirs(os.path.dirname(trans_p), exist_ok=True)
    
    # 1. OCR
    clusters = extract_text_and_bubbles(orig_p, use_cache=False)
    print(f"1. OCR Detected {len(clusters)} clusters/bubbles:")
    for i, c in enumerate(clusters):
        print(f"   [{i+1}] Box={c['box']} Dark={c.get('is_dark')} SFX={c.get('is_sfx')} Text=\"{c['text']}\"")
        
    # 2. Cleaning
    process_page_cleaning(orig_p, clean_p, clusters)
    print("2. Seamless Cleaning applied.")
    
    # 3. Translation & Typesetting
    process_page_translation(clean_p, trans_p, clusters)
    print("3. Translation & Typesetting applied.")
    
    # 4. Crop every bubble from Original, Cleaned, and Translated for inspection
    orig_img = cv2.imread(orig_p)
    clean_img = cv2.imread(clean_p)
    trans_img = cv2.imread(trans_p)
    
    h_img, w_img = orig_img.shape[:2]
    crop_dir = os.path.join(os.path.dirname(__file__), "eval_crops", f"ch{chapter_num}_{page_name.split('.')[0]}")
    os.makedirs(crop_dir, exist_ok=True)
    
    eval_report = []
    for i, c in enumerate(clusters):
        x, y, w, h = c["box"]
        pad = 25
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_img, x + w + pad)
        y2 = min(h_img, y + h + pad)
        
        orig_crop = orig_img[y1:y2, x1:x2]
        clean_crop = clean_img[y1:y2, x1:x2]
        trans_crop = trans_img[y1:y2, x1:x2]
        
        o_path = os.path.join(crop_dir, f"bubble_{i+1}_orig.png")
        c_path = os.path.join(crop_dir, f"bubble_{i+1}_clean.png")
        t_path = os.path.join(crop_dir, f"bubble_{i+1}_trans.png")
        
        cv2.imwrite(o_path, orig_crop)
        cv2.imwrite(c_path, clean_crop)
        cv2.imwrite(t_path, trans_crop)
        
        eval_report.append({
            "index": i + 1,
            "box": c["box"],
            "orig_text": c["text"],
            "paths": {"orig": o_path, "clean": c_path, "trans": t_path}
        })
        
    print(f"4. Exported {len(eval_report)} bubble crops to {crop_dir}")
    return eval_report

if __name__ == "__main__":
    r1 = evaluate_page("533", "page_001.webp")
    r2 = evaluate_page("533", "page_002.webp")
