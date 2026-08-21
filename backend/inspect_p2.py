import os
from PIL import Image

base = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531"
clean_p2 = os.path.join(base, "v2_cleaned", "page_002.webp")
trans_p2 = os.path.join(base, "v3_translated", "page_002.webp")

if os.path.exists(clean_p2):
    img = Image.open(clean_p2)
    crop = img.crop((0, 3800, img.width, 8800))
    crop.save(os.path.join(base, "crop_v2_cleaned_p2.png"))
    print("Saved crop_v2_cleaned_p2.png")
    
if os.path.exists(trans_p2):
    img = Image.open(trans_p2)
    crop = img.crop((0, 3800, img.width, 8800))
    crop.save(os.path.join(base, "crop_v3_trans_p2.png"))
    print("Saved crop_v3_trans_p2.png")
