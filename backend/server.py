# -*- coding: utf-8 -*-
"""
FastAPI Consolidated Server for Manga AI Translator Studio.
Provides unified REST endpoints, real-time Server-Sent Events (SSE) telemetry streaming,
release ZIP downloads, chapter metadata querying, and static assets mounting.
"""
import os
import sys
import time
import json
import uuid
import zipfile
import shutil
import tempfile
import logging
import asyncio
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
DATA_DIR = os.path.join(BASE_DIR, "data", "manga")
DEFAULT_FRONTEND_PUBLIC = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "public", "manga")
)

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from manga_pipeline_service import (
    MangaPipelineService,
    active_tasks,
    DEFAULT_FRONTEND_PUBLIC,
    DATA_DIR
)
from llm_translator import check_ollama_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] TranslationServer: %(message)s")
logger = logging.getLogger("TranslationServer")

app = FastAPI(
    title="Manga AI Translator Studio API",
    description="Autonomous Manga Translation, Typesetting, Telemetry & Release Server",
    version="4.0.0"
)

# Enable CORS for Next.js reader and studio frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
if os.path.exists(DEFAULT_FRONTEND_PUBLIC):
    app.mount("/manga", StaticFiles(directory=DEFAULT_FRONTEND_PUBLIC), name="manga_public")
else:
    app.mount("/manga", StaticFiles(directory=DATA_DIR), name="manga_data")

app.mount("/data/manga", StaticFiles(directory=DATA_DIR), name="manga_backend_data")

# Pipeline progress state tracker for legacy single-task endpoints
last_task_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class StudioTranslateRequest(BaseModel):
    manga_name: str = "The_Ultimate_of_All_Ages"
    chapter_num: str = "531"
    chapters: Optional[str] = None
    source_url: Optional[str] = None
    source_lang: str = "auto"
    target_lang: str = "ru"
    detector_mode: str = "CTD"
    font_style: str = "auto"


class PipelineRunReq(BaseModel):
    manga: str
    chapter: str


class DeployReq(BaseModel):
    manga: str
    chapter: int


# ---------------------------------------------------------------------------
# Healthcheck Endpoint
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    """Health check endpoint checking Ollama inference status, version, and storage paths."""
    ollama_ok, model_name = check_ollama_available(timeout=1.5)
    return {
        "status": "online",
        "service": "Manga Translation AI Pipeline",
        "version": "4.0.0",
        "storage": "backend/data/manga",
        "data_storage": DATA_DIR,
        "public_storage": DEFAULT_FRONTEND_PUBLIC,
        "ollama": {
            "available": ollama_ok,
            "model": model_name if ollama_ok else None
        }
    }


# ---------------------------------------------------------------------------
# Reader & Studio Manga / Chapter Query Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/chapters/{manga_name}")
@app.get("/api/chapters/{manga_name}/")
def get_chapters(manga_name: str):
    """
    Lists all chapters with page counts and layer availability (v1_original, v2_cleaned, v3_translated).
    """
    clean_title = manga_name.replace(" ", "_")
    manga_dir = os.path.join(DATA_DIR, clean_title)
    
    # Check fallback in public storage if not in backend data
    if not os.path.exists(manga_dir) and os.path.exists(os.path.join(DEFAULT_FRONTEND_PUBLIC, clean_title)):
        manga_dir = os.path.join(DEFAULT_FRONTEND_PUBLIC, clean_title)

    if not os.path.exists(manga_dir):
        return {"error": "Manga not found", "manga": clean_title, "chapters": []}

    def natural_sort_key(s):
        import re
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    chapters = []

    for chapter_folder in sorted(os.listdir(manga_dir), key=natural_sort_key):
        if not chapter_folder.startswith("chapter_"):
            continue
        chapter_number = chapter_folder.replace("chapter_", "")
        chapter_path = os.path.join(manga_dir, chapter_folder)
        if not os.path.isdir(chapter_path):
            continue

        versions = {}
        # Layer mappings
        layer_map = {
            "v1_original": ["v1_original", "v1"],
            "v2_cleaned": ["v2_cleaned", "v2"],
            "v3_translated": ["v3_translated", "v3"]
        }

        for std_layer, possible_dirs in layer_map.items():
            for v_folder in possible_dirs:
                v_path = os.path.join(chapter_path, v_folder)
                if os.path.exists(v_path) and os.path.isdir(v_path):
                    images = sorted([
                        img for img in os.listdir(v_path)
                        if img.lower().endswith(valid_exts) and not img.endswith('.ocr.json')
                    ], key=natural_sort_key)
                    if images:
                        versions[std_layer] = [
                            f"/manga/{clean_title}/{chapter_folder}/{v_folder}/{img}" for img in images
                        ]
                        break

        chapters.append({
            "number": chapter_number,
            "folder": chapter_folder,
            "versions": versions
        })

    def chapter_sort_key(ch):
        num_str = ch["number"]
        return int(num_str) if num_str.isdigit() else num_str

    chapters.sort(key=chapter_sort_key)
    return {"manga": clean_title, "chapters": chapters}


