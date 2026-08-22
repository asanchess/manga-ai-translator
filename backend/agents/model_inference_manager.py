# -*- coding: utf-8 -*-
"""
ModelInferenceManager — High-Speed ML Inference Singleton & Dual-Executor Pipeline.
Holds EasyOCR reader, manga-ocr (if available), and inpainting engine in memory once at startup.
Coordinates ThreadPoolExecutor for I/O and compute workers for CPU-bound image ops.
"""
import os
import sys
import time
import json
import shutil
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, Callable

import cv2
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ModelInferenceManager: %(message)s")
logger = logging.getLogger("ModelInferenceManager")

# Base directory setup
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

# Import sub-agent routines
from cleaner_agent import process_page_cleaning, clean_speech_bubble_seamless, get_bubble_background_color
from translator_typesetter_agent import process_page_translation
from llm_translator import translate_bubbles_batch, load_manga_glossary
from ocr_engine import extract_text_and_bubbles, is_sound_effect, topological_reading_sort_key


class InpaintingEngine:
    """
    Dedicated high-speed inpainting engine.
    Applies adaptive per-pixel glyph inpainting (Telea/LaMa) with zero solid-box fills.
    """
    def __init__(self, inpaint_radius: int = 4, flags: int = cv2.INPAINT_TELEA):
        self.inpaint_radius = inpaint_radius
        self.flags = flags
        self.kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        self.kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    def clean_bubble(self, img: np.ndarray, cluster: dict):
        clean_speech_bubble_seamless(img, cluster)

    def clean_image(self, img_input: Any, clusters: List[dict], output_path: Optional[str] = None) -> np.ndarray:
        return process_page_cleaning(img_input, clusters, output_path=output_path)


