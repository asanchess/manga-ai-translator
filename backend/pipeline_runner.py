# -*- coding: utf-8 -*-
"""
End-to-End Manga Translation Pipeline Runner
Orchestrates OCR -> Bubble Cleaning -> Translation -> Typesetting -> Output
"""
import os
import sys
import json
import time
import shutil
import re
import argparse
import logging
from PIL import Image
import cv2
import numpy as np

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
sys.path.insert(0, os.path.dirname(__file__))

from agents.ocr_engine import extract_text_and_bubbles
from agents.cleaner_agent import process_page_cleaning
from agents.translator_typesetter_agent import process_page_translation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PipelineRunner")

DEFAULT_FRONTEND_PUBLIC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "manga")
)

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def process_page(
    image_path: str,
    manga_title: str,
    chapter_num: str,
    page_num: int,
    output_root: str = None
) -> dict:
    """
    Processes a single manga page through the full 5-stage pipeline:
    1. RAW Ingestion -> v1 (Original)
    2. OCR & NMS Detection with 1-based IDs
    3. Seamless Inpainting -> v2 (Cleaned)
    4. Batch LLM Translation (Ollama / OpenRouter / Cache)
    5. Typesetting -> v3 (Translated, <=85% bounds, centered)
    6. Metadata update
    """
    clean_title = manga_title.replace(" ", "_")
    chapter_folder = f"chapter_{chapter_num}"
    base_root = output_root or DEFAULT_FRONTEND_PUBLIC
    base_out = os.path.join(base_root, clean_title, chapter_folder)
    
    v1_dir = os.path.join(base_out, "v1")
    v1_orig_dir = os.path.join(base_out, "v1_original")
    v2_dir = os.path.join(base_out, "v2")
    v2_clean_dir = os.path.join(base_out, "v2_cleaned")
    v3_dir = os.path.join(base_out, "v3")
    v3_trans_dir = os.path.join(base_out, "v3_translated")
    
    ensure_dirs(v1_dir, v1_orig_dir, v2_dir, v2_clean_dir, v3_dir, v3_trans_dir)
    
    page_filename = f"page_{page_num:03d}.webp"
    v1_path = os.path.join(v1_dir, page_filename)
    v1_orig_path = os.path.join(v1_orig_dir, page_filename)
    v2_path = os.path.join(v2_dir, page_filename)
    v2_clean_path = os.path.join(v2_clean_dir, page_filename)
    v3_path = os.path.join(v3_dir, page_filename)
    v3_trans_path = os.path.join(v3_trans_dir, page_filename)

    logger.info(f"--- Processing Page {page_num} [{clean_title} Ch.{chapter_num}] ---")

    # Step 1: Save RAW image as WebP (v1)
    logger.info(f"[Step 1/5] Ingesting RAW image -> {v1_path}")
    raw_img = Image.open(image_path).convert("RGB")
    width, height = raw_img.size
    raw_img.save(v1_path, "WEBP", quality=95)
    shutil.copy2(v1_path, v1_orig_path)
    
    # Check if OCR cache exists in input dir
    src_ocr_cache = image_path + ".ocr.json"
    dst_ocr_cache = v1_path + ".ocr.json"
    if os.path.exists(src_ocr_cache) and not os.path.exists(dst_ocr_cache):
        shutil.copy2(src_ocr_cache, dst_ocr_cache)

    # Step 2: OCR & Text Bubble Detection
    logger.info(f"[Step 2/5] Running OCR & Containment NMS on {v1_path}...")
    clusters = extract_text_and_bubbles(v1_path, use_cache=True)
    logger.info(f"Detected {len(clusters)} text clusters.")

    # Step 3: Seamless Speech Bubble Cleaning (v2)
    logger.info(f"[Step 3/5] Cleaning speech bubbles -> {v2_path}...")
    process_page_cleaning(v1_path, clusters, output_path=v2_path)
    shutil.copy2(v2_path, v2_clean_path)

    # Step 4 & 5: LLM Translation & Typesetting (v3)
    logger.info(f"[Step 4-5/5] Translating & typesetting bubbles -> {v3_path}...")
    process_page_translation(v2_path, clusters, output_path=v3_path)
    shutil.copy2(v3_path, v3_trans_path)

    # Step 6: Update Chapter Metadata
    meta_path = os.path.join(base_out, "meta.json")
    meta_data = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception:
            pass

    pages_list = meta_data.get("pages", [])
    page_entry = {
        "page_num": page_num,
        "filename": page_filename,
        "width": width,
        "height": height,
        "bubbles_count": len(clusters),
        "v1": f"/manga/{clean_title}/{chapter_folder}/v1/{page_filename}",
        "v2": f"/manga/{clean_title}/{chapter_folder}/v2/{page_filename}",
        "v3": f"/manga/{clean_title}/{chapter_folder}/v3/{page_filename}"
    }

    updated = False
    for idx, p in enumerate(pages_list):
        if p.get("page_num") == page_num:
            pages_list[idx] = page_entry
            updated = True
            break
    if not updated:
        pages_list.append(page_entry)
        
    pages_list.sort(key=lambda x: x["page_num"])
    
    meta_data.update({
        "manga": clean_title,
        "chapter": str(chapter_num),
        "total_pages": len(pages_list),
        "last_updated": time.time(),
        "pages": pages_list
    })

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "page_num": page_num,
        "v1": v1_path,
        "v2": v2_path,
        "v3": v3_path,
        "bubbles": len(clusters)
    }

