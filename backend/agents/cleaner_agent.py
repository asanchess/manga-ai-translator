# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CleanerAgentSeamless")

def get_bubble_background_color(img: np.ndarray, x: int, y: int, w: int, h: int) -> tuple[int, int, int]:
    """
    Precisely samples the background color from perimeter strips outside the text bounding box.
    Returns (B, G, R) background color tuple.
    """
    ih, iw, _ = img.shape
    pad = 8
    strips = []
    
    # Top perimeter strip
    if y - 2 >= 0:
        strips.append(img[max(0, y-pad):max(0, y-1), max(0, x-pad):min(iw, x+w+pad)])
    # Bottom perimeter strip
    if y + h + 1 < ih:
        strips.append(img[min(ih-1, y+h+1):min(ih, y+h+pad), max(0, x-pad):min(iw, x+w+pad)])
    # Left perimeter strip
    if x - 2 >= 0:
        strips.append(img[max(0, y-pad):min(ih, y+h+pad), max(0, x-pad):max(0, x-1)])
    # Right perimeter strip
    if x + w + 1 < iw:
        strips.append(img[max(0, y-pad):min(ih, y+h+pad), min(iw-1, x+w+1):min(iw, x+w+pad)])
        
    perimeter_pixels = []
    for s in strips:
        if s.size > 0:
            perimeter_pixels.append(s.reshape(-1, 3))
            
    if perimeter_pixels:
        all_p = np.vstack(perimeter_pixels)
        med_bgr = np.median(all_p, axis=0).astype(int)
        return int(med_bgr[0]), int(med_bgr[1]), int(med_bgr[2])
        
    # Fallback to interior median
    crop = img[max(0, y):min(ih, y+h), max(0, x):min(iw, x+w)]
    if crop.size > 0:
        med_bgr = np.median(crop.reshape(-1, 3), axis=0).astype(int)
        return int(med_bgr[0]), int(med_bgr[1]), int(med_bgr[2])
        
    return 255, 255, 255

def clean_speech_bubble_seamless(img: np.ndarray, cluster: dict):
    """
    Cleans a single bubble cluster using adaptive background color sampling
    and tight text stroke inpainting. NO rectangular boxes are ever drawn.
    """
    ih, iw, _ = img.shape
    x, y, w, h = cluster["box"]
    
    # Pad ROI by 6px
    pad = 6
    bx1 = max(0, x - pad)
    by1 = max(0, y - pad)
    bx2 = min(iw, x + w + pad)
    by2 = min(ih, y + h + pad)
    
    roi = img[by1:by2, bx1:bx2]
    if roi.size == 0:
        return
        
    bg_b, bg_g, bg_r = get_bubble_background_color(img, x, y, w, h)
    bg_color = np.array([bg_b, bg_g, bg_r], dtype=np.float32)
    bg_lum = 0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b
    is_dark = bg_lum < 90
    
    cluster["is_dark"] = is_dark
    cluster["bg_color"] = (bg_b, bg_g, bg_r)
    
    # Calculate Euclidean color distance from true background color
    diff = np.sqrt(np.sum((roi.astype(np.float32) - bg_color) ** 2, axis=2))
    
    # Text pixels are those differing from background
    text_mask = (diff > 28).astype(np.uint8) * 255
    
    # Clean small noise artifacts
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_small)
    
    # Dilate text mask slightly to cover anti-aliasing edges
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    text_mask = cv2.dilate(text_mask, kernel_dilate, iterations=2)
    
    # Inpaint with TELEA using exact text mask
    inpainted_roi = cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    
    # For solid bubbles (pure white or pure black), blend text area with exact sampled background color
    if bg_lum > 215 or bg_lum < 45:
        solid_fill = np.full_like(roi, (bg_b, bg_g, bg_r))
        mask_3d = np.repeat(text_mask[:, :, np.newaxis] / 255.0, 3, axis=2)
        blended = (inpainted_roi.astype(float) * 0.25 + solid_fill.astype(float) * 0.75).astype(np.uint8)
        inpainted_roi = np.where(mask_3d > 0.5, blended, inpainted_roi)
        
    img[by1:by2, bx1:bx2] = inpainted_roi

def process_page_cleaning(img_path: str, output_path: str, clusters: list) -> str:
    """
    Cleans all speech bubbles on a manga page using background-adaptive seamless inpainting.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = cv2.imread(img_path)
    if img is None:
        return output_path
        
    for cluster in clusters:
        clean_speech_bubble_seamless(img, cluster)
        
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    pil_img.save(output_path, "WEBP", quality=95)
    logger.info(f"Page cleaned successfully -> {output_path}")
    return output_path

if __name__ == "__main__":
    print("CleanerAgentSeamless module loaded successfully.")
