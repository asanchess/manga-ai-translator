import os
import urllib.request

url = "https://cdn.black-clover.org/file/leveling/the-ultimate-of-all-ages/chapter-531/2.webp"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://theultimateofallages.com/'})

out_p2 = r"c:\Users\asana\OneDrive\Desktop\Manga\backend\data\manga\The_Ultimate_of_All_Ages\chapter_531\v1_original\page_002.webp"
try:
    with urllib.request.urlopen(req, timeout=10) as r, open(out_p2, 'wb') as f:
        f.write(r.read())
    print("Successfully downloaded clean RAW page_002.webp from CDN! Size:", os.path.getsize(out_p2))
except Exception as e:
    print("CDN download error:", e)
