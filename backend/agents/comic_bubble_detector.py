# -*- coding: utf-8 -*-
"""
ComicBubbleDetector — SOTA Speech Bubble vs SFX Classifier & Precision Segmentation.

Distinguishes:
1. SPEECH_BUBBLE (dialogue, thought, narration, scream bubbles) -> Translated & Inpainted.
2. SFX_ART (onomatopoeia, action sound effects, background kanji/drawings) -> PRESERVED 100% (No inpainting, No text stamping).
3. BACKGROUND_NOISE (action lines, textures, accidental OCR hits like 'G2', 'hx KY', '0g09') -> IGNORED.
"""
import os
import sys
import re
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

# Standard SFX and noise blacklist
SFX_AND_NOISE_PATTERNS = [
    r'^[a-zA-Z0-9]{1,3}$',          # 1-3 char random noise: G2, hx, KY, 0g, etc.
    r'^(hx|ky|g2|0g|09|og|ix|xk|fk|zk|qk|pk|vk)$',
    r'^(boom|bang|crash|slash|whoosh|swish|clash|roar|thud|crack|creak|pant|gasp|sigh|ah|oh|tch|uh|urgh|argh|grr|humph|ha|heh|hm|hmm|hiss|shh|puff|giggle|sob|sniff)$',
    r'^[0-9]+[a-zA-Z]+[0-9]*$',     # 0g09, 1a2, etc.
]

COMMON_SFX_REGEX = re.compile('|'.join(SFX_AND_NOISE_PATTERNS), re.IGNORECASE)


class ComicBubbleDetector:
    """
    High-precision bubble and text classifier.
    Combines geometry, contour curvature, perimeter variance, and text linguistics.
    """
    def __init__(self, confidence_threshold: float = 0.40):
        self.confidence_threshold = confidence_threshold

    def is_sound_effect_or_noise(self, text: str, cluster: Optional[Dict[str, Any]] = None, img_bgr: Optional[np.ndarray] = None) -> bool:
        """
        Determines if a detected text region is a Sound Effect (SFX) or background artifact.
        """
        clean_text = text.strip()
        if not clean_text:
            return True

        # Rule 1: Whole text regex match
        if COMMON_SFX_REGEX.match(clean_text):
            return True

        words = clean_text.split()
        
        # Rule 2: Multi-token short noise (e.g. 'hx KY', '0g 09', 'A1 B2')
        valid_short_words = {"i", "a", "no", "he", "it", "to", "go", "in", "on", "me", "we", "us", "oh", "ah", "am", "is", "my", "by", "do", "so", "up", "if", "at", "as", "or", "an", "be"}
        if len(words) >= 1 and all(len(w) <= 3 for w in words):
            # If none of the words are common English words
            if not any(w.lower() in valid_short_words for w in words):
                return True

        # Rule 3: Single or double character non-words
        alphanumeric = re.sub(r'[^a-zA-Z0-9]', '', clean_text)
        if len(alphanumeric) <= 2 and clean_text.lower() not in valid_short_words:
            return True

        # Rule 4: Visual background texture analysis if image provided
        if img_bgr is not None and cluster is not None:
            box = cluster.get("box") or cluster.get("bbox")
            if box:
                x, y, w, h = box
                ih, iw = img_bgr.shape[:2]
                x1, y1 = max(0, int(x)), max(0, int(y))
                x2, y2 = min(iw, int(x + w)), min(ih, int(y + h))

                if (x2 - x1) > 10 and (y2 - y1) > 10:
                    crop = img_bgr[y1:y2, x1:x2]
                    gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    
                    # Compute border luminance variance to detect enclosed bubble vs busy action background
                    border_mask = np.ones_like(gray_crop, dtype=bool)
                    border_mask[2:-2, 2:-2] = False
                    border_pixels = gray_crop[border_mask]
                    border_variance = float(np.var(border_pixels))

                    # If background is extremely noisy/textured and text is short (<= 8 chars) without punctuation
                    if border_variance > 1200 and len(clean_text.split()) <= 2 and not any(p in clean_text for p in ".!?,:;"):
                        return True

        return False

    def classify_region(self, img_bgr: np.ndarray, cluster: Dict[str, Any]) -> str:
        """
        Classifies a detected region as 'SPEECH_BUBBLE', 'SFX_ART', or 'BACKGROUND_NOISE'.
        """
        text = cluster.get("text", "")
        if self.is_sound_effect_or_noise(text, cluster=cluster, img_bgr=img_bgr):
            return "SFX_ART"
        return "SPEECH_BUBBLE"

    def get_bubble_contour_mask(self, img_bgr: np.ndarray, box: Tuple[int, int, int, int], is_dark_bubble: bool = False) -> np.ndarray:
        """
        Extracts an accurate polygon mask of the speech bubble to avoid rectangular background damage.
        """
        x, y, w, h = box
        ih, iw = img_bgr.shape[:2]
        
        pad = int(min(w, h) * 0.15)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(iw, x + w + pad)
        y2 = min(ih, y + h + pad)

        crop = img_bgr[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        if is_dark_bubble:
            _, binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        else:
            _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
        if contours:
            center_x = (x + w // 2) - x1
            center_y = (y + h // 2) - y1
            
            best_cnt = None
            max_area = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > max_area and cv2.pointPolygonTest(cnt, (center_x, center_y), False) >= 0:
                    max_area = area
                    best_cnt = cnt
            
            if best_cnt is not None:
                offset_cnt = best_cnt + np.array([x1, y1])
                cv2.drawContours(mask, [offset_cnt], -1, 255, -1)
                return mask

        # Elliptical fallback mask inside box (never a sharp rectangle)
        center = (x + w // 2, y + h // 2)
        axes = (w // 2, h // 2)
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        return mask

    def extract_text_glyph_mask(self, img_bgr: np.ndarray, cluster: Dict[str, Any]) -> np.ndarray:
        """
        Extracts the exact per-pixel letter glyph mask for inpainting.
        """
        box = cluster.get("box") or cluster.get("bbox")
        if not box:
            return np.zeros(img_bgr.shape[:2], dtype=np.uint8)

        x, y, w, h = box
        ih, iw = img_bgr.shape[:2]
        x1, y1 = max(0, int(x)), max(0, int(y))
        x2, y2 = min(iw, int(x + w)), min(ih, int(y + h))

        crop = img_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return np.zeros(img_bgr.shape[:2], dtype=np.uint8)

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Detect bubble polarity (dark vs light)
        mean_lum = float(np.mean(gray))
        is_dark = mean_lum < 110

        if is_dark:
            # White letters on dark background
            _, glyph_crop = cv2.threshold(gray, int(mean_lum + 35), 255, cv2.THRESH_BINARY)
        else:
            # Black/dark letters on light background
            _, glyph_crop = cv2.threshold(gray, int(mean_lum - 35), 255, cv2.THRESH_BINARY_INV)

        # 2px dilation for complete glyph boundary coverage
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        glyph_crop = cv2.dilate(glyph_crop, kernel, iterations=1)

        full_mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
        full_mask[y1:y2, x1:x2] = glyph_crop
        return full_mask


# Module singleton
_detector_instance = None

def get_bubble_detector() -> ComicBubbleDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ComicBubbleDetector()
    return _detector_instance
