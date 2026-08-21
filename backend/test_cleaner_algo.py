# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import json
from PIL import Image

def get_bubble_background_color(img: np.ndarray, x: int, y: int, w: int, h: int) -> tuple[int, int, int]:
    """
    Samples background color from perimeter and non-text interior of the bubble box.
    Returns (B, G, R) background color tuple.
    """
    ih, iw, _ = img.shape
    
    # 1. Sample perimeter strips around the bounding box
    pad = 8
    strips = []
    
    # Top strip
    if y - pad >= 0:
        strips.append(img[max(0, y-pad):y, max(0, x-pad):min(iw, x+w+pad)])
    # Bottom strip
    if y + h + pad <= ih:
        strips.append(img[y+h:min(ih, y+h+pad), max(0, x-pad):min(iw, x+w+pad)])
    # Left strip
    if x - pad >= 0:
        strips.append(img[max(0, y-pad):min(ih, y+h+pad), max(0, x-pad):x])
    # Right strip
    if x + w + pad <= iw:
        strips.append(img[max(0, y-pad):min(ih, y+h+pad), x+w:min(iw, x+w+pad)])
        
    perimeter_pixels = []
    for s in strips:
        if s.size > 0:
            perimeter_pixels.append(s.reshape(-1, 3))
            
    if perimeter_pixels:
        all_p = np.vstack(perimeter_pixels)
        # Median color of perimeter
        med_bgr = np.median(all_p, axis=0).astype(int)
        return int(med_bgr[0]), int(med_bgr[1]), int(med_bgr[2])
        
    # Fallback to interior median
    crop = img[max(0, y):min(ih, y+h), max(0, x):min(iw, x+w)]
    if crop.size > 0:
        med_bgr = np.median(crop.reshape(-1, 3), axis=0).astype(int)
        return int(med_bgr[0]), int(med_bgr[1]), int(med_bgr[2])
        
    return 255, 255, 255

def clean_bubble_seamless(img: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    ih, iw, _ = img.shape
    
    # Pad ROI by 6px to have full context
    pad = 6
    bx1 = max(0, x - pad)
    by1 = max(0, y - pad)
    bx2 = min(iw, x + w + pad)
    by2 = min(ih, y + h + pad)
    
    roi = img[by1:by2, bx1:bx2]
    if roi.size == 0:
        return img
        
    # Determine exact background color
    bg_b, bg_g, bg_r = get_bubble_background_color(img, x, y, w, h)
    bg_color = np.array([bg_b, bg_g, bg_r], dtype=np.float32)
    
    # Calculate Euclidean color distance from background
    diff = np.sqrt(np.sum((roi.astype(np.float32) - bg_color) ** 2, axis=2))
    
    # Text pixels differ from background
    # Normal threshold is 32 in RGB color distance
    text_mask = (diff > 30).astype(np.uint8) * 255
    
    # Clean small noise artifacts
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_small)
    
    # Dilate text mask by 2px to cover font anti-aliasing edges
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    text_mask = cv2.dilate(text_mask, kernel_dilate, iterations=2)
    
    # If solid background (standard manga bubble):
    # Inpaint with TELEA using the tight text mask
    inpainted = cv2.inpaint(roi, text_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    
    # For solid bubbles with low variance, also blend with exact background color
    bg_lum = 0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b
    if bg_lum > 220 or bg_lum < 40:
        # Near solid white or black: replace text core with pure bg_color
        solid_fill = np.full_like(roi, (bg_b, bg_g, bg_r))
        mask_3d = np.repeat(text_mask[:, :, np.newaxis] / 255.0, 3, axis=2)
        blended = (inpainted.astype(float) * 0.3 + solid_fill.astype(float) * 0.7).astype(np.uint8)
        inpainted = np.where(mask_3d > 0.5, blended, inpainted)
        
    img[by1:by2, bx1:bx2] = inpainted
    return img

print("Cleaner algorithm module test ready.")