@app.get("/api/studio/mangas")
def list_mangas():
    """
    Lists all manga titles and their available chapter numbers across storage directories.
    """
    def natural_sort_key(s):
        import re
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    discovered: Dict[str, set] = {}

    for root_dir in (DATA_DIR, DEFAULT_FRONTEND_PUBLIC):
        if os.path.exists(root_dir):
            for m in os.listdir(root_dir):
                m_path = os.path.join(root_dir, m)
                if os.path.isdir(m_path) and not m.startswith('.'):
                    if m not in discovered:
                        discovered[m] = set()
                    for c in os.listdir(m_path):
                        if c.startswith("chapter_") and os.path.isdir(os.path.join(m_path, c)):
                            ch_num = c.replace("chapter_", "")
                            discovered[m].add(ch_num)

    mangas = []
    for name, chaps_set in discovered.items():
        sorted_chaps = sorted(list(chaps_set), key=natural_sort_key)
        mangas.append({
            "name": name,
            "title": name.replace("_", " "),
            "chapters": sorted_chaps,
            "total_chapters": len(sorted_chaps)
        })

    mangas.sort(key=lambda x: x["name"])
    return {"mangas": mangas}


# ---------------------------------------------------------------------------
# Studio Translation & Upload Triggers
# ---------------------------------------------------------------------------
@app.post("/api/studio/translate")
def launch_studio_translation(req: StudioTranslateRequest):
    """
    Launch 1-click autonomous chapter translation pipeline (single chapter or batch range).
    """
    global last_task_id
    clean_title = req.manga_name.replace(" ", "_")
    chapter_spec = req.chapters or req.chapter_num

    # Handle batch range e.g. "531-532"
    if "-" in chapter_spec and not req.source_url:
        parts = [p.strip() for p in chapter_spec.split("-")]
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            start_c, end_c = int(parts[0]), int(parts[1])
            created_tasks = []
            for ch in range(start_c, end_c + 1):
                t_id = MangaPipelineService.create_task(
                    manga_name=clean_title,
                    chapter_num=str(ch),
                    options={
                        "source_lang": req.source_lang,
                        "target_lang": req.target_lang,
                        "detector_mode": req.detector_mode,
                        "font_style": req.font_style
                    }
                )
                MangaPipelineService.run_pipeline_async(t_id)
                created_tasks.append(t_id)

            last_task_id = created_tasks[0] if created_tasks else None
            return {
                "status": "started",
                "task_id": last_task_id,
                "task_ids": created_tasks,
                "manga": clean_title,
                "chapters": f"{start_c}-{end_c}",
                "status_url": f"/api/status/{last_task_id}",
                "stream_url": f"/api/pipeline/stream/{last_task_id}"
            }

    ch_clean = str(chapter_spec).replace("chapter_", "")
    task_id = MangaPipelineService.create_task(
        manga_name=clean_title,
        chapter_num=ch_clean,
        source_url=req.source_url,
        options={
            "source_lang": req.source_lang,
            "target_lang": req.target_lang,
            "detector_mode": req.detector_mode,
            "font_style": req.font_style
        }
    )
    last_task_id = task_id
    MangaPipelineService.run_pipeline_async(task_id)

    return {
        "status": "started",
        "task_id": task_id,
        "manga": clean_title,
        "chapter": ch_clean,
        "status_url": f"/api/status/{task_id}",
        "stream_url": f"/api/pipeline/stream/{task_id}"
    }


