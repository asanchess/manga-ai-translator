import os, json, hashlib, cv2

manga_root = r"backend/data/manga/The_Ultimate_of_All_Ages"
results = {}

for ch in sorted(os.listdir(manga_root)):
    ch_path = os.path.join(manga_root, ch)
    if not os.path.isdir(ch_path): continue
    
    v1_p = os.path.join(ch_path, "v1_original")
    v2_p = os.path.join(ch_path, "v2_cleaned")
    v3_p = os.path.join(ch_path, "v3_translated")
    
    v1_files = sorted([f for f in os.listdir(v1_p) if f.endswith(".webp")]) if os.path.exists(v1_p) else []
    v2_files = sorted([f for f in os.listdir(v2_p) if f.endswith(".webp")]) if os.path.exists(v2_p) else []
    v3_files = sorted([f for f in os.listdir(v3_p) if f.endswith(".webp")]) if os.path.exists(v3_p) else []
    
    zips = [f for f in os.listdir(ch_path) if f.endswith(".zip")]
    if os.path.exists(v3_p):
        zips += [f for f in os.listdir(v3_p) if f.endswith(".zip")]
    zips = sorted(list(set(zips)))
    
    # Inspect first page dimension if available
    sample_dim = None
    if v1_files:
        sample_img = cv2.imread(os.path.join(v1_p, v1_files[0]))
        if sample_img is not None:
            sample_dim = f"{sample_img.shape[1]}x{sample_img.shape[0]}"
            
    results[ch] = {
        "v1_count": len(v1_files),
        "v2_count": len(v2_files),
        "v3_count": len(v3_files),
        "parity": f"{len(v1_files)}/{len(v2_files)}/{len(v3_files)}",
        "is_complete": (len(v1_files) > 0 and len(v1_files) == len(v2_files) == len(v3_files) and len(zips) > 0),
        "zips": zips,
        "sample_dimension": sample_dim,
        "deficit": len(v1_files) < 8
    }

print(json.dumps(results, indent=2))