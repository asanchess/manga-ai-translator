import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation, translate_text
from PIL import Image

p8_orig = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_008.webp"
p8_clean = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\test_p8_clean.webp"
p8_trans = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\test_p8_trans.webp"

clusters = extract_text_and_bubbles(p8_orig)
print("Clusters found on Page 8:", len(clusters))
for i, c in enumerate(clusters):
    raw = c['text']
    trans = translate_text(raw, is_sfx=c.get('is_sfx', False))
    print(f"Cluster {i}:")
    print(f"  RAW: '{raw}'")
    print(f"  TRANS: '{trans}'")
    print(f"  BOX: {c['box']}")

process_page_cleaning(p8_orig, p8_clean, clusters)
process_page_translation(p8_clean, p8_trans, clusters)

# Save crop
c_img = Image.open(p8_trans).crop((0, 1000, 800, 4500))
c_img.save(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\test_p8_crop.png")
print("Saved test_p8_crop.png")
