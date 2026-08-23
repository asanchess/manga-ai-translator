# -*- coding: utf-8 -*-
"""
Manga AI Translator Studio — Unified Command-Line Interface (CLI).
Enables autonomous multi-chapter batch processing, deficit resolution,
concurrent inference, Schema v3.0.0 manifest generation, ZIP packaging,
and frontend synchronization for human power users and AI agents.
"""
import os
import sys
import time
import json
import argparse
import logging
from typing import List, Optional, Dict, Any

# Ensure correct sys.path configuration
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

# Reconfigure stdout for UTF-8 encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] CLI: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("CLI")


def parse_chapter_spec(
    spec: str,
    manga_title: str,
    data_root: str = DATA_DIR,
    public_root: str = DEFAULT_FRONTEND_PUBLIC
) -> List[int]:
    """
    Parses various chapter specification formats into a sorted list of integer chapter numbers.

    Supported formats:
    - 'all': Scans storage directories for all existing chapters.
    - '531-535': Hyphenated continuous integer range (inclusive).
    - '531,532,535': Comma-separated list.
    - '531': Single chapter.
    - 'chapter_531-532, 535': Mixed format with prefixes.
    """
    clean_title = manga_title.replace(" ", "_")
    spec_clean = spec.strip()

    if spec_clean.lower() == "all":
        found_chapters = set()
        # Scan backend data directory
        manga_data_dir = os.path.join(data_root, clean_title)
        if os.path.exists(manga_data_dir):
            for d in os.listdir(manga_data_dir):
                if os.path.isdir(os.path.join(manga_data_dir, d)) and d.startswith("chapter_"):
                    num_str = d.replace("chapter_", "")
                    if num_str.isdigit():
                        found_chapters.add(int(num_str))

        # Also scan frontend public directory if available
        manga_pub_dir = os.path.join(public_root, clean_title)
        if os.path.exists(manga_pub_dir):
            for d in os.listdir(manga_pub_dir):
                if os.path.isdir(os.path.join(manga_pub_dir, d)) and d.startswith("chapter_"):
                    num_str = d.replace("chapter_", "")
                    if num_str.isdigit():
                        found_chapters.add(int(num_str))

        if not found_chapters:
            logger.warning(f"No existing chapters found for '{clean_title}'. Defaulting to [1].")
            return [1]

        return sorted(found_chapters)

    chapter_nums = set()
    parts = spec_clean.split(",")
    for part in parts:
        p = part.strip().replace("chapter_", "").replace("ch_", "").replace("ch", "").strip()
        if not p:
            continue
        if "-" in p:
            range_tokens = p.split("-", 1)
            try:
                start_num = int(range_tokens[0].strip())
                end_num = int(range_tokens[1].strip())
                if start_num <= end_num:
                    chapter_nums.update(range(start_num, end_num + 1))
                else:
                    chapter_nums.update(range(end_num, start_num + 1))
            except ValueError:
                logger.error(f"Invalid chapter range token: '{part}'")
        else:
            try:
                chapter_nums.add(int(p))
            except ValueError:
                logger.error(f"Invalid chapter token: '{part}'")

    if not chapter_nums:
        raise ValueError(f"Could not parse any valid chapters from specification: '{spec}'")

    return sorted(chapter_nums)


def print_banner(
    manga_title: str,
    chapters: List[int],
    workers: int,
    auto_deploy: bool,
    force: bool
):
    """Prints a styled terminal banner for the CLI run."""
    ch_summary = (
        f"{chapters[0]}-{chapters[-1]}"
        if len(chapters) > 3 and chapters == list(range(chapters[0], chapters[-1] + 1))
        else ", ".join(map(str, chapters))
    )
    if len(ch_summary) > 40:
        ch_summary = f"{chapters[0]} ... {chapters[-1]} ({len(chapters)} chapters)"

    print("\n" + "=" * 72)
    print(" ⚡ Manga AI Translator Studio — Turnkey CLI Batch Engine v4.0")
    print("=" * 72)
    print(f" 📖 Manga Title:   {manga_title}")
    print(f" 📑 Chapters:      {ch_summary} (Total: {len(chapters)})")
    print(f" ⚙️  Workers:       {workers} parallel worker threads")
    print(f" 🚀 Auto-Deploy:   {'Enabled (Sync to Frontend)' if auto_deploy else 'Disabled'}")
    print(f" 🔄 Force Reproc:  {'Yes (Overwrite existing layers)' if force else 'No (Use cached if valid)'}")
    print("=" * 72 + "\n")


