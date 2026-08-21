import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import clean_speech_bubble, verify_and_refine_cleaning
from translator_typesetter_agent import typeset_bubble, get_best_font

p8_orig = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_008.webp"
clusters = extract_text_and_bubbles(p8_orig)

# 1. Clean
img = cv2.imread(p8_orig)
for c in clusters:
    if c.get("is_sfx", False):
        continue
    x, y, w, h = c["box"]
    # Check if dark bubble
    patch = img[max(0, y):min(img.shape[0], y+h), max(0, x):min(img.shape[1], x+w)]
    luma = np.mean(patch)
    if luma < 100:
        # Dark bubble: Wipe full interior with safe padding
        cv2.rectangle(img, (max(0, x-15), max(0, y-15)), (min(img.shape[1], x+w+15), min(img.shape[0], y+h+15)), (0, 0, 0), -1)
    else:
        clean_speech_bubble(img, c)

img = verify_and_refine_cleaning(img, clusters)
clean_path = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\test_clean_p8.webp"
cv2.imwrite(clean_path, img)

# 2. Translate & Typeset
pil_img = Image.open(clean_path).convert("RGBA")
draw = ImageDraw.Draw(pil_img)

for c in clusters:
    raw = c["text"]
    raw_lower = raw.lower()
    
    trans = ""
    if "yao transformation" in raw_lower:
        trans = "Нет, это не Трансформация Демона! Хотя эффект схож, это состояние куда могущественнее!!"
    elif "coercion" in raw_lower or "ape" in raw_lower or "primordial" in raw_lower:
        trans = "К тому же, устрашающая аура этой обезьяны исходит из Первобытной Эры... Это невероятный Демонический Зверь!"
    elif "head-on" in raw_lower or "clash" in raw_lower:
        trans = "Давай сойдёмся лицом к лицу!!"
    elif "scythe" in raw_lower:
        continue
        
    print(f"Typesetting: '{raw}' -> '{trans}'")
    typeset_bubble(draw, pil_img, c, trans)

final_trans_p8 = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_008.webp"
pil_img.convert("RGB").save(final_trans_p8, "WEBP", quality=94)

# Save test crop
crop = Image.open(final_trans_p8).crop((0, 1200, 800, 2400))
crop.save(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\check_p8_perfect.png")
print("Saved check_p8_perfect.png successfully!")
