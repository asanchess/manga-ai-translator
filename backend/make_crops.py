import os
from PIL import Image

base = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated"

crops = [
    ("page_002.webp", (0, 3800, 800, 7500), "check_p2_trans.png"),
    ("page_006.webp", (0, 0, 800, 3500), "check_p6_trans.png"),
    ("page_008.webp", (0, 1000, 800, 4500), "check_p8_trans.png")
]

for fname, box, out_name in crops:
    p = os.path.join(base, fname)
    if os.path.exists(p):
        img = Image.open(p)
        c = img.crop(box)
        c.save(os.path.join(r"c:\Users\asana\OneDrive\Desktop\Manga\backend", out_name))
        print(f"Saved {out_name}")