def update_global_chapters_index(public_root: str = DEFAULT_FRONTEND_PUBLIC):
    """
    Crawls public manga directory and rebuilds global chapters_index.json for the frontend.
    """
    root = public_root or DEFAULT_FRONTEND_PUBLIC
    index_file = os.path.join(root, "chapters_index.json")
    manifest = {
        "title": "Manga AI Translation Library",
        "last_synced": time.time(),
        "mangas": {}
    }

    if not os.path.exists(public_root):
        return manifest

    for manga_name in sorted(os.listdir(public_root)):
        manga_path = os.path.join(public_root, manga_name)
        if not os.path.isdir(manga_path) or manga_name.startswith('.'):
            continue

        chapters = []
        for ch_name in sorted(os.listdir(manga_path)):
            ch_path = os.path.join(manga_path, ch_name)
            if not os.path.isdir(ch_path) or not ch_name.startswith("chapter_"):
                continue

            meta_file = os.path.join(ch_path, "meta.json")
            ch_num = ch_name.replace("chapter_", "")
            pages_count = 0
            
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as mf:
                        cdata = json.load(mf)
                        pages_count = cdata.get("total_pages", len(cdata.get("pages", [])))
                except Exception:
                    pass
            else:
                v1_dir = os.path.join(ch_path, "v1")
                if os.path.exists(v1_dir):
                    pages_count = len([f for f in os.listdir(v1_dir) if f.endswith('.webp')])

            chapters.append({
                "chapter": ch_num,
                "folder": ch_name,
                "pages_count": pages_count,
                "meta_url": f"/manga/{manga_name}/{ch_name}/meta.json"
            })

        chapters.sort(key=lambda c: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', c["chapter"])])
        
        manifest["mangas"][manga_name] = {
            "title": manga_name.replace("_", " "),
            "chapters": chapters,
            "total_chapters": len(chapters)
        }

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Updated global metadata -> {index_file}")
    return manifest

def process_chapter(
    input_dir: str,
    manga_title: str,
    chapter_num: str,
    output_root: str = DEFAULT_FRONTEND_PUBLIC,
    progress_callback = None
) -> dict:
    """
    Processes all pages inside input_dir for a given chapter.
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    all_files = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in valid_exts]
    
    def sort_key(fn):
        digits = [int(s) for s in re.findall(r'\d+', fn)]
        return digits[0] if digits else fn
        
    all_files.sort(key=sort_key)
    
    total = len(all_files)
    logger.info(f"Starting chapter translation: {manga_title} Ch.{chapter_num} ({total} pages)")
    
    results = []
    for idx, filename in enumerate(all_files, 1):
        img_path = os.path.join(input_dir, filename)
        if progress_callback:
            progress_callback(idx, total, f"Processing page {idx}/{total}: {filename}")
            
        page_res = process_page(
            image_path=img_path,
            manga_title=manga_title,
            chapter_num=chapter_num,
            page_num=idx,
            output_root=output_root
        )
        results.append(page_res)

    target_output_root = output_root or DEFAULT_FRONTEND_PUBLIC
    update_global_chapters_index(target_output_root)
    
    return {
        "status": "completed",
        "manga": manga_title,
        "chapter": chapter_num,
        "total_pages": total,
        "pages": results
    }

def main():
    parser = argparse.ArgumentParser(description="Manga AI Translation Pipeline Runner")
    parser.add_argument("--input", required=True, help="Path to input RAW image file or directory")
    parser.add_argument("--title", required=True, help="Manga title (e.g. 'The_Ultimate_of_All_Ages')")
    parser.add_argument("--chapter", required=True, help="Chapter number (e.g. '531')")
    parser.add_argument("--output_dir", default=None, help="Custom output directory")
    
    args = parser.parse_args()
    
    inp = os.path.abspath(args.input)
    if os.path.isfile(inp):
        res = process_page(
            image_path=inp,
            manga_title=args.title,
            chapter_num=args.chapter,
            page_num=1,
            output_root=args.output_dir
        )
        update_global_chapters_index(args.output_dir or DEFAULT_FRONTEND_PUBLIC)
        print(f"\n[OK] Successfully processed single page: {json.dumps(res, indent=2)}")
    elif os.path.isdir(inp):
        res = process_chapter(
            input_dir=inp,
            manga_title=args.title,
            chapter_num=args.chapter,
            output_root=args.output_dir
        )
        print(f"\n[OK] Successfully processed chapter: {json.dumps(res, indent=2)}")
    else:
        print(f"Error: Path '{inp}' does not exist.")
        sys.exit(1)

if __name__ == "__main__":
    main()