@app.post("/api/studio/upload")
async def upload_chapter_files(
    manga_name: str = Form("The_Ultimate_of_All_Ages"),
    chapter_num: str = Form("531"),
    auto_start: bool = Form(True),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Handles upload of raw chapter images or ZIP archives and auto-triggers translation pipeline.
    """
    global last_task_id
    clean_title = manga_name.replace(" ", "_")
    ch_clean = str(chapter_num).replace("chapter_", "")
    chapter_folder = f"chapter_{ch_clean}"
    chapter_dir = os.path.join(DATA_DIR, clean_title, chapter_folder, "v1_original")
    os.makedirs(chapter_dir, exist_ok=True)

    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No files or ZIP archive uploaded.")

    saved_files = []
    valid_exts = ('.webp', '.png', '.jpg', '.jpeg')

    for up_file in upload_list:
        if not up_file.filename:
            continue
        fn_lower = up_file.filename.lower()
        if fn_lower.endswith(".zip"):
            temp_zip = os.path.join(chapter_dir, f"temp_{uuid.uuid4().hex[:6]}.zip")
            with open(temp_zip, "wb") as out_f:
                content = await up_file.read()
                out_f.write(content)
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(chapter_dir)
            os.remove(temp_zip)
            for extracted in os.listdir(chapter_dir):
                if extracted.lower().endswith(valid_exts) and not extracted.endswith('.ocr.json'):
                    saved_files.append(extracted)
        elif fn_lower.endswith(valid_exts):
            dest_path = os.path.join(chapter_dir, up_file.filename)
            with open(dest_path, "wb") as out_f:
                content = await up_file.read()
                out_f.write(content)
            saved_files.append(up_file.filename)

    if auto_start:
        task_id = MangaPipelineService.create_task(clean_title, ch_clean)
        last_task_id = task_id
        MangaPipelineService.run_pipeline_async(task_id)
        return {
            "status": "started",
            "task_id": task_id,
            "files_count": len(saved_files),
            "manga": clean_title,
            "chapter": ch_clean,
            "status_url": f"/api/status/{task_id}",
            "stream_url": f"/api/pipeline/stream/{task_id}"
        }

    return {
        "status": "uploaded",
        "files_count": len(saved_files),
        "manga": clean_title,
        "chapter": ch_clean
    }


# ---------------------------------------------------------------------------
# Task Status REST Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/studio/tasks/{task_id}")
@app.get("/api/status/{task_id}")
def get_task_status_endpoint(task_id: str):
    """
    REST polling endpoint returning full task status, telemetry logs, and progress.
    """
    status = MangaPipelineService.get_task_status(task_id)
    if "error" in status and status["error"] == "Task not found":
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return status


# ---------------------------------------------------------------------------
# Real-Time Server-Sent Events (SSE) Telemetry Stream
# ---------------------------------------------------------------------------
@app.get("/api/pipeline/stream/{task_id}")
async def stream_pipeline_telemetry(task_id: str):
    """
    Real-time Server-Sent Events (SSE) endpoint streaming fine-grained sub-step telemetry:
    data: {"task_id": "...", "manga": "...", "chapter": "...", "page": 4, "total_pages": 15, "stage": "Telea Inpaint", "progress": 35, "status": "processing", "log": "[Chapter 532] [Page 4/15] -> Telea Inpaint"}\n\n
    """
    task = MangaPipelineService.get_task(task_id)
    if not task:
        async def not_found_generator():
            err_data = json.dumps({
                "task_id": task_id,
                "status": "error",
                "stage": "Error",
                "error": "Task not found",
                "log": f"Task '{task_id}' was not found in active task registry."
            }, ensure_ascii=False)
            yield f"data: {err_data}\n\n"

        return StreamingResponse(
            not_found_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    async def event_generator():
        queue, loop = MangaPipelineService.register_subscriber(task_id)
        try:
            # 1. Replay historical events
            historical_events = MangaPipelineService.get_task_events(task_id)
            for ev in historical_events:
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                if ev.get("status") in ("completed", "failed", "error"):
                    return

            # 2. Stream live incoming telemetry events
            while True:
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                    if ev.get("status") in ("completed", "failed", "error"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive ping comment
                    yield ": ping\n\n"
                    cur_task = MangaPipelineService.get_task(task_id)
                    if cur_task and cur_task.get("status") in ("completed", "failed"):
                        break
        finally:
            MangaPipelineService.unregister_subscriber(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8"
        }
    )


# ---------------------------------------------------------------------------
# Production ZIP Package & Download Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/studio/download/{manga_name}/{chapter}/{layer}")
@app.get("/api/download/{manga_name}/{chapter}/{layer}")
def download_chapter_zip(manga_name: str, chapter: str, layer: str):
    """
    Downloads chapter as a high-fidelity ZIP archive ({manga}_Chapter_{num}_Russian.zip or layer ZIP).
    """
    clean_title = manga_name.replace(" ", "_")
    ch_clean = str(chapter).replace("chapter_", "")
    chapter_folder = f"chapter_{ch_clean}"

    chapter_dir = os.path.join(DATA_DIR, clean_title, chapter_folder)
    if not os.path.exists(chapter_dir) and os.path.exists(os.path.join(DEFAULT_FRONTEND_PUBLIC, clean_title, chapter_folder)):
        chapter_dir = os.path.join(DEFAULT_FRONTEND_PUBLIC, clean_title, chapter_folder)

    # 1. Preferred release ZIP names
    release_zip_name = f"{clean_title}_Chapter_{ch_clean}_Russian.zip"
    layer_zip_name = f"{clean_title}_{chapter_folder}_{layer}.zip"

    # Check for pre-existing release archive
    for zname in [release_zip_name, layer_zip_name]:
        zpath = os.path.join(chapter_dir, zname)
        if os.path.exists(zpath) and os.path.getsize(zpath) > 0:
            return FileResponse(
                zpath,
                media_type="application/zip",
                filename=release_zip_name if layer in ("v3", "v3_translated", "russian", "all") else layer_zip_name,
                headers={"Content-Disposition": f'attachment; filename="{release_zip_name}"'}
            )

    # 2. Build ZIP on the fly from corresponding layer directory
    layer_subfolder = "v3_translated"
    if layer in ("v1", "v1_original", "raw"):
        layer_subfolder = "v1_original"
    elif layer in ("v2", "v2_cleaned", "cleaned"):
        layer_subfolder = "v2_cleaned"

    layer_path = os.path.join(chapter_dir, layer_subfolder)
    if not os.path.exists(layer_path):
        # Check short name folder (e.g. v3 / v2 / v1)
        short_sub = layer_subfolder.split("_")[0]
        layer_path = os.path.join(chapter_dir, short_sub)

    if not os.path.exists(layer_path):
        raise HTTPException(
            status_code=404,
            detail=f"Chapter translation layer '{layer}' for {clean_title} Ch.{ch_clean} not found."
        )

    valid_exts = ('.webp', '.png', '.jpg', '.jpeg')
    images = sorted([
        f for f in os.listdir(layer_path)
        if f.lower().endswith(valid_exts) and not f.endswith('.ocr.json')
    ])

    if not images:
        raise HTTPException(
            status_code=404,
            detail=f"No image files found in chapter directory {layer_path}."
        )

    target_zip_name = release_zip_name if layer in ("v3", "v3_translated", "russian", "all") else layer_zip_name
    target_zip_path = os.path.join(chapter_dir, target_zip_name)

    with zipfile.ZipFile(target_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img in images:
            img_full = os.path.join(layer_path, img)
            zipf.write(img_full, arcname=img)

    return FileResponse(
        target_zip_path,
        media_type="application/zip",
        filename=target_zip_name,
        headers={"Content-Disposition": f'attachment; filename="{target_zip_name}"'}
    )


# ---------------------------------------------------------------------------
# Legacy & CLI Compatibility Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/translate-chapter")
async def translate_chapter_form_endpoint(
    background_tasks: BackgroundTasks,
    manga_title: str = Form(...),
    chapter_num: str = Form(...),
    source_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Accepts form-data upload or source URL and queues the chapter for processing.
    """
    global last_task_id
    clean_title = manga_title.replace(" ", "_")
    ch_clean = str(chapter_num).replace("chapter_", "")
    temp_dir = None
    saved_images = []
    valid_exts = (".webp", ".png", ".jpg", ".jpeg")

    if file or files:
        temp_dir = tempfile.mkdtemp(prefix=f"manga_upload_")
        upload_list = []
        if files:
            upload_list.extend(files)
        if file:
            upload_list.append(file)

        for up in upload_list:
            if not up.filename:
                continue
            if up.filename.lower().endswith(".zip"):
                zip_path = os.path.join(temp_dir, up.filename)
                with open(zip_path, "wb") as f:
                    content = await up.read()
                    f.write(content)
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(temp_dir)
                os.remove(zip_path)
                for root, _, extracted_files in os.walk(temp_dir):
                    for fn in extracted_files:
                        if fn.lower().endswith(valid_exts):
                            saved_images.append(os.path.join(root, fn))
            elif up.filename.lower().endswith(valid_exts):
                dest_path = os.path.join(temp_dir, up.filename)
                with open(dest_path, "wb") as out_f:
                    content = await up.read()
                    out_f.write(content)
                saved_images.append(dest_path)

    local_orig = os.path.join(DATA_DIR, clean_title, f"chapter_{ch_clean}", "v1_original")
    existing_pages = os.path.exists(local_orig) and len([f for f in os.listdir(local_orig) if f.endswith(valid_exts)]) > 0

    if not saved_images and not source_url and not existing_pages:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail="Please provide uploaded images, a ZIP archive, or a source URL for chapter download."
        )

    options = {"temp_input_dir": temp_dir} if temp_dir else {}
    task_id = MangaPipelineService.create_task(
        manga_name=clean_title,
        chapter_num=ch_clean,
        source_url=source_url,
        options=options
    )
    last_task_id = task_id
    MangaPipelineService.run_pipeline_async(task_id)

    return {
        "task_id": task_id,
        "status": "started",
        "manga": clean_title,
        "chapter": ch_clean,
        "status_url": f"/api/status/{task_id}",
        "stream_url": f"/api/pipeline/stream/{task_id}"
    }


