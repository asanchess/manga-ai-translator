import os
import json
import glob

base = rbackend/data/manga/The_Ultimate_of_All_Ages
chapters = range(531, 543)
all_ok = True

print(fChecking chapters {min(chapters)} to {max(chapters)} in {base}...)
for ch in chapters:
    ch_dir = os.path.join(base, fchapter_{ch})
    if not os.path.exists(ch_dir):
        print(fFAIL: Chapter {ch} directory missing)
        all_ok = False
        continue
    
    v1_imgs = [f for f in glob.glob(os.path.join(ch_dir, v1, *.*)) if not f.endswith(.json)]
    v2_imgs = [f for f in glob.glob(os.path.join(ch_dir, v2, *.*)) if not f.endswith(.json)]
    v3_imgs = [f for f in glob.glob(os.path.join(ch_dir, v3, *.*)) if not f.endswith(.json)]
    
    manifest_path = os.path.join(ch_dir, pipeline_manifest.json)
    has_manifest = os.path.exists(manifest_path)
    
    zips = glob.glob(os.path.join(ch_dir, *.zip))
    
    manifest_info = {}
    if has_manifest:
        try:
            with open(manifest_path, r, encoding=utf-8) as f:
                manifest_info = json.load(f)
        except Exception as e:
            manifest_info = {error: str(e)}
            
    v1_cnt, v2_cnt, v3_cnt = len(v1_imgs), len(v2_imgs), len(v3_imgs)
    zip_cnt = len(zips)
    
    is_valid = (v1_cnt >= 8 and v2_cnt >= 8 and v3_cnt >= 8 and v1_cnt == v2_cnt == v3_cnt and has_manifest and zip_cnt >= 1)
    if not is_valid:
        all_ok = False
        
    p_ver = manifest_info.get(pipeline_version, N/A)
    status = OK if is_valid else FAIL
    print(fChapter {ch:03d}: v1={v1_cnt}, v2={v2_cnt}, v3={v3_cnt}, manifest={has_manifest} (ver={p_ver}), zips={zip_cnt} -> {status})

print(Overall Chapter Integrity:  + (PASSED if all_ok else FAILED))
