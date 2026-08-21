import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation
from PIL import Image

p2_orig = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
p2_clean = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v2_cleaned\page_002.webp"
p2_trans = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_002.webp"

clusters = extract_text_and_bubbles(p2_orig)
process_page_cleaning(p2_orig, p2_clean, clusters)
process_page_translation(p2_clean, p2_trans, clusters)

# Save verification crop to brain artifacts dir
art_dir = r"C:\Users\asana\.gemini\antigravity-ide\brain\82afacb4-6595-41bc-919d-fd18e11e0577"
img = Image.open(p2_trans)
crop = img.crop((0, 3800, 800, 7500))
out_p = os.path.join(art_dir, "artifact_p2_translated.png")
crop.save(out_p)
print("Saved final artifact_p2_translated.png successfully!")
