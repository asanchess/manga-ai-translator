# -*- coding: utf-8 -*-
import cv2
import numpy as np
import easyocr
import json
import os
import re

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader

def is_sound_effect(text: str) -> bool:
    """
    Identifies standalone SFX/sound effects.
    Sentences and dialogue must NEVER be classified as SFX.
    """
    t = text.lower().strip()
    words = t.split()
    
    # Dialogue sentences with multiple words or dialogue punctuation
    if len(words) > 3 or len(t) > 20:
        return False
    if any(p in t for p in ['.', '?', '...', ',', ':', ';']):
        return False
        
    sfx_keywords = {
        "boom", "whoosh", "bang", "slash", "crash", "clash", "bzzt", "swish", 
        "rumble", "thud", "snap", "wham", "crack", "gasp", "ah", "ahh", "shing", 
        "clank", "pant", "woosh", "wouip", "fwoosh", "roar", "ha", "hah", "haha", "tsk",
        "dong", "bam", "kacha", "clang", "giggle", "sigh", "gulp", "drip"
    }
    
    clean_words = [re.sub(r'[^a-z]', '', w) for w in words]
    if any(w in sfx_keywords for w in clean_words):
        return True
        
    # Standalone 1-2 words in all-caps without punctuation
    if len(words) <= 2 and text.isupper() and len(text) <= 8 and not any(c.isdigit() for c in text):
        return True
        
    return False

def calculate_iou(box1: tuple, box2: tuple) -> float:
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    
    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter_area = inter_w * inter_h
    
    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / float(union_area)

def safe_ocr_read(chunk: np.ndarray, detail: int = 1) -> list:
    if chunk is None or chunk.size == 0 or chunk.shape[0] < 4 or chunk.shape[1] < 4:
        return []
    try:
        reader = get_reader()
        return reader.readtext(chunk, detail=detail)
    except Exception:
        return []

