# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
from ocr_engine import extract_text_and_bubbles
from llm_translator import translate_bubbles_with_openrouter

orig_p = os.path.join(os.path.dirname(__file__), "data", "manga", "The_Ultimate_of_All_Ages", "chapter_533", "v1_original", "page_001.webp")
clusters = extract_text_and_bubbles(orig_p, use_cache=True)
b6_text = clusters[5]["text"]

t_map = translate_bubbles_with_openrouter({"bubble_6": b6_text})
val = t_map.get("bubble_6", "")

with open(os.path.join(os.path.dirname(__file__), "debug_chars.txt"), "w", encoding="utf-8") as f:
    f.write(f"val: {val}\n")
    for i, ch in enumerate(val):
        f.write(f"{i}: {repr(ch)} ord={ord(ch)}\n")

print("Exported debug_chars.txt!")
