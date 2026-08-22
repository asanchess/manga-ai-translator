# -*- coding: utf-8 -*-
"""
Cleaner Agent with Adaptive Per-Pixel Glyph Inpainting (Telea).
Replaces text with seamless background inpainting without solid rectangle fills.
"""
import os
import cv2
import numpy as np
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CleanerAgentSeamless")

def get_bubble_background_color(img: np.ndarray, x: int, y: int, w: int, h: int) -> tuple[int, int, int]:
    """
    Samples background color from perimeter strips outside the text bounding box.
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
    Cleans a single bubble cluster using adaptive per-pixel glyph inpainting.
    NO solid rectangles are drawn.
    """
    ih, iw, _ = img.shape
    x, y, w, h = cluster["box"]
    
    pad = 6
    bx1 = max(0, x - pad)
    by1 = max(0, y - pad)
    bx2 = min(iw, x + w + pad)
    by2 = min(ih, y + h + pad)
    
    roi = img[by1:by2, bx1:bx2]
    if roi.size == 0 or roi.shape[0] < 2 or roi.shape[1] < 2:
        return
        
    bg_b, bg_g, bg_r = get_bubble_background_color(img, x, y, w, h)
    bg_color = np.array([bg_b, bg_g, bg_r], dtype=np.float32)
    bg_lum = 0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b
    is_dark = bg_lum < 90
    
    cluster["is_dark"] = is_dark
    cluster["bg_color"] = (bg_b, bg_g, bg_r)
    
    # 1. Color Euclidean distance from background
    color_diff = np.sqrt(np.sum((roi.astype(np.float32) - bg_color) ** 2, axis=2))
    
    # 2. Otsu thresholding on grayscale ROI
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    if is_dark:
        # Light text on dark background
        _, otsu_mask = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # Dark text on light background
        _, otsu_mask = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
    # Combine Otsu with color distance
    dist_mask = (color_diff > 25).astype(np.uint8) * 255
    text_mask = cv2.bitwise_and(otsu_mask, dist_mask)
    
    # Clean small noise artifacts
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_small)
    
    # Dilate text mask slightly to cover font antialiasing contours
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    text_mask = cv2.dilate(text_mask, kernel_dilate, iterations=2)
    
    if np.count_nonzero(text_mask) == 0:
        # Fallback if no text mask detected: use distance mask
        text_mask = cv2.dilate((color_diff > 20).astype(np.uint8) * 255, kernel_dilate, iterations=1)

    # Safety: If text mask covers > 50% of the ROI, Otsu captured background; clamp with stricter threshold
    if text_mask.size > 0 and (np.count_nonzero(text_mask) / text_mask.size) > 0.50:
        dist_mask_strict = (color_diff > 45).astype(np.uint8) * 255
        text_mask = cv2.bitwise_and(otsu_mask, dist_mask_strict)
        text_mask = cv2.dilate(text_mask, kernel_dilate, iterations=1)

    # Safety: Keep 2px outer boundary of ROI untouched to guarantee genuine Telea inpainting reference pixels
    if text_mask.shape[0] > 4 and text_mask.shape[1] > 4:
        text_mask[0:2, :] = 0
        text_mask[-2:, :] = 0
        text_mask[:, 0:2] = 0
        text_mask[:, -2:] = 0
        
    if np.count_nonzero(text_mask) > 0:
        inpainted_roi = cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
        img[by1:by2, bx1:bx2] = inpainted_roi

def process_page_cleaning(img_input, clusters: list, output_path: str = None) -> np.ndarray:
    """
    Cleans all speech bubbles on a page and returns the cleaned BGR numpy array.
    Optionally saves the image to output_path if specified.
    """
    if isinstance(img_input, str):
        img = cv2.imread(img_input)
        if img is None:
            raise FileNotFoundError(f"Cannot read image file: {img_input}")
    elif isinstance(img_input, np.ndarray):
        img = img_input.copy()
    else:
        raise ValueError("img_input must be file path or numpy.ndarray")
        
    for cluster in clusters:
        clean_speech_bubble_seamless(img, cluster)
        
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_path.lower().endswith(".webp"):
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img.save(output_path, "WEBP", quality=98)
        else:
            cv2.imwrite(output_path, img)
        logger.info(f"Page cleaned successfully -> {output_path}")
        
    return img

if __name__ == "__main__":
    print("CleanerAgentSeamless module ready.")
