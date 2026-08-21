# -*- coding: utf-8 -*-
import os
import sys
import json
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from ocr_engine import calculate_iou

def deduplicate_clusters(clusters: list) -> list:
    final = []
    # Sort by text length descending so longer complete sentences come first
    sorted_c = sorted(clusters, key=lambda c: len(c.get("text", "")), reverse=True)
    
    for c in sorted_c:
        cb = c["box"]
        ct = c.get("text", "").strip()
        if not ct or len(ct) < 2:
            continue
            
        # Ignore credit watermarks
        if "scythescans" in ct.lower() or "brought to you by" in ct.lower() or "exclusive chapters" in ct.lower():
            continue
            
        is_dup = False
        for ex in final:
            eb = ex["box"]
            et = ex.get("text", "").strip()
            
            iou = calculate_iou(cb, eb)
            
            # Intersection area check
            ix1 = max(cb[0], eb[0])
            iy1 = max(cb[1], eb[1])
            ix2 = min(cb[0] + cb[2], eb[0] + eb[2])
            iy2 = min(cb[1] + cb[3], eb[1] + eb[3])
            inter_w = max(0, ix2 - ix1)
            inter_h = max(0, iy2 - iy1)
            inter_area = inter_w * inter_h
            min_area = min(cb[2] * cb[3], eb[2] * eb[3])
            overlap_ratio = inter_area / float(min_area) if min_area > 0 else 0
            
            if iou > 0.25 or overlap_ratio > 0.50 or (ct.lower() in et.lower() and overlap_ratio > 0.30):
                is_dup = True
                # Merge missing line boxes into the master cluster
                for l in c.get("lines", []):
                    if l not in ex.get("lines", []):
                        ex.setdefault("lines", []).append(l)
                break
                
        if not is_dup:
            words = ct.split()
            if len(words) > 3 or len(ct) > 20 or any(p in ct for p in ['.', '?', '!', ',', '...']):
                c["is_sfx"] = False
            final.append(c)
            
    final.sort(key=lambda c: (c["box"][1], c["box"][0]))
    return final

def reprocess_all():
    manga_dir = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages")
    chapters = ["chapter_531", "chapter_532"]
    
    for ch in chapters:
        orig_dir = os.path.join(manga_dir, ch, "v1_original")
        clean_dir = os.path.join(manga_dir, ch, "v2_cleaned")
        trans_dir = os.path.join(manga_dir, ch, "v3_translated")
        
        if not os.path.exists(orig_dir):
            continue
            
        pages = sorted([f for f in os.listdir(orig_dir) if f.endswith('.webp') and not f.endswith('.ocr.json')])
        print(f"=== Reprocessing {ch} ({len(pages)} pages) ===")
        
        for p in pages:
            orig_file = os.path.join(orig_dir, p)
            ocr_file = os.path.join(orig_dir, p + ".ocr.json")
            cleaned_file = os.path.join(clean_dir, p)
            out_file = os.path.join(trans_dir, p)
            
            if os.path.exists(ocr_file) and os.path.exists(orig_file):
                with open(ocr_file, "r", encoding="utf-8") as f:
                    raw_clusters = json.load(f)
                clean_clusters = deduplicate_clusters(raw_clusters)
                
                # 1. Clean page with precision inpainting
                process_page_cleaning(orig_file, cleaned_file, clean_clusters)
                # 2. Typeset Russian translation with Cyrillic Comic font
                process_page_translation(cleaned_file, out_file, clean_clusters)
                print(f"[OK] {ch}/{p} -> Cleaned & Typeset ({len(clean_clusters)} bubbles).")

        # 3. Re-package ZIP
        ch_num = ch.replace("chapter_", "")
        zip_name = f"The_Ultimate_of_All_Ages_Chapter_{ch_num}_Russian.zip"
        zip_path = os.path.join(trans_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in os.listdir(trans_dir):
                if f.endswith('.webp'):
                    zipf.write(os.path.join(trans_dir, f), arcname=f)
        print(f"[OK] Re-packaged ZIP: {zip_path}")

if __name__ == "__main__":
    reprocess_all()
