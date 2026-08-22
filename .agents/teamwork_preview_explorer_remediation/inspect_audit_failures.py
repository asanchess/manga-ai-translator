# -*- coding: utf-8 -*-
"""
Remediation Forensic Diagnostic Script
Inspects:
1. Ch. 533 page 7: Check A solid patch violation details
2. Ch. 540 page 4: Check B SSIM background degradation details
3. All chapters 531-542: Detailed layer inventory, dimensions, manifests, archives, and sync status
"""
import os
import sys
import json
import numpy as np
import cv2
from PIL import Image

PROJECT_ROOT = r"c:\Users\asana\OneDrive\Desktop\Manga"
BACKEND_DATA = os.path.join(PROJECT_ROOT, "backend", "data", "manga", "The_Ultimate_of_All_Ages")
FRONTEND_PUBLIC = os.path.join(PROJECT_ROOT, "frontend", "public", "manga", "The_Ultimate_of_All_Ages")

sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "tests"))
from anti_patch_guard import detect_solid_patches, compute_background_ssim, load_bubble_boxes

def inspect_ch533_p7():
    print("=== INSPECTING CHAPTER 533 PAGE 7 ===")
    v1_p = os.path.join(BACKEND_DATA, "chapter_533", "v1_original", "page_007.webp")
    v2_p = os.path.join(BACKEND_DATA, "chapter_533", "v2_cleaned", "page_007.webp")
    v3_p = os.path.join(BACKEND_DATA, "chapter_533", "v3_translated", "page_007.webp")
    
    if not os.path.exists(v1_p) or not os.path.exists(v2_p):
        print(f"Files not found: v1 exists={os.path.exists(v1_p)}, v2 exists={os.path.exists(v2_p)}")
        return
    
    v1 = cv2.imread(v1_p)
    v2 = cv2.imread(v2_p)
    v3 = cv2.imread(v3_p) if os.path.exists(v3_p) else None
    
    boxes = load_bubble_boxes(v1_p, v2_p)
    print(f"Loaded {len(boxes)} bubble boxes:")
    for idx, b in enumerate(boxes):
        print(f"  Box {idx}: {b}")
        
    res_a = detect_solid_patches(v2, boxes, variance_threshold=1.0)
    print(f"Check A Result: passed={res_a['passed']}, violations={res_a['violations_count']}")
    for v in res_a["violations"]:
        print(f"  Violation in box {v['box']}: mean_var={v['mean_variance']}, solid_subpatches={v['solid_subpatches']}/{v['total_subpatches']}")
        
    # Analyze the specific crop in v1 and v2
    for idx, b in enumerate(boxes):
        box = b.get("box", b) if isinstance(b, dict) else b
        x, y, w, h = box
        crop_v1 = v1[y:y+h, x:x+w]
        crop_v2 = v2[y:y+h, x:x+w]
        diff = cv2.absdiff(crop_v1, crop_v2)
        print(f"Box {idx} [x={x}, y={y}, w={w}, h={h}]:")
        print(f"  v1 crop shape: {crop_v1.shape}, v1 mean var: {np.mean(np.var(crop_v1, axis=(0,1))):.4f}")
        print(f"  v2 crop shape: {crop_v2.shape}, v2 mean var: {np.mean(np.var(crop_v2, axis=(0,1))):.4f}")
        print(f"  diff non-zero pixels: {np.count_nonzero(diff)} / {diff.size}")
        # Check unique colors in v2 crop
        unique_colors = len(np.unique(crop_v2.reshape(-1, 3), axis=0))
        print(f"  v2 unique colors: {unique_colors}")