@app.post("/api/pipeline/run")
def run_pipeline_endpoint(req: PipelineRunReq):
    global last_task_id
    clean_title = req.manga.replace(" ", "_")
    ch_clean = str(req.chapter).replace("chapter_", "")
    last_task_id = MangaPipelineService.create_task(clean_title, ch_clean)
    MangaPipelineService.run_pipeline_async(last_task_id)
    return {
        "status": "started",
        "task_id": last_task_id,
        "manga": clean_title,
        "chapter": ch_clean,
        "status_url": f"/api/status/{last_task_id}",
        "stream_url": f"/api/pipeline/stream/{last_task_id}"
    }


@app.post("/api/deploy")
def deploy_manga_chapter(req: DeployReq):
    global last_task_id
    clean_title = req.manga.replace(" ", "_")
    ch_str = str(req.chapter)
    last_task_id = MangaPipelineService.create_task(clean_title, ch_str)
    MangaPipelineService.run_pipeline_async(last_task_id)
    return {
        "status": "started",
        "task_id": last_task_id,
        "manga": clean_title,
        "chapter": ch_str,
        "status_url": f"/api/status/{last_task_id}",
        "stream_url": f"/api/pipeline/stream/{last_task_id}"
    }


@app.get("/api/pipeline/status")
def get_pipeline_status():
    global last_task_id
    if not last_task_id:
        return {
            "status": "idle",
            "current_agent": "Ready",
            "progress": 0,
            "current_page": 0,
            "total_pages": 0,
            "logs": ["Ready for task execution."]
        }
    
    t = MangaPipelineService.get_task_status(last_task_id)
    mapped_status = "running"
    if t.get("status") == "completed":
        mapped_status = "completed"
    elif t.get("status") in ("failed", "error"):
        mapped_status = "error"
        
    return {
        "status": mapped_status,
        "current_agent": t.get("current_step", "Processing"),
        "stage": t.get("stage", "Processing"),
        "progress": t.get("progress", 0),
        "current_page": t.get("processed_pages", 0),
        "total_pages": t.get("total_pages", 0),
        "logs": t.get("logs", [])
    }


# ---------------------------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting Consolidated Manga Translation API Server on http://0.0.0.0:8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
