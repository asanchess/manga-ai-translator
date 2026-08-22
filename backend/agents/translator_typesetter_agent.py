# -*- coding: utf-8 -*-
"""
Typesetter Agent with Adaptive Font Sizing, Strict 85% Bounding Box Fitting, and Centering.
"""
import os
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from llm_translator import translate_bubbles_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TypesetterAgent")

# Windows Cyrillic-compatible fonts
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
        return ImageFont.truetype(fpath, max(8, size))
    except Exception:
        return ImageFont.load_default()

def wrap_text_to_bounds(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
    """
    Wraps text into balanced lines such that no line exceeds max_w.
    """
    words = text.split()
    if not words:
        return []
        
    dummy_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy_img)
    
    lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w <= max_w:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
            cur_line = [w]
    if cur_line:
        lines.append(" ".join(cur_line))
        
    return lines

def typeset_bubble(draw: ImageDraw.ImageDraw, pil_img: Image.Image, cluster: dict, translated_text: str):
    """
    Renders translated text centered inside the cluster's bounding box,
    strictly staying within 85% of bubble width and height.
    """
    if not translated_text or not translated_text.strip():
        return
        
    x, y, w, h = cluster["box"]
    if w <= 0 or h <= 0:
        return
        
    # Clean text artifacts
    clean_text = translated_text.strip()
    if clean_text.startswith("*[") and clean_text.endswith("]*"):
        clean_text = clean_text[2:-2].strip()
    clean_text = re.sub(r'[\ufffd\u25a0\u25a1\u25aa\u25ab]', '', clean_text)
    clean_text = re.sub(r'\[\s*\]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    if not clean_text:
        return
        
    # Determine background luminance
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
    
    words = clean_text.split()
    is_shout = ("!" in clean_text and len(words) <= 4) or clean_text.isupper()
    font_key = "arial" if is_shout else "comic"
    
    # 85% safe boundary limits
    safe_w = max(20, int(w * 0.85))
    safe_h = max(15, int(h * 0.85))
    
    best_font = None
    best_lines = []
    
    # Adaptive font sizing from 26 down to 8
    for font_size in range(26, 7, -1):
        test_font = get_best_font(font_key, font_size)
        wrapped_lines = wrap_text_to_bounds(clean_text, test_font, safe_w)
        if not wrapped_lines:
            continue
            
        line_bboxes = [draw.textbbox((0, 0), l, font=test_font) for l in wrapped_lines]
        line_heights = [b[3] - b[1] for b in line_bboxes]
        line_widths = [b[2] - b[0] for b in line_bboxes]
        total_text_h = sum(line_heights) + (len(wrapped_lines) - 1) * 3
        max_line_w = max(line_widths) if line_widths else 0
        
        if total_text_h <= safe_h and max_line_w <= safe_w:
            best_font = test_font
            best_lines = wrapped_lines
            break
            
    if best_font is None:
        best_font = get_best_font(font_key, 8)
        best_lines = wrap_text_to_bounds(clean_text, best_font, safe_w)
        
    if not best_lines:
        return
        
    line_bboxes = [draw.textbbox((0, 0), l, font=best_font) for l in best_lines]
    line_heights = [b[3] - b[1] for b in line_bboxes]
    line_widths = [b[2] - b[0] for b in line_bboxes]
    line_spacing = 3
    total_text_h = sum(line_heights) + (len(best_lines) - 1) * line_spacing
    
    # Perfect vertical and horizontal centering
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

def process_page_translation(cleaned_img_input, clusters: list, output_path: str = None) -> np.ndarray:
    """
    Translates all bubbles via batch LLM translator and typesets them centered inside boxes.
    Returns BGR numpy array and optionally saves to output_path.
    """
    if isinstance(cleaned_img_input, str):
        cv_img = cv2.imread(cleaned_img_input)
        if cv_img is None:
            raise FileNotFoundError(f"Cannot read image: {cleaned_img_input}")
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
    elif isinstance(cleaned_img_input, np.ndarray):
        rgb = cv2.cvtColor(cleaned_img_input, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
    else:
        raise ValueError("cleaned_img_input must be file path or np.ndarray")
        
    draw = ImageDraw.Draw(pil_img)
    
    # 1. Prepare batch translation request linked by bubble ID
    items_to_translate = []
    valid_clusters = []
    
    for cluster in clusters:
        raw_text = cluster.get("text", "").strip()
        if not raw_text:
            continue
        # Skip watermarks
        if "scythescans" in raw_text.lower() or "brought to you by" in raw_text.lower():
            continue
        b_id = cluster["id"]
        items_to_translate.append({"id": b_id, "text": raw_text})
        valid_clusters.append(cluster)
        
    logger.info(f"Translating {len(items_to_translate)} bubbles in batch...")
    translation_results = translate_bubbles_batch(items_to_translate)
    translations_by_id = {item["id"]: item["translated"] for item in translation_results}
    
    # 2. Render each bubble
    for cluster in valid_clusters:
        b_id = cluster["id"]
        trans_text = translations_by_id.get(b_id, "")
        typeset_bubble(draw, pil_img, cluster, trans_text)
        
    final_rgb = pil_img.convert("RGB")
    final_bgr = cv2.cvtColor(np.array(final_rgb), cv2.COLOR_RGB2BGR)
    
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_path.lower().endswith(".webp"):
            final_rgb.save(output_path, "WEBP", quality=95)
        else:
            cv2.imwrite(output_path, final_bgr)
        logger.info(f"Page translated & typeset successfully -> {output_path}")
        
    return final_bgr

if __name__ == "__main__":
    print("TypesetterAgent ready.")
