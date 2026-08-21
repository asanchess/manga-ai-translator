# -*- coding: utf-8 -*-
"""
FastAPI Server for Manga Translation Pipeline
Provides async background translation endpoints and progress tracking.
"""

import os
import sys
import uuid
import time
import zipfile
import shutil
import tempfile
import logging
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure agents folder is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
sys.path.insert(0, os.path.dirname(__file__))

from pipeline_runner import process_chapter, process_page, DEFAULT_FRONTEND_PUBLIC
from agents.llm_translator import check_ollama_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TranslationServer")

app = FastAPI(
    title="Manga Translation AI Service",
    description="Autonomous 5-Agent SOTA Manga Translation & Typesetting Pipeline API",
    version="2.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task state registry
tasks = {}

def run_translation_task(task_id: str, temp_dir: str, manga_title: str, chapter_num: str):
    """Executes the chapter processing in the background and updates the task state."""
    task = tasks[task_id]
    task["status"] = "running"
    task["start_time"] = time.time()
    
    def log_message(msg: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        task["logs"].append(entry)
        logger.info(f"[{task_id}] {msg}")

    def progress_callback(cur_page: int, total_pages: int, message: str):
        task["current_page"] = cur_page
        task["total_pages"] = total_pages
        task["progress"] = int((cur_page / max(1, total_pages)) * 100)
        log_message(message)

    try:
        log_message(f"Starting pipeline for '{manga_title}' Chapter {chapter_num}...")
        result = process_chapter(
            input_dir=temp_dir,
            manga_title=manga_title,
            chapter_num=chapter_num,
            output_root=DEFAULT_FRONTEND_PUBLIC,
            progress_callback=progress_callback
        )
        task["status"] = "completed"
        task["progress"] = 100
        task["result"] = result
        log_message("✓ All pages processed and published successfully!")
    except Exception as e:
        logger.exception(f"Error during translation task {task_id}: {e}")
        task["status"] = "error"
        task["error"] = str(e)
        log_message(f"❌ Pipeline failed: {e}")
    finally:
        # Clean up temporary upload directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

@app.get("/api/health")
def health():
    ollama_ok, model_name = check_ollama_available(timeout=1.5)
    return {
        "status": "online",
        "service": "Manga Translation AI Pipeline",
        "ollama": {
            "available": ollama_ok,
            "model": model_name if ollama_ok else None
        },
        "public_storage": DEFAULT_FRONTEND_PUBLIC
    }

@app.post("/api/translate-chapter")
async def translate_chapter(
    background_tasks: BackgroundTasks,
    manga_title: str = Form(...),
    chapter_num: str = Form(...),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Accepts a ZIP archive or multiple image files and queues the chapter for processing.
    """
    if not file and not files:
        raise HTTPException(status_code=400, detail="Please upload either a ZIP file or image files.")

    task_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp(prefix=f"manga_{task_id}_")

    valid_exts = (".webp", ".png", ".jpg", ".jpeg")
    saved_images = []

    # 1. Handle ZIP Archive
    if file and file.filename.lower().endswith(".zip"):
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp_dir)
        os.remove(zip_path)
        
        # Collect extracted images (handling subfolders if any)
        for root, _, extracted_files in os.walk(temp_dir):
            for fn in extracted_files:
                if fn.lower().endswith(valid_exts):
                    src = os.path.join(root, fn)
                    dst = os.path.join(temp_dir, fn)
                    if src != dst:
                        shutil.move(src, dst)
                    saved_images.append(dst)

    # 2. Handle Multiple Uploaded Images
    elif files:
        for f in files:
            if f.filename.lower().endswith(valid_exts):
                dest_path = os.path.join(temp_dir, f.filename)
                with open(dest_path, "wb") as out_f:
                    content = await f.read()
                    out_f.write(content)
                saved_images.append(dest_path)

    # 3. Handle Single Direct Image
    elif file and file.filename.lower().endswith(valid_exts):
        dest_path = os.path.join(temp_dir, file.filename)
        with open(dest_path, "wb") as out_f:
            content = await file.read()
            out_f.write(content)
        saved_images.append(dest_path)

    if not saved_images:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No valid images (.webp, .png, .jpg) found in upload.")

    total_pages = len(saved_images)
    
    # Initialize task status
    tasks[task_id] = {
        "task_id": task_id,
        "manga": manga_title,
        "chapter": str(chapter_num),
        "status": "queued",
        "progress": 0,
        "current_page": 0,
        "total_pages": total_pages,
        "logs": [f"[{time.strftime('%H:%M:%S')}] Task queued with {total_pages} pages."],
        "created_at": time.time(),
        "result": None,
        "error": None
    }

    # Dispatch to background task
    background_tasks.add_task(run_translation_task, task_id, temp_dir, manga_title, chapter_num)

    return {
        "task_id": task_id,
        "status": "started",
        "manga": manga_title,
        "chapter": str(chapter_num),
        "total_pages": total_pages,
        "status_url": f"/api/status/{task_id}"
    }

@app.get("/api/status/{task_id}")
def get_task_status(task_id: str):
    """Retrieves real-time status, progress percentage, and logs for a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    print("Starting Manga Translation API Server on http://0.0.0.0:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
