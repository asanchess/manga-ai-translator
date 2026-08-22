import os
import sys
import cv2
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles, is_sound_effect
from cleaner_agent import process_page_cleaning
from translator_typesetter_agent import process_page_translation

def main():
    p2_orig = r"C:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
    p2_clean = r"C:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v2_cleaned\page_002.webp"
    p2_trans = r"C:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_002.webp"
    
    print("Extracting clusters...")
    clusters = extract_text_and_bubbles(p2_orig, use_cache=True)
    for c in clusters:
        c["is_sfx"] = is_sound_effect(c.get("text", ""))

    print("Cleaning...")
    process_page_cleaning(p2_orig, p2_clean, clusters)
    
    print("Translating and Typesetting...")
    process_page_translation(p2_clean, p2_trans, clusters)
    
    print("Done! Check v3_translated.")

if __name__ == "__main__":
    main()