class ModelInferenceManager:
    """
    Thread-safe Singleton holding EasyOCR, manga-ocr, and inpainting engine.
    Dual executors provide parallel I/O and parallel CPU image processing.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, gpu: Optional[bool] = None, io_workers: int = 8, compute_workers: int = 4):
        if ModelInferenceManager._instance is not None:
            raise RuntimeError("ModelInferenceManager is a singleton. Call ModelInferenceManager.get_instance().")
        
        self.gpu = False
        try:
            import torch
            self.gpu = torch.cuda.is_available() if gpu is None else gpu
        except Exception:
            self.gpu = False

        logger.info(f"Initializing ModelInferenceManager (GPU={self.gpu}, io_workers={io_workers}, compute_workers={compute_workers})...")
        
        # 1. Initialize OCR Reader (EasyOCR)
        self._ocr_reader = None
        self._init_ocr_reader()

        # 2. Initialize Manga OCR (if available)
        self._manga_ocr = None
        self._init_manga_ocr()

        # 3. Initialize Inpainting Engine
        self._inpainting_engine = InpaintingEngine(inpaint_radius=4, flags=cv2.INPAINT_TELEA)

        # 4. Dual Executors
        self.io_executor = ThreadPoolExecutor(max_workers=io_workers, thread_name_prefix="MIM_IO")
        self.compute_executor = ThreadPoolExecutor(max_workers=compute_workers, thread_name_prefix="MIM_Compute")

        # 5. Metrics
        self.stats = {
            "pages_processed": 0,
            "total_ocr_time_ms": 0.0,
            "total_cleaning_time_ms": 0.0,
            "total_translation_time_ms": 0.0,
            "total_typesetting_time_ms": 0.0,
            "chapters_completed": 0
        }
        logger.info("ModelInferenceManager initialized successfully.")

    @classmethod
    def get_instance(cls, gpu: Optional[bool] = None, io_workers: int = 8, compute_workers: int = 4) -> "ModelInferenceManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(gpu=gpu, io_workers=io_workers, compute_workers=compute_workers)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Allows resetting instance for unit testing."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.shutdown()
                except Exception:
                    pass
                cls._instance = None

    def _init_ocr_reader(self):
        try:
            import easyocr
            logger.info("Loading EasyOCR Reader model into memory...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=self.gpu)
            logger.info("EasyOCR Reader loaded.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization warning: {e}")
            self._ocr_reader = None

    def _init_manga_ocr(self):
        try:
            import manga_ocr
            logger.info("Loading MangaOCR model into memory...")
            self._manga_ocr = manga_ocr.MangaOcr()
            logger.info("MangaOCR model loaded.")
        except Exception:
            self._manga_ocr = None
            logger.info("manga_ocr not available; using EasyOCR pipeline.")

    def get_ocr_reader(self):
        """Returns the preloaded EasyOCR Reader singleton."""
        if self._ocr_reader is None:
            self._init_ocr_reader()
        return self._ocr_reader

    def get_manga_ocr(self):
        """Returns manga-ocr instance or None."""
        return self._manga_ocr

    def get_inpainting_engine(self) -> InpaintingEngine:
        """Returns the pre-initialized InpaintingEngine."""
        return self._inpainting_engine

    def inpaint_image(self, img_input: Any, clusters: List[dict], output_path: Optional[str] = None) -> np.ndarray:
        """Applies seamless inpainting without solid rectangular fills."""
        return self._inpainting_engine.clean_image(img_input, clusters, output_path=output_path)

    def extract_bubbles(self, image_path: str, use_cache: bool = True) -> List[dict]:
        """Extracts text and speech bubbles using singleton OCR reader."""
        return extract_text_and_bubbles(image_path, use_cache=use_cache)

    def process_page_fast(
        self,
        image_path: str,
        manga_title: str,
        chapter_num: str,
        page_num: int,
        output_root: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fast end-to-end page processing using singleton inference resources:
        1. RAW ingestion -> v1
        2. 2-Pass OCR & Containment NMS
        3. Seamless inpainting -> v2 (Telea, 0 cv2.rectangle fills)
        4. Batch LLM translation with glossary injection
        5. Elliptical typesetting -> v3
        6. Synchronized metadata update
        """
        t0 = time.time()
        clean_title = manga_title.replace(" ", "_")
        ch_clean = str(chapter_num).replace("chapter_", "")
        chapter_folder = f"chapter_{ch_clean}"

        pub_root = output_root or DEFAULT_FRONTEND_PUBLIC
        pub_chapter_dir = os.path.join(pub_root, clean_title, chapter_folder)
        backend_chapter_dir = os.path.join(DATA_DIR, clean_title, chapter_folder)

        v1_pub = os.path.join(pub_chapter_dir, "v1")
        v2_pub = os.path.join(pub_chapter_dir, "v2")
        v3_pub = os.path.join(pub_chapter_dir, "v3")

        v1_backend = os.path.join(backend_chapter_dir, "v1_original")
        v2_backend = os.path.join(backend_chapter_dir, "v2_cleaned")
        v3_backend = os.path.join(backend_chapter_dir, "v3_translated")

        for d in (v1_pub, v2_pub, v3_pub, v1_backend, v2_backend, v3_backend):
            os.makedirs(d, exist_ok=True)

        page_filename = f"page_{page_num:03d}.webp"
        v1_p = os.path.join(v1_pub, page_filename)
        v2_p = os.path.join(v2_pub, page_filename)
        v3_p = os.path.join(v3_pub, page_filename)

        v1_b_p = os.path.join(v1_backend, page_filename)
        v2_b_p = os.path.join(v2_backend, page_filename)
        v3_b_p = os.path.join(v3_backend, page_filename)

        # Stage 1: Ingest RAW image -> v1
        raw_img = Image.open(image_path).convert("RGB")
        width, height = raw_img.size
        raw_img.save(v1_p, "WEBP", quality=98)
        raw_img.save(v1_b_p, "WEBP", quality=98)

        # Propagate OCR cache if exists
        src_ocr_cache = image_path + ".ocr.json"
        dst_ocr_cache = v1_p + ".ocr.json"
        if os.path.exists(src_ocr_cache) and not os.path.exists(dst_ocr_cache):
            shutil.copy2(src_ocr_cache, dst_ocr_cache)

        # Stage 2: OCR
        t_ocr_start = time.time()
        clusters = extract_text_and_bubbles(v1_p, use_cache=True)
        from comic_bubble_detector import get_bubble_detector
        detector = get_bubble_detector()
        for c in clusters:
            c["is_sfx"] = detector.is_sound_effect_or_noise(c.get("text", ""), cluster=c)
        t_ocr_ms = (time.time() - t_ocr_start) * 1000.0

        # Stage 3: Cleaning -> v2
        t_clean_start = time.time()
        self.inpaint_image(v1_p, clusters, output_path=v2_p)
        shutil.copy2(v2_p, v2_b_p)
        t_clean_ms = (time.time() - t_clean_start) * 1000.0

        # Stage 4 & 5: Translation & Typesetting -> v3
        t_trans_start = time.time()
        process_page_translation(v2_p, clusters, output_path=v3_p, manga_title=clean_title)
        shutil.copy2(v3_p, v3_b_p)
        t_trans_ms = (time.time() - t_trans_start) * 1000.0

        total_elapsed_ms = (time.time() - t0) * 1000.0

        with self._lock:
            self.stats["pages_processed"] += 1
            self.stats["total_ocr_time_ms"] += t_ocr_ms
            self.stats["total_cleaning_time_ms"] += t_clean_ms
            self.stats["total_translation_time_ms"] += t_trans_ms

        return {
            "status": "success",
            "page_num": page_num,
            "filename": page_filename,
            "width": width,
            "height": height,
            "bubbles": len(clusters),
            "v1": v1_p,
            "v2": v2_p,
            "v3": v3_p,
            "elapsed_ms": total_elapsed_ms,
            "stage_timings_ms": {
                "ocr": t_ocr_ms,
                "cleaning": t_clean_ms,
                "translation_typesetting": t_trans_ms
            }
        }

    def process_chapter_concurrent(
        self,
        input_dir: str,
        manga_title: str,
        chapter_num: str,
        output_root: Optional[str] = None,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        High-throughput concurrent chapter processor targeting 60-120s full chapter throughput.
        Concurrently executes page pipelines across worker pools.
        """
        t_chapter_start = time.time()
        valid_exts = (".webp", ".png", ".jpg", ".jpeg")
        files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")]

        def natural_sort_key(s):
            import re
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        files.sort(key=natural_sort_key)
        total_pages = len(files)

        if total_pages == 0:
            raise FileNotFoundError(f"No valid image files found in {input_dir}")

        logger.info(f"Starting concurrent chapter processing: {manga_title} Ch.{chapter_num} ({total_pages} pages)...")

        workers = max_workers or min(4, total_pages)
        page_results = [None] * total_pages
        completed_count = 0

        # Execute concurrent page tasks
        futures = {}
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ChapterWorker") as executor:
            for idx, filename in enumerate(files, 1):
                file_path = os.path.join(input_dir, filename)
                fut = executor.submit(
                    self.process_page_fast,
                    file_path,
                    manga_title,
                    chapter_num,
                    idx,
                    output_root
                )
                futures[fut] = (idx, filename)

            for fut in as_completed(futures):
                idx, filename = futures[fut]
                try:
                    res = fut.result()
                    page_results[idx - 1] = res
                    completed_count += 1
                    msg = f"Completed page {idx}/{total_pages} ({filename}) in {res['elapsed_ms']:.1f}ms"
                    if progress_callback:
                        progress_callback(completed_count, total_pages, msg)
                except Exception as e:
                    logger.error(f"Error processing page {idx} ({filename}): {e}")
                    raise

        total_time_sec = time.time() - t_chapter_start
        pages_per_sec = total_pages / max(0.001, total_time_sec)
        logger.info(f"Completed chapter {chapter_num} in {total_time_sec:.2f}s ({pages_per_sec:.2f} pages/sec).")

        with self._lock:
            self.stats["chapters_completed"] += 1

        return {
            "status": "completed",
            "manga": manga_title,
            "chapter": str(chapter_num),
            "total_pages": total_pages,
            "elapsed_seconds": round(total_time_sec, 2),
            "pages_per_second": round(pages_per_sec, 2),
            "pages": page_results
        }

    def shutdown(self):
        """Cleanly shuts down worker executors."""
        try:
            self.io_executor.shutdown(wait=False)
            self.compute_executor.shutdown(wait=False)
        except Exception:
            pass


# Module-level convenience functions
def get_inference_manager(gpu: Optional[bool] = None) -> ModelInferenceManager:
    return ModelInferenceManager.get_instance(gpu=gpu)

def get_ocr_reader():
    return ModelInferenceManager.get_instance().get_ocr_reader()

def get_inpainting_engine():
    return ModelInferenceManager.get_instance().get_inpainting_engine()

def process_chapter_concurrent(input_dir: str, manga_title: str, chapter_num: str, **kwargs):
    return ModelInferenceManager.get_instance().process_chapter_concurrent(
        input_dir, manga_title, chapter_num, **kwargs
    )

if __name__ == "__main__":
    mgr = get_inference_manager()
    print("ModelInferenceManager ready. OCR Reader loaded:", mgr.get_ocr_reader() is not None)
