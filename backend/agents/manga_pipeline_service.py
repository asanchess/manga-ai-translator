# -*- coding: utf-8 -*-
"""
MangaPipelineService — Unified Central Pipeline Service for Manga AI Translator.
Handles full lifecycle: Ingestion/Download -> 2-Pass OCR -> Seamless Inpainting -> LLM Translation -> Typesetting -> QA -> Indexing.
"""
import os
import sys
import time
import json
import uuid
import zipfile
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Callable, Dict, Any

from PIL import Image
import cv2
import numpy as np

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
DATA_DIR = os.path.join(BASE_DIR, "data", "manga")
DEFAULT_FRONTEND_PUBLIC = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "public", "manga")
)

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ocr_engine import extract_text_and_bubbles, is_sound_effect
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection
from scraper_agent import ScraperAgent
from llm_translator import check_ollama_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] MangaPipeline: %(message)s")
logger = logging.getLogger("MangaPipeline")

# In-memory task state registry
active_tasks: Dict[str, Dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=2)


def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def update_global_chapters_index(public_root: str = DEFAULT_FRONTEND_PUBLIC):
    """
    Scans all manga folders in the public storage directory and updates chapters_index.json.
    """
    if not public_root or not os.path.exists(public_root):
        return

    manga_entries = {}
    for manga_name in os.listdir(public_root):
        manga_dir = os.path.join(public_root, manga_name)
        if not os.path.isdir(manga_dir):
            continue

        chapters = []
        for ch_name in sorted(os.listdir(manga_dir)):
            ch_dir = os.path.join(manga_dir, ch_name)
            if not os.path.isdir(ch_dir) or not ch_name.startswith("chapter_"):
                continue

            ch_num = ch_name.replace("chapter_", "")
            v3_dir = os.path.join(ch_dir, "v3")
            v3_alt = os.path.join(ch_dir, "v3_translated")
            
            pages_count = 0
            if os.path.exists(v3_dir):
                pages_count = len([f for f in os.listdir(v3_dir) if f.endswith(".webp")])
            elif os.path.exists(v3_alt):
                pages_count = len([f for f in os.listdir(v3_alt) if f.endswith(".webp")])

            meta_file = os.path.join(ch_dir, "meta.json")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        if "total_pages" in m_data:
                            pages_count = m_data["total_pages"]
                except Exception:
                    pass

            chapters.append({
                "chapter": ch_num,
                "folder": ch_name,
                "pages_count": pages_count,
                "meta_url": f"/manga/{manga_name}/{ch_name}/meta.json"
            })

        chapters.sort(key=lambda x: int(x["chapter"]) if x["chapter"].isdigit() else str(x["chapter"]))
        manga_entries[manga_name] = {
            "title": manga_name.replace("_", " "),
            "chapters": chapters,
            "total_chapters": len(chapters)
        }

    index_payload = {
        "title": "Manga AI Translation Library",
        "last_synced": time.time(),
        "mangas": manga_entries
    }

    index_file = os.path.join(public_root, "chapters_index.json")
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Updated global metadata -> {index_file}")
    return index_payload


