# -*- coding: utf-8 -*-
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import time
import zipfile
import shutil
import uuid

# Ensure agents dir in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from manga_pipeline_service import MangaPipelineService, active_tasks

app = FastAPI(title="Manga 5-Agent Scanlation API & AI Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_dir = os.path.join(os.path.dirname(__file__), "data", "manga")
os.makedirs(data_dir, exist_ok=True)

# Serve the manga data folder statically
app.mount("/manga", StaticFiles(directory=data_dir), name="manga")

# Pipeline progress state tracker
last_task_id = None

class StudioTranslateRequest(BaseModel):
    manga_name: str = "The_Ultimate_of_All_Ages"
    chapter_num: str = "531"
    source_url: Optional[str] = None
    source_lang: str = "auto"
    target_lang: str = "ru"
    detector_mode: str = "CTD"
    font_style: str = "auto"

@app.get("/api/chapters/{manga_name}")
def get_chapters(manga_name: str):
    manga_dir = os.path.join(data_dir, manga_name)
    if not os.path.exists(manga_dir):
        return {"error": "Manga not found"}
        
    chapters = []
    for chapter_folder in sorted(os.listdir(manga_dir)):
        if chapter_folder.startswith("chapter_"):
            chapter_number = chapter_folder.replace("chapter_", "")
            versions = {}
            chapter_path = os.path.join(manga_dir, chapter_folder)
            for v_folder in ["v1_original", "v2_cleaned", "v3_translated"]:
                v_path = os.path.join(chapter_path, v_folder)
                if os.path.exists(v_path):
                    images = sorted([img for img in os.listdir(v_path) if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and not img.endswith('.ocr.json')])
                    versions[v_folder] = [f"/manga/{manga_name}/{chapter_folder}/{v_folder}/{img}" for img in images]
                    
            chapters.append({
                "number": chapter_number,
                "versions": versions
            })
            
    return {"manga": manga_name, "chapters": chapters}

@app.get("/api/studio/mangas")
def list_mangas():
    mangas = []
    if os.path.exists(data_dir):
        for m in os.listdir(data_dir):
            m_path = os.path.join(data_dir, m)
            if os.path.isdir(m_path):
                chaps = [c.replace("chapter_", "") for c in os.listdir(m_path) if c.startswith("chapter_") and os.path.isdir(os.path.join(m_path, c))]
                mangas.append({"name": m, "chapters": chaps})
    return {"mangas": mangas}

@app.post("/api/studio/translate")
def launch_studio_translation(req: StudioTranslateRequest):
    """
    Launch 1-click autonomous chapter translation pipeline
    """
    task_id = MangaPipelineService.create_task(
        manga_name=req.manga_name,
        chapter_num=req.chapter_num,
        source_url=req.source_url,
        options={
            "source_lang": req.source_lang,
            "target_lang": req.target_lang,
            "detector_mode": req.detector_mode,
            "font_style": req.font_style
        }
    )
    MangaPipelineService.run_pipeline_async(task_id)
    return {
        "status": "started",
        "task_id": task_id,
        "manga": req.manga_name,
        "chapter": req.chapter_num
    }

@app.post("/api/studio/upload")
async def upload_chapter_files(
    manga_name: str = Form("The_Ultimate_of_All_Ages"),
    chapter_num: str = Form("531"),
    auto_start: bool = Form(True),
    files: List[UploadFile] = File(...)
):
    """
    Upload images or ZIP file and auto-trigger translation pipeline
    """
    chapter_folder = f"chapter_{chapter_num}"
    chapter_dir = os.path.join(data_dir, manga_name, chapter_folder, "v1_original")
    os.makedirs(chapter_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        if file.filename.endswith(".zip"):
            temp_zip = os.path.join(chapter_dir, f"temp_{uuid.uuid4().hex[:6]}.zip")
            with open(temp_zip, "wb") as f:
                content = await file.read()
                f.write(content)
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(chapter_dir)
            os.remove(temp_zip)
        else:
            file_path = os.path.join(chapter_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_files.append(file.filename)
            
    if auto_start:
        task_id = MangaPipelineService.create_task(manga_name, chapter_num)
        MangaPipelineService.run_pipeline_async(task_id)
        return {"status": "started", "task_id": task_id, "files_count": len(saved_files)}
    
    return {"status": "uploaded", "files_count": len(saved_files)}

@app.get("/api/studio/tasks/{task_id}")
def get_studio_task_status(task_id: str):
    return MangaPipelineService.get_task_status(task_id)

@app.get("/api/studio/download/{manga_name}/{chapter_folder}/{version}")
def download_chapter_zip(manga_name: str, chapter_folder: str, version: str):
    target_dir = os.path.join(data_dir, manga_name, chapter_folder, version)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Chapter version folder not found")
        
    zip_path = os.path.join(data_dir, manga_name, chapter_folder, f"{manga_name}_{chapter_folder}_{version}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_dir):
            for file in sorted(files):
                if file.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')) and not file.endswith('.ocr.json'):
                    zipf.write(os.path.join(root, file), arcname=file)
                    
    return FileResponse(zip_path, media_type="application/zip", filename=f"{manga_name}_{chapter_folder}_{version}.zip")

class PipelineRunReq(BaseModel):
    manga: str
    chapter: str

@app.post("/api/pipeline/run")
def run_pipeline_endpoint(req: PipelineRunReq):
    global last_task_id
    last_task_id = MangaPipelineService.create_task(req.manga, req.chapter)
    MangaPipelineService.run_pipeline_async(last_task_id)
    return {"status": "started", "task_id": last_task_id}

class DeployReq(BaseModel):
    manga: str
    chapter: int

@app.post("/api/deploy")
def deploy_manga_chapter(req: DeployReq):
    global last_task_id
    # We would normally trigger a scraper here to download the raw images.
    # Since we are mocking the scraper, we'll just create the task and run the pipeline
    # with the chapter number converted to string.
    chapter_str = str(req.chapter)
    last_task_id = MangaPipelineService.create_task(req.manga.replace(" ", "_"), chapter_str)
    MangaPipelineService.run_pipeline_async(last_task_id)
    return {"status": "started", "task_id": last_task_id}

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
            "logs": ["Ожидание запуска..."]
        }
    
    t = MangaPipelineService.get_task_status(last_task_id)
    # Map back to the UI expected status shape
    mapped_status = "running"
    if t.get("status") == "completed":
        mapped_status = "completed"
    elif t.get("status") == "failed":
        mapped_status = "error"
        
    return {
        "status": mapped_status,
        "current_agent": t.get("current_step", "Processing"),
        "progress": t.get("progress", 0),
        "current_page": t.get("processed_pages", 0),
        "total_pages": t.get("total_pages", 0),
        "logs": t.get("logs", [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
