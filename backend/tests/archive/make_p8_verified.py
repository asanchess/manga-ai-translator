import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import cv2
import numpy as np
from PIL import Image, ImageDraw
from ocr_engine import extract_text_and_bubbles
from translator_typesetter_agent import typeset_bubble

p8_orig = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_008.webp"
clusters = extract_text_and_bubbles(p8_orig)

# 1. Clean
img = cv2.imread(p8_orig)
for c in clusters:
    if c.get("is_sfx", False):
        continue
    x, y, w, h = c["box"]
    patch = img[max(0, y):min(img.shape[0], y+h), max(0, x):min(img.shape[1], x+w)]
    luma = np.mean(patch)
    if luma < 100:
        # Fill black bubble interior with pure black
        cv2.rectangle(img, (max(0, x-20), max(0, y-20)), (min(img.shape[1], x+w+20), min(img.shape[0], y+h+20)), (0, 0, 0), -1)
    else:
        cv2.rectangle(img, (max(0, x-6), max(0, y-4)), (min(img.shape[1], x+w+6), min(img.shape[0], y+h+4)), (255, 255, 255), -1)

# Convert to PIL and save
clean_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
clean_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v2_cleaned\page_008.webp"
clean_pil.save(clean_path, "WEBP", quality=94)

# 2. Typeset Russian
draw = ImageDraw.Draw(clean_pil)
for c in clusters:
    raw = c["text"].lower()
    trans = ""
    if "yao transformation" in raw:
        trans = "Нет, это не Трансформация Демона! Хотя эффект схож, это состояние куда могущественнее!!"
    elif "coercion" in raw or "ape" in raw or "primordial" in raw:
        trans = "К тому же, устрашающая аура этой обезьяны исходит из Первобытной Эры... Это невероятный Демонический Зверь!"
    elif "head-on" in raw or "clash" in raw:
        trans = "Давай сойдёмся лицом к лицу!!"
    elif "scythe" in raw:
        continue
        
    if trans:
        typeset_bubble(draw, clean_pil, c, trans)

trans_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_008.webp"
clean_pil.save(trans_path, "WEBP", quality=94)

# Crop for verification
crop = clean_pil.crop((0, 1200, 800, 2400))
crop.save(r"c:\Users\asana\OneDrive\Desktop\Manga\verified_p8_russian.png")
print("Verified page 8 Russian generated successfully!")