def extract_text_and_bubbles(image_path: str, use_cache: bool = True) -> list:
    cache_path = image_path + ".ocr.json"
    if use_cache and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    img = cv2.imread(image_path)
    if img is None:
        return []
        
    h, w, _ = img.shape
    chunk_h = 2400
    overlap = 120
    
    raw_detections = []
    
    # Pass 1: Standard OCR pass
    for y_start in range(0, h, chunk_h - overlap):
        y_end = min(h, y_start + chunk_h)
        chunk = img[y_start:y_end, :]
        
        results = safe_ocr_read(chunk, detail=1)
        for bbox, text, conf in results:
            clean_t = text.strip()
            if conf < 0.10 or len(clean_t) < 2:
                continue
            xs = [int(p[0]) for p in bbox]
            ys = [int(p[1]) + y_start for p in bbox]
            bx = max(0, min(xs))
            by = max(0, min(ys))
            bw = min(w - bx, max(xs) - bx)
            bh = min(h - by, max(ys) - by)
            
            raw_detections.append({
                "box": (bx, by, bw, bh),
                "text": clean_t,
                "conf": conf,
                "is_dark": False
            })
            
    # Pass 2: Inverted pass for white-on-dark text
    for y_start in range(0, h, chunk_h - overlap):
        y_end = min(h, y_start + chunk_h)
        chunk = img[y_start:y_end, :]
        chunk_gray = cv2.cvtColor(chunk, cv2.COLOR_BGR2GRAY)
        
        if np.sum(chunk_gray < 50) > 1000:
            inverted_chunk = 255 - chunk
            results_inv = safe_ocr_read(inverted_chunk, detail=1)
            for bbox, text, conf in results_inv:
                clean_t = text.strip()
                if conf < 0.10 or len(clean_t) < 2:
                    continue
                xs = [int(p[0]) for p in bbox]
                ys = [int(p[1]) + y_start for p in bbox]
                bx = max(0, min(xs))
                by = max(0, min(ys))
                bw = min(w - bx, max(xs) - bx)
                bh = min(h - by, max(ys) - by)
                
                cy = min(h-1, by + bh // 2)
                cx = min(w-1, bx + bw // 2)
                if img[cy, cx, 0] < 70 and img[cy, cx, 1] < 70 and img[cy, cx, 2] < 70:
                    raw_detections.append({
                        "box": (bx, by, bw, bh),
                        "text": clean_t,
                        "conf": conf,
                        "is_dark": True
                    })
                    
    # --- DEDUPLICATION OF RAW DETECTIONS ---
    deduped_detections = []
    for d in raw_detections:
        is_dup = False
        for existing in deduped_detections:
            iou = calculate_iou(d["box"], existing["box"])
            if iou > 0.35:
                # Keep the one with higher confidence
                if d["conf"] > existing["conf"]:
                    existing["box"] = d["box"]
                    existing["text"] = d["text"]
                    existing["conf"] = d["conf"]
                is_dup = True
                break
        if not is_dup:
            deduped_detections.append(d)
            
    # --- SPATIAL CLUSTERING INTO SPEECH BUBBLES ---
    clusters = []
    used = set()
    deduped_detections.sort(key=lambda d: (d["box"][1], d["box"][0]))
    
    for i, d1 in enumerate(deduped_detections):
        if i in used:
            continue
        used.add(i)
        
        bx, by, bw, bh = d1["box"]
        cluster_texts = [d1["text"]]
        cluster_boxes = [(bx, by, bw, bh)]
        is_dark = d1["is_dark"]
        
        for j, d2 in enumerate(deduped_detections):
            if j in used:
                continue
            ox, oy, ow, oh = d2["box"]
            
            # Check vertical and horizontal proximity for multi-line bubbles
            vert_dist = oy - (by + bh)
            overlap_y = max(0, min(by + bh, oy + oh) - max(by, oy))
            horiz_dist = max(0, max(bx, ox) - min(bx + bw, ox + ow))
            overlap_x = max(0, min(bx + bw, ox + ow) - max(bx, ox))
            
            # If boxes overlap or are adjacent lines in the same bubble
            if (overlap_y > 0 or -10 <= vert_dist <= 75) and (overlap_x > 0 or horiz_dist <= 80):
                used.add(j)
                cluster_texts.append(d2["text"])
                cluster_boxes.append((ox, oy, ow, oh))
                min_x = min(bx, ox)
                min_y = min(by, oy)
                max_x = max(bx + bw, ox + ow)
                max_y = max(by + bh, oy + oh)
                bx, by, bw, bh = min_x, min_y, max_x - min_x, max_y - min_y
                if d2["is_dark"]:
                    is_dark = True
                    
        full_text = " ".join(cluster_texts)
        clusters.append({
            "box": (bx, by, bw, bh),
            "text": full_text,
            "lines": cluster_boxes,
            "is_sfx": is_sound_effect(full_text),
            "is_dark": is_dark
        })
        
    # --- FINAL STRICT CLUSTER MERGING & NON-MAXIMUM SUPPRESSION ---
    final_clusters = []
    for c in clusters:
        x1, y1, w1, h1 = c["box"]
        area1 = w1 * h1
        absorbed = False
        
        for ex in final_clusters:
            x2, y2, w2, h2 = ex["box"]
            area2 = w2 * h2
            
            xi1 = max(x1, x2)
            yi1 = max(y1, y2)
            xi2 = min(x1 + w1, x2 + w2)
            yi2 = min(y1 + h1, y2 + h2)
            inter_w = max(0, xi2 - xi1)
            inter_h = max(0, yi2 - yi1)
            inter_area = inter_w * inter_h
            
            min_area = min(area1, area2)
            union_area = area1 + area2 - inter_area
            
            # If one box contains the other or substantial overlap
            if min_area > 0 and (inter_area / float(min_area) > 0.30 or (union_area > 0 and inter_area / float(union_area) > 0.20)):
                # Merge into single enclosing box
                nx = min(x1, x2)
                ny = min(y1, y2)
                nw = max(x1 + w1, x2 + w2) - nx
                nh = max(y1 + h1, y2 + h2) - ny
                ex["box"] = (nx, ny, nw, nh)
                
                # Keep the longer, more complete text
                t1 = c.get("text", "").strip()
                t2 = ex.get("text", "").strip()
                if len(t1) > len(t2):
                    ex["text"] = t1
                    
                if c.get("is_dark") or ex.get("is_dark"):
                    ex["is_dark"] = True
                    
                absorbed = True
                break
                
        if not absorbed:
            final_clusters.append(c)
            
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(final_clusters, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
        
    return final_clusters

if __name__ == "__main__":
    print("OCR Engine module ready.")