class MangaPipelineService:
    """
    Central facade for Manga AI Translation SDLC.
    """

    @staticmethod
    def process_page(
        image_path: str,
        manga_title: str,
        chapter_num: str,
        page_num: int,
        output_root: Optional[str] = None
    ) -> dict:
        """
        Processes a single manga page through the full 5-stage pipeline:
        1. RAW Ingestion -> v1 (Original)
        2. 2-Pass OCR & NMS Detection with 1-based sequential IDs
        3. Seamless Per-Pixel Inpainting -> v2 (Cleaned)
        4. Batch LLM Translation (Ollama / OpenRouter / Cache)
        5. Typesetting -> v3 (Translated, <=85% bounds, centered)
        6. Metadata and multi-layer sync
        """
        clean_title = manga_title.replace(" ", "_")
        ch_clean = str(chapter_num).replace("chapter_", "")
        chapter_folder = f"chapter_{ch_clean}"

        # 1. Base paths in frontend/public and backend/data
        pub_root = output_root or DEFAULT_FRONTEND_PUBLIC
        pub_chapter_dir = os.path.join(pub_root, clean_title, chapter_folder)
        backend_chapter_dir = os.path.join(DATA_DIR, clean_title, chapter_folder)

        # Standard subdirectories
        v1_pub = os.path.join(pub_chapter_dir, "v1")
        v2_pub = os.path.join(pub_chapter_dir, "v2")
        v3_pub = os.path.join(pub_chapter_dir, "v3")

        v1_backend = os.path.join(backend_chapter_dir, "v1_original")
        v2_backend = os.path.join(backend_chapter_dir, "v2_cleaned")
        v3_backend = os.path.join(backend_chapter_dir, "v3_translated")

        ensure_dirs(v1_pub, v2_pub, v3_pub, v1_backend, v2_backend, v3_backend)

        page_filename = f"page_{page_num:03d}.webp"
        
        v1_p = os.path.join(v1_pub, page_filename)
        v2_p = os.path.join(v2_pub, page_filename)
        v3_p = os.path.join(v3_pub, page_filename)

        v1_b_p = os.path.join(v1_backend, page_filename)
        v2_b_p = os.path.join(v2_backend, page_filename)
        v3_b_p = os.path.join(v3_backend, page_filename)

        logger.info(f"--- Processing Page {page_num} [{clean_title} Ch.{ch_clean}] ---")

        # Step 1: RAW Ingestion -> v1
        logger.info(f"[Step 1/5] Ingesting RAW image -> {v1_p}")
        raw_img = Image.open(image_path).convert("RGB")
        width, height = raw_img.size
        raw_img.save(v1_p, "WEBP", quality=95)
        raw_img.save(v1_b_p, "WEBP", quality=95)

        # Propagate OCR cache if present
        src_ocr_cache = image_path + ".ocr.json"
        dst_ocr_cache = v1_p + ".ocr.json"
        if os.path.exists(src_ocr_cache) and not os.path.exists(dst_ocr_cache):
            shutil.copy2(src_ocr_cache, dst_ocr_cache)

        # Step 2: 2-Pass OCR & Bubble Detection
        logger.info(f"[Step 2/5] Running 2-Pass OCR & Containment NMS on {v1_p}...")
        clusters = extract_text_and_bubbles(v1_p, use_cache=True)
        for c in clusters:
            c["is_sfx"] = is_sound_effect(c.get("text", ""))
        logger.info(f"Detected {len(clusters)} text clusters.")

        # Step 3: Seamless Per-Pixel Glyph Inpainting -> v2
        logger.info(f"[Step 3/5] Cleaning speech bubbles -> {v2_p}...")
        process_page_cleaning(v1_p, clusters, output_path=v2_p)
        shutil.copy2(v2_p, v2_b_p)

        # Step 4 & 5: LLM Translation & Typesetting -> v3
        logger.info(f"[Step 4-5/5] Translating & typesetting bubbles -> {v3_p}...")
        process_page_translation(v2_p, clusters, output_path=v3_p, manga_title=clean_title)
        shutil.copy2(v3_p, v3_b_p)


        # Step 6: Update Metadata
        meta_path = os.path.join(pub_chapter_dir, "meta.json")
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
            "chapter": str(ch_clean),
            "total_pages": len(pages_list),
            "last_updated": time.time(),
            "pages": pages_list
        })

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "page_num": page_num,
            "v1": v1_p,
            "v2": v2_p,
            "v3": v3_p,
            "bubbles": len(clusters)
        }

    @staticmethod
    def process_chapter(
        input_dir: str,
        manga_title: str,
        chapter_num: str,
        output_root: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> dict:
        """
        Batch processes all manga pages in an input directory.
        """
        valid_exts = (".webp", ".png", ".jpg", ".jpeg")
        files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")]

        def natural_sort_key(s):
            import re
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        files.sort(key=natural_sort_key)

        if not files:
            raise FileNotFoundError(f"No valid image files found in {input_dir}")

        total_pages = len(files)
        logger.info(f"Starting chapter translation: {manga_title} Ch.{chapter_num} ({total_pages} pages)")

        results = []
        for idx, filename in enumerate(files, 1):
            file_path = os.path.join(input_dir, filename)
            if progress_callback:
                progress_callback(idx, total_pages, f"Processing page {idx}/{total_pages} ({filename})...")

            page_res = MangaPipelineService.process_page(
                image_path=file_path,
                manga_title=manga_title,
                chapter_num=chapter_num,
                page_num=idx,
                output_root=output_root
            )
            results.append(page_res)

        target_root = output_root or DEFAULT_FRONTEND_PUBLIC
        update_global_chapters_index(target_root)

        return {
            "status": "completed",
            "manga": manga_title,
            "chapter": str(chapter_num),
            "total_pages": total_pages,
            "pages": results
        }

    @staticmethod
    def create_task(manga_name: str, chapter_num: str, source_url: Optional[str] = None, options: Optional[dict] = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        ch_clean = str(chapter_num).replace("chapter_", "")
        active_tasks[task_id] = {
            "task_id": task_id,
            "manga_name": manga_name,
            "chapter_num": ch_clean,
            "source_url": source_url,
            "options": options or {},
            "status": "queued",
            "progress": 0,
            "current_step": "Инициализация задачи",
            "total_pages": 0,
            "processed_pages": 0,
            "pages_status": [],
            "logs": [f"[{time.strftime('%H:%M:%S')}] Задача зарегистрирована."],
            "error": None,
            "result_url": None,
            "created_at": time.time()
        }
        return task_id

    @staticmethod
    def log(task_id: str, message: str):
        if task_id in active_tasks:
            t_str = time.strftime("%H:%M:%S")
            active_tasks[task_id]["logs"].append(f"[{t_str}] {message}")
            logger.info(f"[{task_id}] {message}")

    @staticmethod
    def update_progress(task_id: str, progress: int, step: str):
        if task_id in active_tasks:
            active_tasks[task_id]["progress"] = progress
            active_tasks[task_id]["current_step"] = step

    @staticmethod
    def run_pipeline_async(task_id: str):
        _executor.submit(MangaPipelineService._execute_task, task_id)

    @staticmethod
    def _execute_task(task_id: str):
        task = active_tasks.get(task_id)
        if not task:
            return

        manga_name = task["manga_name"]
        chapter_num = task["chapter_num"]
        source_url = task.get("source_url")
        temp_input_dir = task.get("options", {}).get("temp_input_dir")

        chapter_folder = f"chapter_{chapter_num}"
        chapter_path = os.path.join(DATA_DIR, manga_name, chapter_folder)
        orig_dir = os.path.join(chapter_path, "v1_original")
        clean_dir = os.path.join(chapter_path, "v2_cleaned")
        trans_dir = os.path.join(chapter_path, "v3_translated")

        ensure_dirs(orig_dir, clean_dir, trans_dir)

        try:
            task["status"] = "running"
            MangaPipelineService.log(task_id, f"Запуск автономного пайплайна для '{manga_name}' (Глава {chapter_num})")
            MangaPipelineService.update_progress(task_id, 10, "1/5: Скачивание и сборка страниц")

            # 1. Fetch / Copy pages into v1_original
            if temp_input_dir and os.path.exists(temp_input_dir):
                valid_exts = (".webp", ".png", ".jpg", ".jpeg")
                for fn in os.listdir(temp_input_dir):
                    if fn.lower().endswith(valid_exts) and not fn.endswith(".ocr.json"):
                        shutil.copy2(os.path.join(temp_input_dir, fn), os.path.join(orig_dir, fn))
            elif source_url and not os.listdir(orig_dir):
                MangaPipelineService.log(task_id, f"Скачивание страниц по URL: {source_url}")
                scraper = ScraperAgent(output_dir=DATA_DIR)
                import asyncio
                asyncio.run(scraper.download_chapter_async(manga_name, str(chapter_num)))

            pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])
            if not pages:
                raise Exception(f"Страницы главы не найдены в {orig_dir}. Загрузите файлы или укажите URL.")

            total_pages = len(pages)
            task["total_pages"] = total_pages
            task["pages_status"] = [{"page": p, "step": "в очереди", "progress": 0} for p in pages]
            MangaPipelineService.log(task_id, f"Найдено страниц для перевода: {total_pages}")

            # 2. Process chapter with live callback
            def progress_cb(cur: int, tot: int, msg: str):
                pct = 15 + int((cur / max(1, tot)) * 75)
                MangaPipelineService.update_progress(task_id, pct, f"Обработка [{cur}/{tot}]: {msg}")
                MangaPipelineService.log(task_id, msg)
                if cur <= len(task["pages_status"]):
                    task["pages_status"][cur - 1]["step"] = "Готово"
                    task["pages_status"][cur - 1]["progress"] = 100
                task["processed_pages"] = cur

            result = MangaPipelineService.process_chapter(
                input_dir=orig_dir,
                manga_title=manga_name,
                chapter_num=chapter_num,
                output_root=DEFAULT_FRONTEND_PUBLIC,
                progress_callback=progress_cb
            )

            # 3. Create ZIP archive
            MangaPipelineService.update_progress(task_id, 95, "Создание архива главы (ZIP)")
            zip_filename = f"{manga_name}_Chapter_{chapter_num}_Russian.zip"
            zip_path = os.path.join(chapter_path, zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for p in sorted(os.listdir(trans_dir)):
                    if p.endswith(".webp"):
                        zipf.write(os.path.join(trans_dir, p), arcname=p)

            task["status"] = "completed"
            task["progress"] = 100
            task["current_step"] = "Глава полностью переведена и опубликована!"
            task["result"] = result
            task["result_url"] = f"/reader/{manga_name}?chapter=chapter_{chapter_num}"
            MangaPipelineService.log(task_id, f"✓ Глава {chapter_num} успешно обработана и готова!")

        except Exception as e:
            logger.exception("Pipeline execution failed:")
            task["status"] = "failed"
            task["error"] = str(e)
            MangaPipelineService.log(task_id, f"❌ Ошибка: {str(e)}")
        finally:
            if temp_input_dir and os.path.exists(temp_input_dir):
                shutil.rmtree(temp_input_dir, ignore_errors=True)

    @staticmethod
    def get_task_status(task_id: str) -> dict:
        return active_tasks.get(task_id, {"error": "Task not found"})


# Module-level aliases
process_page = MangaPipelineService.process_page
process_chapter = MangaPipelineService.process_chapter

if __name__ == "__main__":
    print("MangaPipelineService ready.")