def run_batch_pipeline(
    title: str,
    chapters_spec: str,
    auto_deploy: bool = True,
    workers: int = 4,
    force: bool = False,
    min_pages: int = 8,
    gpu: Optional[bool] = None,
    data_root: str = DATA_DIR,
    public_root: str = DEFAULT_FRONTEND_PUBLIC
) -> int:
    """
    Executes the end-to-end batch translation pipeline across requested chapters.

    Returns:
        0 on success, 1 on fatal error.
    """
    t_start_batch = time.time()
    clean_title = title.strip().replace(" ", "_")
    manga_dir = os.path.join(data_root, clean_title)
    os.makedirs(manga_dir, exist_ok=True)

    try:
        chapter_list = parse_chapter_spec(
            spec=chapters_spec,
            manga_title=clean_title,
            data_root=data_root,
            public_root=public_root
        )
    except Exception as e:
        logger.error(f"Failed to parse chapter argument '{chapters_spec}': {e}")
        return 1

    print_banner(
        manga_title=clean_title,
        chapters=chapter_list,
        workers=workers,
        auto_deploy=auto_deploy,
        force=force
    )

    # Lazy-load pipeline models and helpers on actual execution
    from agents.manga_pipeline_service import update_global_chapters_index
    from agents.model_inference_manager import ModelInferenceManager
    from agents.chapter_integrity_checker import ChapterIntegrityChecker

    # Initialize Singleton Manager and Integrity Checker
    mgr = ModelInferenceManager.get_instance(gpu=gpu, compute_workers=workers)
    checker = ChapterIntegrityChecker(data_root=data_root, public_root=public_root)

    results_summary = []
    has_failures = False
    valid_exts = (".webp", ".png", ".jpg", ".jpeg")

    for idx, ch_num in enumerate(chapter_list, 1):
        ch_name = f"chapter_{ch_num}"
        ch_dir = os.path.join(manga_dir, ch_name)
        v1_dir = os.path.join(ch_dir, "v1_original")
        v2_dir = os.path.join(ch_dir, "v2_cleaned")
        v3_dir = os.path.join(ch_dir, "v3_translated")
        manifest_path = os.path.join(ch_dir, "pipeline_manifest.json")

        for d in (ch_dir, v1_dir, v2_dir, v3_dir):
            os.makedirs(d, exist_ok=True)

        print(f"\n[{idx}/{len(chapter_list)}] >>> Processing {clean_title} — Chapter {ch_num} <<<")
        t_ch_start = time.time()

        try:
            # 1. Deficit Resolution (Ensure >= min_pages in v1_original)
            existing_v1 = [f for f in os.listdir(v1_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")] if os.path.exists(v1_dir) else []
            if len(existing_v1) < min_pages:
                logger.info(f"Chapter {ch_num} page count ({len(existing_v1)}) < threshold ({min_pages}). Resolving deficits...")
                new_count = checker.resolve_chapter_deficit(ch_dir, manga_title=clean_title, min_pages=min_pages)
                logger.info(f"Chapter {ch_num} now contains {new_count} pages.")

            v1_pages = sorted([f for f in os.listdir(v1_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")])
            v2_pages = sorted([f for f in os.listdir(v2_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")]) if os.path.exists(v2_dir) else []
            v3_pages = sorted([f for f in os.listdir(v3_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")]) if os.path.exists(v3_dir) else []

            if not v1_pages:
                raise FileNotFoundError(f"No source images found in {v1_dir} for Chapter {ch_num}.")

            # 2. Check if inference is needed or can be reused
            release_zip_name = f"{clean_title}_Chapter_{ch_num}_Russian.zip"
            release_zip_path = os.path.join(ch_dir, release_zip_name)
            needs_inference = (
                force
                or len(v1_pages) != len(v3_pages)
                or len(v3_pages) == 0
                or not os.path.exists(manifest_path)
                or not os.path.exists(release_zip_path)
            )

            if needs_inference:
                logger.info(f"Running concurrent ML pipeline for Chapter {ch_num} ({len(v1_pages)} pages) with {workers} workers...")
                proc_res = mgr.process_chapter_concurrent(
                    input_dir=v1_dir,
                    manga_title=clean_title,
                    chapter_num=str(ch_num),
                    output_root=public_root,
                    max_workers=workers
                )
                logger.info(f"ML Pipeline finished in {proc_res.get('elapsed_seconds', 0)}s.")
            else:
                logger.info(f"Chapter {ch_num} layers verified (v1={len(v1_pages)}, v2={len(v2_pages)}, v3={len(v3_pages)}). Skipping re-inference.")

            # 3. Generate Schema v3.0.0 Manifest
            manifest = checker.generate_pipeline_manifest(ch_dir, manga_title=clean_title, chapter_num=str(ch_num))
            
            # 4. Generate Production Release ZIP Packages
            zips = checker.create_chapter_zip(ch_dir, manga_title=clean_title, chapter_num=str(ch_num))
            primary_zip = zips[0] if zips else release_zip_path

            ch_elapsed = time.time() - t_ch_start
            v3_final_count = len([f for f in os.listdir(v3_dir) if f.lower().endswith(valid_exts) and not f.endswith(".ocr.json")])

            results_summary.append({
                "chapter": ch_num,
                "v1_pages": len(v1_pages),
                "v2_pages": len(v2_pages),
                "v3_pages": v3_final_count,
                "manifest": "v3.0.0 [OK]",
                "zip": os.path.basename(primary_zip),
                "elapsed": f"{ch_elapsed:.1f}s",
                "status": "SUCCESS"
            })
            print(f" ✓ Chapter {ch_num} completed successfully ({v3_final_count} translated pages, {ch_elapsed:.1f}s)")

        except Exception as e:
            logger.exception(f"Error processing Chapter {ch_num}: {e}")
            has_failures = True
            ch_elapsed = time.time() - t_ch_start
            results_summary.append({
                "chapter": ch_num,
                "v1_pages": 0,
                "v2_pages": 0,
                "v3_pages": 0,
                "manifest": "ERROR",
                "zip": "N/A",
                "elapsed": f"{ch_elapsed:.1f}s",
                "status": f"FAILED ({str(e)[:30]})"
            })
            print(f" ❌ Chapter {ch_num} FAILED: {e}")

    # 5. Frontend Deployment / Synchronization
    if auto_deploy:
        print("\n" + "-" * 72)
        print(f" 🚀 Synchronizing '{clean_title}' to Frontend ({public_root})...")
        synced_count = checker.sync_to_frontend(manga_title=clean_title)
        update_global_chapters_index(public_root)
        print(f" ✓ Synced {synced_count} chapters to frontend public storage.")
        print(f" ✓ Updated chapters index -> {os.path.join(public_root, 'chapters_index.json')}")
        print("-" * 72)

    # 6. Final Summary Report Table
    total_batch_elapsed = time.time() - t_start_batch
    print("\n" + "=" * 72)
    print(" 📊 BATCH EXECUTION SUMMARY REPORT")
    print("=" * 72)
    header = f"{'Chapter':<10} | {'Pages (v1/v2/v3)':<18} | {'Manifest':<12} | {'Time':<8} | {'Status':<10}"
    print(header)
    print("-" * 72)
    for r in results_summary:
        pages_str = f"{r['v1_pages']}/{r['v2_pages']}/{r['v3_pages']}"
        print(f"{r['chapter']:<10} | {pages_str:<18} | {r['manifest']:<12} | {r['elapsed']:<8} | {r['status']:<10}")
    print("=" * 72)
    print(f" Total Elapsed Time: {total_batch_elapsed:.2f}s | Result: {'ALL PASSED (0 errors)' if not has_failures else 'COMPLETED WITH ERRORS'}\n")

    return 1 if has_failures else 0


def build_parser() -> argparse.ArgumentParser:
    """Builds the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="python backend/cli.py",
        description="Manga AI Translator Studio — Autonomous Multi-Chapter Translation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate chapters 531 and 532 of The Ultimate of All Ages:
  python backend/cli.py --title The_Ultimate_of_All_Ages --chapters 531-532

  # Translate all available chapters with 8 concurrent workers and auto-deploy:
  python backend/cli.py --title The_Ultimate_of_All_Ages --chapters all --workers 8 --auto-deploy

  # Force re-translation of specific comma-separated chapters:
  python backend/cli.py --title "The Ultimate of All Ages" --chapters 531,533,535 --force
        """
    )
    parser.add_argument(
        "--title", "-t",
        required=True,
        type=str,
        help="Manga title (e.g. 'The_Ultimate_of_All_Ages' or 'The Ultimate of All Ages')"
    )
    parser.add_argument(
        "--chapters", "-c",
        required=True,
        type=str,
        help="Chapter range or list to process (e.g. '531-532', '531,532', '531', 'all')"
    )
    parser.add_argument(
        "--auto-deploy",
        dest="auto_deploy",
        action="store_true",
        default=True,
        help="Automatically synchronize completed chapters to frontend public directory (default: True)"
    )
    parser.add_argument(
        "--no-deploy",
        dest="auto_deploy",
        action="store_false",
        help="Disable automatic frontend public synchronization"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of concurrent worker threads for ML page inference (default: 4)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Force re-processing of pages even if v3 translated layers already exist"
    )
    parser.add_argument(
        "--min-pages",
        type=int,
        default=8,
        help="Minimum required page threshold per chapter before deficit resolution (default: 8)"
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        default=None,
        help="Enable GPU acceleration for OCR and inpainting if CUDA is available"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=DATA_DIR,
        help=f"Custom backend data directory (default: {DATA_DIR})"
    )
    parser.add_argument(
        "--public-dir",
        type=str,
        default=DEFAULT_FRONTEND_PUBLIC,
        help=f"Custom frontend public directory (default: {DEFAULT_FRONTEND_PUBLIC})"
    )
    return parser


def main() -> int:
    """Main entrypoint for CLI execution."""
    parser = build_parser()
    args = parser.parse_args()

    return run_batch_pipeline(
        title=args.title,
        chapters_spec=args.chapters,
        auto_deploy=args.auto_deploy,
        workers=args.workers,
        force=args.force,
        min_pages=args.min_pages,
        gpu=args.gpu,
        data_root=args.data_dir,
        public_root=args.public_dir
    )


if __name__ == "__main__":
    sys.exit(main())
