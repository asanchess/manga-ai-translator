# -*- coding: utf-8 -*-
"""
Typesetter Agent with Elliptical / Diamond Word Wrapping, 
Adaptive Font Sizing (12px - 38px), Safe Oval Padding, and Auto-Contrast.
"""
import os
import re
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from llm_translator import translate_bubbles_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TypesetterAgent")

# Validated Windows Cyrillic-compatible fonts
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

def wrap_text_elliptic(words: list, font: ImageFont.FreeTypeFont, safe_w: int, safe_h: int) -> list:
    """
    Wraps words into balanced lines tailored for elliptical/oval speech bubbles.
    Lines near the top and bottom are shorter, while lines in the center are wider.
    Returns a list of lines if a valid packing is found, or an empty list otherwise.
    """
    if not words:
        return []
        
    dummy_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy_img)
    
    # Calculate representative line height and spacing
    sample_bbox = draw.textbbox((0, 0), "АбвГд123!?", font=font)
    line_h = max(10, sample_bbox[3] - sample_bbox[1])
    line_spacing = max(2, int(0.15 * font.size if hasattr(font, 'size') else line_h * 0.15))
    line_step = line_h + line_spacing
    
    max_lines = int(safe_h // line_step)
    if max_lines < 1:
        return []
        
    a_semi = safe_w / 2.0
    b_semi = safe_h / 2.0
    
    # Try different target line counts starting from most balanced
    for N in range(1, max_lines + 1):
        total_text_h = N * line_step - line_spacing
        if total_text_h > safe_h:
            continue
            
        allowed_widths = []
        for i in range(N):
            # Midpoint y of line i relative to vertical center
            y_mid = - (total_text_h / 2.0) + i * line_step + (line_h / 2.0)
            u = abs(y_mid) / max(1.0, b_semi)
            if u >= 1.0:
                allowed_w = 0
            else:
                # Ellipse horizontal chord length at y_mid
                allowed_w = int(2.0 * a_semi * math.sqrt(1.0 - u * u))
            allowed_widths.append(max(0, allowed_w))
            
        # Attempt to greedily pack words into these N elliptical chords
        words_idx = 0
        candidate_lines = []
        possible = True
        
        for i in range(N):
            cur_line_words = []
            cur_max_w = allowed_widths[i]
            
            while words_idx < len(words):
                test_str = " ".join(cur_line_words + [words[words_idx]])
                bbox = draw.textbbox((0, 0), test_str, font=font)
                test_w = bbox[2] - bbox[0]
                
                if test_w <= cur_max_w:
                    cur_line_words.append(words[words_idx])
                    words_idx += 1
                else:
                    break
                    
            if cur_line_words:
                candidate_lines.append(" ".join(cur_line_words))
            else:
                possible = False
                break
                
        if possible and words_idx == len(words):
            return candidate_lines
            
    return []

def wrap_text_rectangular(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
    """
    Standard rectangular wrap fallback when elliptical packing requires fallback.
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

# Alias for backwards compatibility with tests
wrap_text_to_bounds = wrap_text_rectangular

def typeset_bubble(draw: ImageDraw.ImageDraw, pil_img: Image.Image, cluster: dict, translated_text: str):
    """
    Renders translated text centered inside the cluster's bounding box,
    strictly staying within 85% of bubble oval width and height.
    Applies auto-contrast and stroke based on bubble background luminance.
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
        
    # Determine background luminance for smart auto-contrast
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
    
    # Font style selection
    words = clean_text.split()
    is_shout = ("!" in clean_text and len(words) <= 4) or (clean_text.isupper() and len(words) <= 5)
    font_key = "arial" if is_shout else "comic"
    
    # 85% safe boundary limits (8-10% internal padding from boundary)
    safe_w = max(20, int(w * 0.85))
    safe_h = max(15, int(h * 0.85))
    
    best_font = None
    best_lines = []
    
    # 1. Binary Search for optimal font size in range [12, 38] using elliptical chord wrapping
    low_size = 12
    high_size = 38
    
    while low_size <= high_size:
        mid_size = (low_size + high_size) // 2
        test_font = get_best_font(font_key, mid_size)
        candidate_lines = wrap_text_elliptic(words, test_font, safe_w, safe_h)
        if candidate_lines:
            best_font = test_font
            best_lines = candidate_lines
            low_size = mid_size + 1  # Try finding a larger legible font size
        else:
            high_size = mid_size - 1  # Reduce font size to fit inside oval chords
            
    # 2. If not fitted in [12, 38], try lower range 11px down to 8px
    if best_font is None:
        for font_size in range(11, 7, -1):
            test_font = get_best_font(font_key, font_size)
            candidate_lines = wrap_text_elliptic(words, test_font, safe_w, safe_h)
            if candidate_lines:
                best_font = test_font
                best_lines = candidate_lines
                break
                
    # 3. Final Fallback: standard rectangular wrapping if text is exceptionally long
    if best_font is None:
        best_font = get_best_font(font_key, 8)
        best_lines = wrap_text_rectangular(clean_text, best_font, safe_w)
        
    if not best_lines:
        return
        
    # Determine exact text styling
    font_size_val = best_font.size if hasattr(best_font, 'size') else 14
    line_spacing = max(2, int(0.15 * font_size_val))
    
    if is_dark_bubble:
        text_color = (255, 255, 255)
        stroke_color = (0, 0, 0)
        stroke_w = 2 if font_size_val >= 22 else 1  # ~1.5px average stroke outline
    else:
        text_color = (0, 0, 0)
        stroke_color = (255, 255, 255)
        stroke_w = 0  # Clean black text on light background
        
    line_bboxes = [draw.textbbox((0, 0), l, font=best_font) for l in best_lines]
    line_heights = [b[3] - b[1] for b in line_bboxes]
    line_widths = [b[2] - b[0] for b in line_bboxes]
    total_text_h = sum(line_heights) + (len(best_lines) - 1) * line_spacing
    
    # Perfect vertical centering inside bubble box
    cur_y = y + (h - total_text_h) / 2.0
    
    for i, line in enumerate(best_lines):
        # Perfect horizontal centering for each line (diamond silhouette)
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

def process_page_translation(
    cleaned_img_input, 
    clusters: list, 
    output_path: str = None, 
    manga_title: str = "The_Ultimate_of_All_Ages"
) -> np.ndarray:
    """
    Translates all bubbles via batch LLM translator with glossary injection
    and typesets them centered inside boxes strictly paired by bubble ID.
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
    
    # 1. Prepare batch translation request linked strictly by bubble ID
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
        
    logger.info(f"Translating {len(items_to_translate)} bubbles in batch for '{manga_title}'...")
    translation_results = translate_bubbles_batch(items_to_translate, manga_title=manga_title)
    translations_by_id = {item["id"]: item["translated"] for item in translation_results}
    
    # 2. Render each bubble strictly where dialogue.id == bubble.id
    for cluster in valid_clusters:
        b_id = cluster["id"]
        trans_text = translations_by_id.get(b_id, "")
        typeset_bubble(draw, pil_img, cluster, trans_text)
        
    final_rgb = pil_img.convert("RGB")
    final_bgr = cv2.cvtColor(np.array(final_rgb), cv2.COLOR_RGB2BGR)
    
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_path.lower().endswith(".webp"):
            final_rgb.save(output_path, "WEBP", quality=98)
        else:
            cv2.imwrite(output_path, final_bgr)
        logger.info(f"Page translated & typeset successfully -> {output_path}")
        
    return final_bgr

if __name__ == "__main__":
    print("TypesetterAgent ready.")
