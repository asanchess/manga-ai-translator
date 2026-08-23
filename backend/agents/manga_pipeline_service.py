# -*- coding: utf-8 -*-
"""
MangaPipelineService — Unified Central Pipeline Service for Manga AI Translator.
Handles full lifecycle: Ingestion/Download -> 2-Pass OCR -> Seamless Inpainting -> LLM Translation -> Typesetting -> QA -> Manifest/Packaging -> Indexing.
Includes fine-grained per-substep telemetry and real-time async event broadcasting for SSE streaming.
"""
import os
import sys
import time
import json
import uuid
import zipfile
import shutil
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Callable, Dict, Any, Tuple

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
    Central facade for Manga AI Translation SDLC with real-time SSE telemetry broadcasting.
    """

    @staticmethod
    def create_task(
        manga_name: str,
        chapter_num: str,
        source_url: Optional[str] = None,
        options: Optional[dict] = None
    ) -> str:
        """
        Creates and registers a new pipeline task in the registry.
        """
        task_id = str(uuid.uuid4())[:8]
        ch_clean = str(chapter_num).replace("chapter_", "")
        clean_title = manga_name.replace(" ", "_")

        active_tasks[task_id] = {
            "task_id": task_id,
            "manga_name": clean_title,
            "chapter_num": ch_clean,
            "source_url": source_url,
            "options": options or {},
            "status": "queued",
            "stage": "Queue",
            "progress": 0,
            "current_step": "Инициализация задачи",
            "total_pages": 0,
            "processed_pages": 0,
            "current_page": 0,
            "pages_status": [],
            "logs": [f"[{time.strftime('%H:%M:%S')}] Задача зарегистрирована."],
            "events": [],
            "event_subscribers": [],
            "event_lock": threading.Lock(),
            "error": None,
            "result_url": None,
            "zip_url": None,
            "created_at": time.time(),
            "completed_at": None
        }
        return task_id

    @staticmethod
    def get_task(task_id: str) -> Optional[dict]:
        return active_tasks.get(task_id)

    @staticmethod
    def get_task_status(task_id: str) -> dict:
        task = active_tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        # Return a clean copy without non-serializable objects (locks, queues)
        clean_task = {
            "task_id": task["task_id"],
            "manga": task["manga_name"],
            "manga_name": task["manga_name"],
            "chapter": task["chapter_num"],
            "chapter_num": task["chapter_num"],
            "status": task["status"],
            "stage": task.get("stage", "Queue"),
            "progress": task.get("progress", 0),
            "current_step": task.get("current_step", ""),
            "total_pages": task.get("total_pages", 0),
            "processed_pages": task.get("processed_pages", 0),
            "current_page": task.get("current_page", 0),
            "pages_status": task.get("pages_status", []),
            "logs": list(task.get("logs", [])),
            "error": task.get("error"),
            "result_url": task.get("result_url"),
            "zip_url": task.get("zip_url"),
            "created_at": task.get("created_at"),
            "completed_at": task.get("completed_at")
        }
        if "result" in task and task["result"]:
            clean_task["result"] = task["result"]
        return clean_task

    @staticmethod
    def get_task_events(task_id: str) -> List[dict]:
        task = active_tasks.get(task_id)
        if not task:
            return []
        with task.get("event_lock", threading.Lock()):
            return list(task.get("events", []))

    @staticmethod
    def register_subscriber(task_id: str, loop: Optional[asyncio.AbstractEventLoop] = None) -> Tuple[asyncio.Queue, asyncio.AbstractEventLoop]:
        task = active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

        q = asyncio.Queue()
        with task.get("event_lock", threading.Lock()):
            if "event_subscribers" not in task:
                task["event_subscribers"] = []
            task["event_subscribers"].append((q, loop))
        return q, loop

    @staticmethod
    def unregister_subscriber(task_id: str, queue: asyncio.Queue):
        task = active_tasks.get(task_id)
        if task and "event_lock" in task:
            with task["event_lock"]:
                task["event_subscribers"] = [
                    (q, loop) for q, loop in task.get("event_subscribers", []) if q is not queue
                ]

    @staticmethod
    def emit_task_event(
        task_id: str,
        stage: str,
        progress: int,
        log_msg: str,
        status: str = "processing",
        page: int = 0,
        total_pages: int = 0,
        extra: Optional[dict] = None
    ):
        task = active_tasks.get(task_id)
        if not task:
            return

        task["stage"] = stage
        task["progress"] = progress
        task["current_step"] = log_msg
        task["status"] = status
        if page > 0:
            task["current_page"] = page
            task["processed_pages"] = page
        if total_pages > 0:
            task["total_pages"] = total_pages

        t_str = time.strftime("%H:%M:%S")
        formatted_log = f"[{t_str}] {log_msg}"
        task["logs"].append(formatted_log)
        logger.info(f"[{task_id}] [{stage}] {log_msg} ({progress}%)")

        event_payload = {
            "task_id": task_id,
            "manga": task["manga_name"],
            "chapter": task["chapter_num"],
            "page": page or task.get("current_page", 0),
            "total_pages": total_pages or task.get("total_pages", 0),
            "stage": stage,
            "progress": progress,
            "status": status,
            "log": log_msg,
            "timestamp": time.time()
        }
        if extra:
            event_payload.update(extra)

        lock = task.get("event_lock")
        if lock:
            with lock:
                if "events" not in task:
                    task["events"] = []
                task["events"].append(event_payload)
                subscribers = list(task.get("event_subscribers", []))
                for q, loop in subscribers:
                    try:
                        if loop.is_running():
                            loop.call_soon_threadsafe(q.put_nowait, event_payload)
                        else:
                            q.put_nowait(event_payload)
                    except Exception as ex:
                        logger.debug(f"Subscriber put error: {ex}")

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
    def process_page(
        image_path: str,
        manga_title: str,
        chapter_num: str,
        page_num: int,
        total_pages: int = 1,
        output_root: Optional[str] = None,
        substep_callback: Optional[Callable[[str, str, int], None]] = None
    ) -> dict:
        """
        Processes a single manga page through the full 5-stage pipeline:
        1. RAW Ingestion -> v1 (Original)
        2. 2-Pass OCR & NMS Detection with 1-based sequential IDs
        3. Seamless Per-Pixel Inpainting -> v2 (Cleaned, 0 cv2.rectangle)
        4. Batch LLM Translation (OpenRouter / Gemini / Groq / Glossary)
        5. Mathematical Elliptical Typesetting -> v3 (<=85% bounds, auto-contrast)
        6. Metadata and multi-layer synchronization
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
        if substep_callback:
            substep_callback("RAW Ingestion", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> RAW Ingestion", 1)
        logger.info(f"[Step 1/5] Ingesting RAW image -> {v1_p}")
        raw_img = Image.open(image_path).convert("RGB")
        width, height = raw_img.size
        raw_img.save(v1_p, "WEBP", quality=98)
        raw_img.save(v1_b_p, "WEBP", quality=98)

        # Propagate OCR cache if present
        src_ocr_cache = image_path + ".ocr.json"
        dst_ocr_cache = v1_p + ".ocr.json"
        if os.path.exists(src_ocr_cache) and not os.path.exists(dst_ocr_cache):
            shutil.copy2(src_ocr_cache, dst_ocr_cache)

        # Step 2: 2-Pass OCR & Bubble Detection
        if substep_callback:
            substep_callback("2-Pass OCR", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> 2-Pass OCR & Containment NMS", 2)
        logger.info(f"[Step 2/5] Running 2-Pass OCR & Containment NMS on {v1_p}...")
        clusters = extract_text_and_bubbles(v1_p, use_cache=True)
        for c in clusters:
            c["is_sfx"] = is_sound_effect(c.get("text", ""))
        logger.info(f"Detected {len(clusters)} text clusters.")

        # Step 3: Seamless Per-Pixel Glyph Inpainting -> v2
        if substep_callback:
            substep_callback("Telea Inpaint", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> Telea Inpaint", 3)
        logger.info(f"[Step 3/5] Cleaning speech bubbles -> {v2_p}...")
        process_page_cleaning(v1_p, clusters, output_path=v2_p)
        shutil.copy2(v2_p, v2_b_p)

        # Step 4: Batch LLM Translation
        if substep_callback:
            substep_callback("Batch LLM", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> Batch LLM Translation", 4)

        # Step 5: Typesetting -> v3
        if substep_callback:
            substep_callback("Elliptical Typeset", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> Elliptical Chord Typeset", 5)
        logger.info(f"[Step 4-5/5] Translating & typesetting bubbles -> {v3_p}...")
        process_page_translation(v2_p, clusters, output_path=v3_p, manga_title=clean_title)
        shutil.copy2(v3_p, v3_b_p)

        # Step 6: Update Metadata
        if substep_callback:
            substep_callback("Manifest Sync", f"[{clean_title} Ch.{ch_clean}] [Page {page_num}/{total_pages}] -> Manifest & Layer Sync", 6)

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
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        substep_callback: Optional[Callable[[int, int, str, str, int], None]] = None,
        task_id: Optional[str] = None
    ) -> dict:
        """
        Batch processes all manga pages in an input directory with fine-grained telemetry.
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

            def page_substep_cb(stage_name: str, log_msg: str, substep_idx: int):
                page_fraction = (idx - 1) + (substep_idx / 6.0)
                overall_pct = 10 + int((page_fraction / max(1, total_pages)) * 80)
                if substep_callback:
                    substep_callback(idx, total_pages, stage_name, log_msg, overall_pct)
                elif progress_callback:
                    progress_callback(idx, total_pages, log_msg)

            page_res = MangaPipelineService.process_page(
                image_path=file_path,
                manga_title=manga_title,
                chapter_num=chapter_num,
                page_num=idx,
                total_pages=total_pages,
                output_root=output_root,
                substep_callback=page_substep_cb
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
    def run_pipeline_async(task_id: str):
        _executor.submit(MangaPipelineService._execute_task, task_id)

    @staticmethod
    def _execute_task(task_id: str):
        task = active_tasks.get(task_id)
        if not task:
            return

        manga_name = task["manga_name"]
        chapter_num = str(task["chapter_num"])
        source_url = task.get("source_url")
        temp_input_dir = task.get("options", {}).get("temp_input_dir")

        chapter_folder = f"chapter_{chapter_num}"
        chapter_path = os.path.join(DATA_DIR, manga_name, chapter_folder)
        orig_dir = os.path.join(chapter_path, "v1_original")
        clean_dir = os.path.join(chapter_path, "v2_cleaned")
        trans_dir = os.path.join(chapter_path, "v3_translated")

        ensure_dirs(orig_dir, clean_dir, trans_dir)

        try:
            task["status"] = "processing"
            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Initialization",
                progress=5,
                log_msg=f"[{manga_name} Ch.{chapter_num}] Initializing autonomous pipeline...",
                status="processing"
            )

            # 1. Fetch / Copy pages into v1_original
            if temp_input_dir and os.path.exists(temp_input_dir):
                valid_exts = (".webp", ".png", ".jpg", ".jpeg")
                for fn in os.listdir(temp_input_dir):
                    if fn.lower().endswith(valid_exts) and not fn.endswith(".ocr.json"):
                        shutil.copy2(os.path.join(temp_input_dir, fn), os.path.join(orig_dir, fn))
            elif source_url and not os.listdir(orig_dir):
                MangaPipelineService.emit_task_event(
                    task_id=task_id,
                    stage="Scraping",
                    progress=8,
                    log_msg=f"[{manga_name} Ch.{chapter_num}] Downloading scans from {source_url}...",
                    status="processing"
                )
                scraper = ScraperAgent(output_dir=DATA_DIR)
                import asyncio as aio
                aio.run(scraper.download_chapter_async(manga_name, str(chapter_num)))

            pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])
            if not pages:
                raise Exception(f"No chapter pages found in {orig_dir}. Please upload images or provide a valid source URL.")

            total_pages = len(pages)
            task["total_pages"] = total_pages
            task["pages_status"] = [{"page": p, "step": "Queue", "progress": 0} for p in pages]

            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Ingestion",
                progress=10,
                log_msg=f"[{manga_name} Ch.{chapter_num}] Discovered {total_pages} pages ready for translation.",
                status="processing",
                page=0,
                total_pages=total_pages
            )

            # 2. Process chapter with fine-grained substep callback
            def chapter_substep_cb(cur: int, tot: int, stage_name: str, log_msg: str, progress_pct: int):
                MangaPipelineService.emit_task_event(
                    task_id=task_id,
                    stage=stage_name,
                    progress=progress_pct,
                    log_msg=log_msg,
                    status="processing",
                    page=cur,
                    total_pages=tot
                )
                if cur <= len(task["pages_status"]):
                    task["pages_status"][cur - 1]["step"] = stage_name
                    task["pages_status"][cur - 1]["progress"] = max(0, min(100, int((progress_pct - 10) / 0.8)))
                task["processed_pages"] = cur

            result = MangaPipelineService.process_chapter(
                input_dir=orig_dir,
                manga_title=manga_name,
                chapter_num=chapter_num,
                output_root=DEFAULT_FRONTEND_PUBLIC,
                substep_callback=chapter_substep_cb,
                task_id=task_id
            )

            # 3. Integrity verification & manifest generation
            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Manifest Generation",
                progress=92,
                log_msg=f"[{manga_name} Ch.{chapter_num}] Generating Pipeline Manifest Schema v3.0.0...",
                status="processing",
                page=total_pages,
                total_pages=total_pages
            )
            from chapter_integrity_checker import ChapterIntegrityChecker
            checker = ChapterIntegrityChecker(data_root=DATA_DIR, public_root=DEFAULT_FRONTEND_PUBLIC)
            checker.generate_pipeline_manifest(chapter_path, manga_title=manga_name, chapter_num=chapter_num)

            # 4. Packaging Release ZIP
            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Packaging ZIP",
                progress=95,
                log_msg=f"[{manga_name} Ch.{chapter_num}] Packaging release ZIP archive...",
                status="processing",
                page=total_pages,
                total_pages=total_pages
            )
            checker.create_chapter_zip(chapter_path, manga_title=manga_name, chapter_num=chapter_num)

            # 5. Frontend Public Sync & Global Index
            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Frontend Sync",
                progress=98,
                log_msg=f"[{manga_name} Ch.{chapter_num}] Synchronizing assets to frontend public mirror...",
                status="processing",
                page=total_pages,
                total_pages=total_pages
            )
            checker.sync_to_frontend(manga_title=manga_name)
            update_global_chapters_index(DEFAULT_FRONTEND_PUBLIC)

            zip_url = f"/api/studio/download/{manga_name}/{chapter_num}/v3"
            read_url = f"/reader/{manga_name}?chapter=chapter_{chapter_num}"

            task["status"] = "completed"
            task["progress"] = 100
            task["stage"] = "Complete"
            task["current_step"] = "Chapter completely translated and released!"
            task["result"] = result
            task["result_url"] = read_url
            task["zip_url"] = zip_url
            task["completed_at"] = time.time()

            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Complete",
                progress=100,
                log_msg=f"✓ [{manga_name} Ch.{chapter_num}] Chapter translation complete and release package created!",
                status="completed",
                page=total_pages,
                total_pages=total_pages,
                extra={"zip_url": zip_url, "read_url": read_url}
            )

        except Exception as e:
            logger.exception(f"Pipeline execution failed for task {task_id}:")
            task["status"] = "failed"
            task["stage"] = "Error"
            task["error"] = str(e)
            task["current_step"] = f"Error: {str(e)}"
            MangaPipelineService.emit_task_event(
                task_id=task_id,
                stage="Error",
                progress=task.get("progress", 0),
                log_msg=f"❌ Error: {str(e)}",
                status="error",
                extra={"error": str(e)}
            )
        finally:
            if temp_input_dir and os.path.exists(temp_input_dir):
                shutil.rmtree(temp_input_dir, ignore_errors=True)


# Module-level aliases
process_page = MangaPipelineService.process_page
process_chapter = MangaPipelineService.process_chapter

if __name__ == "__main__":
    print("MangaPipelineService ready.")
