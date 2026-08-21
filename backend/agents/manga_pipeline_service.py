# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import uuid
import zipfile
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root and agents are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
DATA_DIR = os.path.join(BASE_DIR, "data", "manga")

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

from ocr_engine import extract_text_and_bubbles, is_sound_effect
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from qa_inspector_agent import run_qa_inspection
from scraper_agent import ScraperAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] MangaPipeline: %(message)s")
logger = logging.getLogger("MangaPipeline")

# Global active tasks store
active_tasks = {}

class MangaPipelineService:
    @staticmethod
    def create_task(manga_name: str, chapter_num: str, source_url: str = None, options: dict = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        active_tasks[task_id] = {
            "task_id": task_id,
            "manga_name": manga_name,
            "chapter_num": str(chapter_num).replace("chapter_", ""),
            "source_url": source_url,
            "options": options or {},
            "status": "queued",
            "progress": 0,
            "current_step": "Инициализация задачи",
            "total_pages": 0,
            "processed_pages": 0,
            "pages_status": [],
            "logs": [],
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
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(MangaPipelineService._execute_task, task_id)

    @staticmethod
    def _execute_task(task_id: str):
        task = active_tasks.get(task_id)
        if not task:
            return

        manga_name = task["manga_name"]
        chapter_num = task["chapter_num"]
        source_url = task.get("source_url")
        
        chapter_folder = f"chapter_{chapter_num}"
        chapter_path = os.path.join(DATA_DIR, manga_name, chapter_folder)
        orig_dir = os.path.join(chapter_path, "v1_original")
        clean_dir = os.path.join(chapter_path, "v2_cleaned")
        trans_dir = os.path.join(chapter_path, "v3_translated")

        os.makedirs(orig_dir, exist_ok=True)
        os.makedirs(clean_dir, exist_ok=True)
        os.makedirs(trans_dir, exist_ok=True)

        try:
            task["status"] = "processing"
            MangaPipelineService.log(task_id, f"Запуск автономного пайплайна для {manga_name} (Глава {chapter_num})")
            MangaPipelineService.update_progress(task_id, 10, "1/5: Скачивание и проверка страниц главы")

            # 1. Scraping / Fetching if source_url is provided and pages don't exist yet
            pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])
            if not pages and source_url:
                MangaPipelineService.log(task_id, f"Скачивание страниц по ссылке: {source_url}")
                scraper = ScraperAgent(output_dir=DATA_DIR)
                import asyncio
                asyncio.run(scraper.download_chapter_async(manga_name, str(chapter_num)))
                pages = sorted([f for f in os.listdir(orig_dir) if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json')])
                MangaPipelineService.log(task_id, f"Успешно загружено {len(pages)} страниц")
            if not pages:
                raise Exception(f"Страницы главы не найдены в {orig_dir}. Укажите ссылку для скачивания или загрузите файлы.")

            total_pages = len(pages)
            task["total_pages"] = total_pages
            task["pages_status"] = [{"page": p, "step": "в очереди", "progress": 0} for p in pages]
            MangaPipelineService.log(task_id, f"Найдено страниц для обработки: {total_pages}")

            # 2. Process each page through OCR, 5-Pass Cleaning, Translation & Typesetting
            for idx, p in enumerate(pages):
                page_progress_base = 20 + int((idx / total_pages) * 70)
                MangaPipelineService.update_progress(task_id, page_progress_base, f"Обработка страницы [{idx+1}/{total_pages}]: {p}")
                task["pages_status"][idx]["step"] = "распознавание текста"
                MangaPipelineService.log(task_id, f"[{idx+1}/{total_pages}] Детекция текста (Comic Text Detector) на {p}...")

                orig_p = os.path.join(orig_dir, p)
                clean_p = os.path.join(clean_dir, p)
                trans_p = os.path.join(trans_dir, p)

                # Step A: OCR & bubble clustering
                clusters = extract_text_and_bubbles(orig_p, use_cache=True)
                for c in clusters:
                    c["is_sfx"] = is_sound_effect(c.get("text", ""))

                task["pages_status"][idx]["step"] = f"5-Pass клининг ({len(clusters)} баблов)"
                MangaPipelineService.log(task_id, f"[{idx+1}/{total_pages}] Выполнение 5-проходного клининга ({len(clusters)} баблов)...")
                
                # Step B: 5-Pass inpainting & cleaning
                process_page_cleaning(orig_p, clean_p, clusters)

                # Step C: Translation & Typesetting
                task["pages_status"][idx]["step"] = "OpenRouter перевод & тайпсеттинг"
                MangaPipelineService.log(task_id, f"[{idx+1}/{total_pages}] Каскадный перевод и центрированный тайпсеттинг...")
                process_page_translation(clean_p, trans_p, clusters)

                # Step D: QA Inspector
                qa = run_qa_inspection(orig_p, clean_p, trans_p, clusters)
                task["pages_status"][idx]["step"] = f"Готово (QA: {qa.get('qa_grade')})"
                task["pages_status"][idx]["progress"] = 100
                task["processed_pages"] = idx + 1
                MangaPipelineService.log(task_id, f"[{idx+1}/{total_pages}] ✓ Страница {p} готова! Оценка QA: {qa.get('qa_grade')}")

            # 3. Create ZIP archive for download
            MangaPipelineService.update_progress(task_id, 95, "Создание архива главы (ZIP)")
            zip_filename = f"{manga_name}_Chapter_{chapter_num}_Russian.zip"
            zip_path = os.path.join(chapter_path, zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for p in pages:
                    tp = os.path.join(trans_dir, p)
                    if os.path.exists(tp):
                        zipf.write(tp, arcname=p)
            
            MangaPipelineService.log(task_id, f"Архив главы успешно создан: {zip_filename}")

            task["status"] = "completed"
            task["progress"] = 100
            task["current_step"] = "Глава полностью переведена и опубликована!"
            task["result_url"] = f"/reader/{manga_name}?chapter=chapter_{chapter_num}"
            task["zip_download_url"] = f"/api/studio/download/{manga_name}/{chapter_folder}/v3_translated"
            MangaPipelineService.log(task_id, f"🎉 Все {total_pages} страниц успешно переведены и доступны для чтения!")

        except Exception as e:
            logger.exception("Ошибка автономного пайплайна:")
            task["status"] = "failed"
            task["error"] = str(e)
            MangaPipelineService.log(task_id, f"❌ Ошибка: {str(e)}")

    @staticmethod
    def get_task_status(task_id: str) -> dict:
        return active_tasks.get(task_id, {"error": "Task not found"})
