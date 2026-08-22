# -*- coding: utf-8 -*-
"""
FastAPI Server for Manga Translation Pipeline
Connected to MangaPipelineService for unified async task management.
"""
import os
import sys
import time
import zipfile
import shutil
import tempfile
import logging
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.manga_pipeline_service import (
    MangaPipelineService,
    DEFAULT_FRONTEND_PUBLIC,
    DATA_DIR
)
from agents.llm_translator import check_ollama_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] TranslationServer: %(message)s")
logger = logging.getLogger("TranslationServer")

app = FastAPI(
    title="Manga Translation AI Service",
    description="Autonomous Manga Translation & Typesetting Pipeline API powered by MangaPipelineService",
    version="2.1.0"
)

# Enable CORS for Next.js reader frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    """Health check endpoint checking Ollama inference status and service state."""
    ollama_ok, model_name = check_ollama_available(timeout=1.5)
    return {
        "status": "online",
        "service": "Manga Translation AI Pipeline",
        "version": "2.1.0",
        "ollama": {
            "available": ollama_ok,
            "model": model_name if ollama_ok else None
        },
        "public_storage": DEFAULT_FRONTEND_PUBLIC,
        "data_storage": DATA_DIR
    }

@app.post("/api/translate-chapter")
async def translate_chapter(
    background_tasks: BackgroundTasks,
    manga_title: str = Form(...),
    chapter_num: str = Form(...),
    source_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Accepts a ZIP archive or multiple image files and queues the chapter for processing via MangaPipelineService.
    """
    valid_exts = (".webp", ".png", ".jpg", ".jpeg")
    temp_dir = None
    saved_images = []

    # If files are uploaded, extract to temp directory
    if file or files:
        task_uuid = tempfile.mkdtemp(prefix=f"manga_upload_")
        temp_dir = task_uuid

        # 1. Handle ZIP Archive
        if file and file.filename.lower().endswith(".zip"):
            zip_path = os.path.join(temp_dir, file.filename)
            with open(zip_path, "wb") as f:
                content = await file.read()
                f.write(content)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(temp_dir)
            os.remove(zip_path)

            for root, _, extracted_files in os.walk(temp_dir):
                for fn in extracted_files:
                    if fn.lower().endswith(valid_exts):
                        src = os.path.join(root, fn)
                        dst = os.path.join(temp_dir, fn)
                        if src != dst:
                            shutil.move(src, dst)
                        saved_images.append(dst)

        # 2. Handle Multiple Files
        elif files:
            for f in files:
                if f.filename.lower().endswith(valid_exts):
                    dest_path = os.path.join(temp_dir, f.filename)
                    with open(dest_path, "wb") as out_f:
                        content = await f.read()
                        out_f.write(content)
                    saved_images.append(dest_path)

        # 3. Handle Single Direct File
        elif file and file.filename.lower().endswith(valid_exts):
            dest_path = os.path.join(temp_dir, file.filename)
            with open(dest_path, "wb") as out_f:
                content = await file.read()
                out_f.write(content)
            saved_images.append(dest_path)

    # If neither files nor source_url provided and no local files exist
    clean_title = manga_title.replace(" ", "_")
    ch_clean = str(chapter_num).replace("chapter_", "")
    local_orig = os.path.join(DATA_DIR, clean_title, f"chapter_{ch_clean}", "v1_original")
    existing_pages = os.path.exists(local_orig) and len([f for f in os.listdir(local_orig) if f.endswith(valid_exts)]) > 0

    if not saved_images and not source_url and not existing_pages:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail="Please provide uploaded images, a ZIP archive, or a source URL for chapter download."
        )

    # Create task in MangaPipelineService
    options = {"temp_input_dir": temp_dir} if temp_dir else {}
    task_id = MangaPipelineService.create_task(
        manga_name=clean_title,
        chapter_num=ch_clean,
        source_url=source_url,
        options=options
    )

    # Launch asynchronously
    MangaPipelineService.run_pipeline_async(task_id)

    return {
        "task_id": task_id,
        "status": "started",
        "manga": clean_title,
        "chapter": ch_clean,
        "status_url": f"/api/status/{task_id}"
    }

@app.get("/api/status/{task_id}")
def get_task_status(task_id: str):
    """Retrieves real-time status, progress percentage, and logs for a task."""
    status = MangaPipelineService.get_task_status(task_id)
    if "error" in status and status["error"] == "Task not found":
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@app.get("/api/studio/download/{manga_name}/{chapter}/{layer}")
def download_chapter_zip(manga_name: str, chapter: str, layer: str):
    """Downloads chapter as a ZIP package."""
    clean_title = manga_name.replace(" ", "_")
    ch_clean = chapter.replace("chapter_", "")
    chapter_folder = f"chapter_{ch_clean}"

    zip_filename = f"{clean_title}_Chapter_{ch_clean}_Russian.zip"
    zip_path = os.path.join(DATA_DIR, clean_title, chapter_folder, zip_filename)

    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")

    # Generate on the fly if needed
    trans_dir = os.path.join(DATA_DIR, clean_title, chapter_folder, "v3_translated")
    if os.path.exists(trans_dir) and os.listdir(trans_dir):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for p in sorted(os.listdir(trans_dir)):
                if p.endswith(".webp"):
                    zipf.write(os.path.join(trans_dir, p), arcname=p)
        return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")

    raise HTTPException(status_code=404, detail="Chapter translation package not found.")

if __name__ == "__main__":
    import uvicorn
    print("Starting Manga Translation API Server on http://0.0.0.0:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
