import os
from PIL import Image

src = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v3_translated\page_008.webp"
img = Image.open(src)
crop = img.crop((0, 2400, 800, 4200))
crop.save(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\check_p8_russian_crop.png")
print("Saved check_p8_russian_crop.png")
