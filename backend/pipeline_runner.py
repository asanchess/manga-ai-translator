# -*- coding: utf-8 -*-
"""
End-to-End Manga Translation Pipeline Runner CLI
Lightweight wrapper around MangaPipelineService
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
sys.path.insert(0, os.path.dirname(__file__))

from agents.manga_pipeline_service import (
    MangaPipelineService,
    process_page,
    process_chapter,
    update_global_chapters_index,
    DEFAULT_FRONTEND_PUBLIC
)

def main():
    parser = argparse.ArgumentParser(description="Manga AI Translation Pipeline CLI")
    parser.add_argument("--input", required=True, help="Path to input image file or directory")
    parser.add_argument("--title", required=True, help="Manga title")
    parser.add_argument("--chapter", required=True, help="Chapter number")
    parser.add_argument("--page", type=int, default=1, help="Page number (for single page processing)")
    parser.add_argument("--output", default=None, help="Custom output directory")
    
    args = parser.parse_args()
    
    if os.path.isdir(args.input):
        print(f"Starting batch translation for {args.title} Ch.{args.chapter}...")
        res = MangaPipelineService.process_chapter(
            input_dir=args.input,
            manga_title=args.title,
            chapter_num=args.chapter,
            output_root=args.output
        )
        print("Completed:", res)
    else:
        print(f"Processing page {args.page} of {args.title} Ch.{args.chapter}...")
        res = MangaPipelineService.process_page(
            image_path=args.input,
            manga_title=args.title,
            chapter_num=args.chapter,
            page_num=args.page,
            output_root=args.output
        )
        print("Completed:", res)

if __name__ == "__main__":
    main()
