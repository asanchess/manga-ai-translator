# -*- coding: utf-8 -*-
import os
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from manga_pipeline_service import MangaPipelineService, active_tasks

def run_test():
    print("=== STARTING AUTONOMOUS 1-CLICK PIPELINE FOR CHAPTER 532 ===")
    task_id = MangaPipelineService.create_task(
        manga_name="The_Ultimate_of_All_Ages",
        chapter_num="532",
        source_url="https://theultimateofallages.com/manga/the-ultimate-of-all-ages-chapter-532/"
    )
    
    # Run task synchronously for complete logging
    MangaPipelineService._execute_task(task_id)
    
    task_data = MangaPipelineService.get_task_status(task_id)
    print("=== TASK COMPLETION STATUS ===")
    print(f"Status: {task_data.get('status')}")
    print(f"Progress: {task_data.get('progress')}%")
    print(f"Total Pages: {task_data.get('total_pages')}")
    print(f"Processed Pages: {task_data.get('processed_pages')}")
    print(f"Result URL: {task_data.get('result_url')}")
    print(f"ZIP Download: {task_data.get('zip_download_url')}")

if __name__ == "__main__":
    run_test()
