from PIL import Image

img = Image.open(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\test_clean_p8.webp")
crop = img.crop((0, 1200, 800, 2400))
crop.save(r"c:\Users\asana\OneDrive\Desktop\Manga\test_clean_crop.png")
print("Saved test_clean_crop.png")
