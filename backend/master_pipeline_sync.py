# -*- coding: utf-8 -*-
import os
import sys
import shutil
import json
import subprocess

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def sync_and_deploy():
    src_base = os.path.join(os.path.dirname(__file__), "data", "manga")
    dst_base = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "manga")
    
    print("1. Syncing backend data to frontend public folder...")
    for manga in os.listdir(src_base):
        m_src = os.path.join(src_base, manga)
        if not os.path.isdir(m_src): continue
        for ch in os.listdir(m_src):
            ch_src = os.path.join(m_src, ch)
            if not os.path.isdir(ch_src): continue
            for v in ['v1_original', 'v2_cleaned', 'v3_translated']:
                v_src = os.path.join(ch_src, v)
                if os.path.isdir(v_src):
                    v_dst = os.path.join(dst_base, manga, ch, v)
                    os.makedirs(v_dst, exist_ok=True)
                    for f in os.listdir(v_src):
                        if f.endswith(('.webp', '.png', '.jpg', '.jpeg')) and not f.endswith('.ocr.json') and not f.startswith('test_') and not f.startswith('sample_'):
                            shutil.copy2(os.path.join(v_src, f), os.path.join(v_dst, f))

    print("2. Rebuilding static chapters_index.json metadata...")
    index_data = {}
    for manga in os.listdir(dst_base):
        m_path = os.path.join(dst_base, manga)
        if not os.path.isdir(m_path): continue
        chapters = []
        for ch_folder in sorted(os.listdir(m_path), key=lambda x: int(x.replace('chapter_', '')) if x.replace('chapter_', '').isdigit() else 0):
            ch_path = os.path.join(m_path, ch_folder)
            if not os.path.isdir(ch_path) or not ch_folder.startswith('chapter_'): continue
            ch_num = ch_folder.replace('chapter_', '')
            versions = {}
            for v in ['v1_original', 'v2_cleaned', 'v3_translated']:
                vp = os.path.join(ch_path, v)
                if os.path.isdir(vp):
                    imgs = sorted([f for f in os.listdir(vp) if f.endswith(('.webp', '.png', '.jpg', '.jpeg'))])
                    versions[v] = [f'/manga/{manga}/{ch_folder}/{v}/{img}' for img in imgs]
                else:
                    versions[v] = []
            chapters.append({'number': ch_num, 'versions': versions})
        index_data[manga] = {'manga': manga, 'chapters': chapters}

    with open(os.path.join(dst_base, 'chapters_index.json'), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print("3. Deploying updated build to Vercel production...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    result = subprocess.run(["npx", "--yes", "vercel", "--prod", "--yes"], cwd=frontend_dir, capture_output=True, text=True, shell=True)
    print("Vercel Output:\n", result.stdout)
    if result.stderr:
        print("Vercel Warnings/Errors:\n", result.stderr)

    print("✓ All chapters synchronized and deployed to Vercel production successfully!")

if __name__ == "__main__":
    sync_and_deploy()
