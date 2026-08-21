import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

fonts_dir = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\assets\fonts"
os.makedirs(fonts_dir, exist_ok=True)

# Copy or test system fonts
sys_fonts = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\comicbd.ttf",
    r"C:\Windows\Fonts\impact.ttf"
]

test_text = "МАСТЕР, БУДЬТЕ ОСТОРОЖНЫ!\nМЫ НЕ ЗНАЕМ, ЧТО ОНИ ЗАДУМАЛИ!"

for fpath in sys_fonts:
    if os.path.exists(fpath):
        fname = os.path.basename(fpath)
        font = ImageFont.truetype(fpath, 28)
        img = Image.new("RGB", (500, 150), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.multiline_text((20, 20), test_text, fill=(0, 0, 0), font=font, align="center")
        out_path = os.path.join(fonts_dir, f"test_{fname}.png")
        img.save(out_path)
        print(f"Rendered test font with {fname} -> {out_path}")
