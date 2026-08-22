# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np

def generate_all_side_by_side_checks():
    base_dir = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531"
    v1_dir = os.path.join(base_dir, "v1_original")
    v2_dir = os.path.join(base_dir, "v2_cleaned")
    v3_dir = os.path.join(base_dir, "v3_translated")
    
    pages = sorted([f for f in os.listdir(orig_dir if 'orig_dir' in locals() else v1_dir) if f.endswith('.webp')])
    
    for p in pages:
        p1 = os.path.join(v1_dir, p)
        p2 = os.path.join(v2_dir, p)
        p3 = os.path.join(v3_dir, p)
        
        if not (os.path.exists(p1) and os.path.exists(p2) and os.path.exists(p3)):
            continue
            
        im1 = cv2.imread(p1)
        im2 = cv2.imread(p2)
        im3 = cv2.imread(p3)
        
        if im1 is None or im2 is None or im3 is None:
            continue
        
        h, w, _ = im1.shape
        crop_h = min(h, 1200)
        c1 = im1[0:crop_h, 0:w]
        c2 = im2[0:crop_h, 0:w]
        c3 = im3[0:crop_h, 0:w]
        
        cv2.putText(c1, "1. ORIGINAL", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.putText(c2, "2. CLEANED (5-PASS)", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(c3, "3. TRANSLATED (RUS)", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 100, 0), 3)
        
        combined = np.hstack([c1, c2, c3])
        out_crop = os.path.join(base_dir, f"sample_check_{p}.png")
        cv2.imwrite(out_crop, combined)
        print(f"Generated side-by-side check: {out_crop}")

if __name__ == "__main__":
    generate_all_side_by_side_checks()
