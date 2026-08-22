import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import cv2
import numpy as np
from PIL import Image, ImageDraw
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import sample_background_color, verify_and_refine_cleaning
from translator_typesetter_agent import typeset_bubble, translate_text

p2_orig = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
clusters = extract_text_and_bubbles(p2_orig)

img = cv2.imread(p2_orig)
for c in clusters:
    if c.get("is_sfx", False):
        continue
    x, y, w, h = c["box"]
    bg_color = sample_background_color(img, x, y, w, h)
    luma = 0.299 * bg_color[2] + 0.587 * bg_color[1] + 0.114 * bg_color[0]
    fill_col = (0, 0, 0) if luma < 100 else (255, 255, 255)
    
    # Wipe the entire bubble area with safe padding
    pad = 12
    cv2.rectangle(img, (max(0, x-pad), max(0, y-pad)), (min(img.shape[1], x+w+pad), min(img.shape[0], y+h+pad)), fill_col, -1)

img = verify_and_refine_cleaning(img, clusters)
clean_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

draw = ImageDraw.Draw(clean_pil)
for c in clusters:
    trans = translate_text(c["text"], is_sfx=c.get("is_sfx", False))
    print(f"Translating: '{c['text']}' -> '{trans}'")
    typeset_bubble(draw, clean_pil, c, trans)

art_dir = r"C:\Users\asana\.gemini\antigravity-ide\brain\82afacb4-6595-41bc-919d-fd18e11e0577"
crop = clean_pil.crop((0, 3800, 800, 7500))
crop.save(os.path.join(art_dir, "artifact_p2_translated.png"))
print("Saved clean artifact_p2_translated.png!")
