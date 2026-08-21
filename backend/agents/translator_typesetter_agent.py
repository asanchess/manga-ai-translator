# -*- coding: utf-8 -*-
import os
import json
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from llm_translator import translate_bubbles_with_openrouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TypesetterAgent")

# 100% Cyrillic-verified Windows fonts
FONTS = {
    "comic": r"C:\Windows\Fonts\comicbd.ttf",
    "segoe": r"C:\Windows\Fonts\segoeuib.ttf",
    "arial": r"C:\Windows\Fonts\arialbd.ttf",
    "trebuchet": r"C:\Windows\Fonts\trebucbd.ttf",
    "tahoma": r"C:\Windows\Fonts\tahomabd.ttf"
}

def get_best_font(font_key: str, size: int):
    fpath = FONTS.get(font_key, FONTS["comic"])
    if not os.path.exists(fpath):
        fpath = FONTS["arial"]
    try:
        return ImageFont.truetype(fpath, size)
    except Exception:
        return ImageFont.load_default()

def wrap_text_to_bubble(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
    """
    Wraps text into balanced lines to fit inside natural speech bubbles.
    """
    words = text.split()
    if not words:
        return []
        
    dummy_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy_img)
    
    total_len = len(words)
    if total_len <= 3:
        lines = []
        cur = []
        for w in words:
            test = " ".join(cur + [w])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_w:
                cur.append(w)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        return lines

    # Target balanced lines based on word count
    target_lines = 2 if total_len <= 7 else (3 if total_len <= 14 else 4)
    words_per_line = max(1, int(np.ceil(total_len / target_lines)))
    
    lines = []
    for i in range(0, total_len, words_per_line):
        chunk = " ".join(words[i:i+words_per_line])
        bbox = draw.textbbox((0, 0), chunk, font=font)
        if bbox[2] - bbox[0] > max_w:
            sub_words = chunk.split()
            sub_cur = []
            for sw in sub_words:
                test = " ".join(sub_cur + [sw])
                if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                    sub_cur.append(sw)
                else:
                    if sub_cur:
                        lines.append(" ".join(sub_cur))
                    sub_cur = [sw]
            if sub_cur:
                lines.append(" ".join(sub_cur))
        else:
            lines.append(chunk)
            
    return lines

def typeset_bubble(draw: ImageDraw.ImageDraw, pil_img: Image.Image, cluster: dict, translated_text: str):
    if not translated_text or not translated_text.strip():
        return
        
    x, y, w, h = cluster["box"]
    is_sfx = cluster.get("is_sfx", False)
    words = translated_text.split()
    
    # Remove SFX tags if LLM returned them accidentally
    if translated_text.startswith("*[") and translated_text.endswith("]*"):
        translated_text = translated_text[2:-2].strip()
        
    translated_text = re.sub(r'[\ufffd\u25a0\u25a1\u25aa\u25ab]', '', translated_text)
    translated_text = re.sub(r'\[\s*\]', '', translated_text)
    translated_text = re.sub(r'\s+', ' ', translated_text).strip()
        
    # --- Standard Dialogue Bubble Typography ---
    crop_x1 = max(0, x)
    crop_y1 = max(0, y)
    crop_x2 = min(pil_img.width, x + w)
    crop_y2 = min(pil_img.height, y + h)
    
    crop = pil_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    stat = np.array(crop)
    if stat.size > 0:
        avg_luma = np.mean(0.299 * stat[:, :, 0] + 0.587 * stat[:, :, 1] + 0.114 * stat[:, :, 2])
    else:
        avg_luma = 255
        
    is_dark_bubble = avg_luma < 120 or cluster.get("is_dark", False)
    text_color = (255, 255, 255) if is_dark_bubble else (15, 15, 15)
    stroke_color = (0, 0, 0) if is_dark_bubble else (255, 255, 255)
    stroke_w = 2 if is_dark_bubble else 1
    
    is_shout = ("!" in translated_text and len(words) <= 4) or translated_text.isupper()
    font_key = "arial" if is_shout else "comic"
    
    safe_w = max(50, int(w * 0.90))
    safe_h = max(25, int(h * 0.90))
    
    best_font = None
    best_lines = []
    
    # Adaptive font sizing from 24 down to 10
    for font_size in range(24, 9, -1):
        test_font = get_best_font(font_key, font_size)
        wrapped_lines = wrap_text_to_bubble(translated_text, test_font, safe_w)
        if not wrapped_lines:
            continue
            
        line_heights = [draw.textbbox((0, 0), l, font=test_font)[3] - draw.textbbox((0, 0), l, font=test_font)[1] for l in wrapped_lines]
        total_h = sum(line_heights) + (len(wrapped_lines) - 1) * 3
        
        if total_h <= safe_h:
            best_font = test_font
            best_lines = wrapped_lines
            break
            
    if best_font is None:
        best_font = get_best_font(font_key, 11)
        best_lines = wrap_text_to_bubble(translated_text, best_font, safe_w)
        
    if not best_lines:
        return
        
    line_bboxes = [draw.textbbox((0, 0), l, font=best_font) for l in best_lines]
    line_heights = [b[3] - b[1] for b in line_bboxes]
    line_widths = [b[2] - b[0] for b in line_bboxes]
    line_spacing = 3
    total_text_h = sum(line_heights) + (len(best_lines) - 1) * line_spacing
    
    cur_y = y + (h - total_text_h) / 2.0
    
    for i, line in enumerate(best_lines):
        cur_x = x + (w - line_widths[i]) / 2.0
        draw.text(
            (cur_x, cur_y), 
            line, 
            fill=text_color, 
            font=best_font, 
            stroke_width=stroke_w, 
            stroke_fill=stroke_color
        )
        cur_y += line_heights[i] + line_spacing

def process_page_translation(cleaned_img_path: str, output_path: str, clusters: list) -> str:
    """
    Translates all bubbles on the page via LLM and typesets them.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pil_img = Image.open(cleaned_img_path).convert("RGBA")
    draw = ImageDraw.Draw(pil_img)
    
    # 1. Collect all bubbles for batch LLM translation
    bubbles_payload = {}
    valid_clusters = []
    
    for idx, cluster in enumerate(clusters, 1):
        raw_text = cluster.get("text", "").strip()
        if not raw_text:
            continue
        # Filter watermarks
        if "scythescans" in raw_text.lower() or "brought to you by" in raw_text.lower():
            continue
        bubble_key = f"bubble_{idx}"
        cluster["bubble_key"] = bubble_key
        bubbles_payload[bubble_key] = raw_text
        valid_clusters.append(cluster)
        
    logger.info(f"Translating {len(bubbles_payload)} bubbles for {os.path.basename(cleaned_img_path)}...")
    translations_map = translate_bubbles_with_openrouter(bubbles_payload)
    
    # 2. Typeset each bubble
    for cluster in valid_clusters:
        b_key = cluster.get("bubble_key")
        translated_text = translations_map.get(b_key, "")
        typeset_bubble(draw, pil_img, cluster, translated_text)
        
    final_rgb = pil_img.convert("RGB")
    final_rgb.save(output_path, "WEBP", quality=94)
    logger.info(f"Page translated & typeset successfully -> {output_path}")
    return output_path

if __name__ == "__main__":
    print("TypesetterAgent loaded successfully.")
