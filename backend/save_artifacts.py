import os
from PIL import Image

art_dir = r"C:\Users\asana\.gemini\antigravity-ide\brain\82afacb4-6595-41bc-919d-fd18e11e0577"
base_v3 = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated"

crops = [
    ("page_002.webp", (0, 3800, 800, 7500), "artifact_p2_translated.png"),
    ("page_006.webp", (0, 0, 800, 3500), "artifact_p6_translated.png"),
    ("page_008.webp", (0, 1200, 800, 3200), "artifact_p8_translated.png"),
]

for fname, box, out_name in crops:
    p = os.path.join(base_v3, fname)
    if os.path.exists(p):
        img = Image.open(p)
        c = img.crop(box)
        out_p = os.path.join(art_dir, out_name)
        c.save(out_p)
        print(f"Saved {out_p}")