def inspect_ch540_p4():
    print("\n=== INSPECTING CHAPTER 540 PAGE 4 ===")
    v1_p = os.path.join(BACKEND_DATA, "chapter_540", "v1_original", "page_004.webp")
    v2_p = os.path.join(BACKEND_DATA, "chapter_540", "v2_cleaned", "page_004.webp")
    v3_p = os.path.join(BACKEND_DATA, "chapter_540", "v3_translated", "page_004.webp")
    
    if not os.path.exists(v1_p) or not os.path.exists(v3_p):
        print(f"Files not found: v1={os.path.exists(v1_p)}, v3={os.path.exists(v3_p)}")
        return
        
    v1 = cv2.imread(v1_p)
    v2 = cv2.imread(v2_p) if os.path.exists(v2_p) else None
    v3 = cv2.imread(v3_p)
    
    boxes = load_bubble_boxes(v1_p, v2_p)
    print(f"Loaded {len(boxes)} boxes for Ch. 540 p. 4")
    
    res_b = compute_background_ssim(v1, v3, boxes, min_ssim=0.995, max_degradation_pct=0.5)
    print(f"Check B Result: passed={res_b['passed']}, bg_ssim={res_b['bg_ssim']}, degradation_pct={res_b['degradation_pct']}%")
    print(f"  bg_pixel_count: {res_b['bg_pixel_count']}, total_pixels: {res_b['total_pixels']}")
    
    # Let's inspect where difference lies outside boxes
    ih, iw = v1.shape[:2]
    diff = cv2.absdiff(v1, v3)
    diff_g = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(diff_g, 8, 255, cv2.THRESH_BINARY)
    print(f"Total modified pixels (diff > 8): {np.count_nonzero(thresh)}")

def inspect_all_chapters():
    print("\n=== CHAPTERS INVENTORY (531 to 542) ===")
    for ch_num in range(531, 543):
        ch_name = f"chapter_{ch_num}"
        b_ch = os.path.join(BACKEND_DATA, ch_name)
        f_ch = os.path.join(FRONTEND_PUBLIC, ch_name)
        
        v1_b = os.path.join(b_ch, "v1_original")
        v2_b = os.path.join(b_ch, "v2_cleaned")
        v3_b = os.path.join(b_ch, "v3_translated")
        
        v1_pages = [f for f in os.listdir(v1_b) if f.endswith((".webp", ".png")) and not f.endswith(".ocr.json")] if os.path.exists(v1_b) else []
        v2_pages = [f for f in os.listdir(v2_b) if f.endswith((".webp", ".png")) and not f.endswith(".ocr.json")] if os.path.exists(v2_b) else []
        v3_pages = [f for f in os.listdir(v3_b) if f.endswith((".webp", ".png")) and not f.endswith(".ocr.json")] if os.path.exists(v3_b) else []
        
        # Dimensions of v1 pages
        dims = []
        for p in v1_pages:
            try:
                with Image.open(os.path.join(v1_b, p)) as im:
                    dims.append((p, im.size))
            except Exception as e:
                dims.append((p, str(e)))
                
        manifest_b = os.path.exists(os.path.join(b_ch, "pipeline_manifest.json"))
        zips_b = [f for f in os.listdir(b_ch) if f.endswith(".zip")] if os.path.exists(b_ch) else []
        
        # Frontend check
        v1_f = os.path.join(f_ch, "v1")
        v2_f = os.path.join(f_ch, "v2")
        v3_f = os.path.join(f_ch, "v3")
        v1_f_cnt = len(os.listdir(v1_f)) if os.path.exists(v1_f) else 0
        v2_f_cnt = len(os.listdir(v2_f)) if os.path.exists(v2_f) else 0
        v3_f_cnt = len(os.listdir(v3_f)) if os.path.exists(v3_f) else 0
        meta_f = os.path.exists(os.path.join(f_ch, "meta.json"))
        
        print(f"Chapter {ch_num}:")
        print(f"  Backend: v1={len(v1_pages)}, v2={len(v2_pages)}, v3={len(v3_pages)} | Manifest={manifest_b} | Zips={len(zips_b)}")
        print(f"  Frontend: v1={v1_f_cnt}, v2={v2_f_cnt}, v3={v3_f_cnt} | meta.json={meta_f}")
        print(f"  v1 Dimensions: {dims}")

if __name__ == "__main__":
    inspect_ch533_p7()
    inspect_ch540_p4()
    inspect_all_chapters()
