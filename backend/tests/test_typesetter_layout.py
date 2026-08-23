# -*- coding: utf-8 -*-
"""
Unit test for Typesetter Layout:
1. Elliptical/Circular Bubble Fitting (150x150 px with 12-word Russian sentence)
2. Strict Circle Boundary Constraint (Zero text pixels outside radius 75)
3. Light vs Dark Bubble Auto-Contrast
"""
import sys
import os
import math
import unittest
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents")))
from translator_typesetter_agent import typeset_bubble


class TestTypesetterLayout(unittest.TestCase):
    """
    Unit tests for elliptical chord typesetting, boundary adherence, and auto-contrast.
    """

    def test_circular_bubble_fitting(self):
        # 1. Create a 200x200 canvas with a 150x150 white circle in the center (25..175)
        img_size = 200
        cx, cy, r = 100, 100, 75
        bg_color = (200, 200, 200)  # Gray canvas background
        bubble_color = (255, 255, 255)  # White bubble interior
        
        pil_img = Image.new("RGB", (img_size, img_size), bg_color)
        draw = ImageDraw.Draw(pil_img)
        
        # Draw bubble circle
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bubble_color, outline=(0, 0, 0), width=2)
        
        cluster = {
            "id": 1,
            "box": [cx - r, cy - r, 2 * r, 2 * r],  # [25, 25, 150, 150]
            "is_dark": False
        }
        
        long_phrase = "Мастер, эта древняя техника разрушения небес слишком опасна для вашего текущего уровня культивации!"
        words_count = len(long_phrase.split())
        self.assertGreaterEqual(words_count, 12, f"Expected at least 12 words, got {words_count}")
        
        # Render text into bubble
        typeset_bubble(draw, pil_img, cluster, long_phrase)
        
        # Check pixel distribution
        img_np = np.array(pil_img)
        
        # Text pixels are dark pixels inside the image (luminance < 100)
        luma = 0.299 * img_np[:, :, 0] + 0.587 * img_np[:, :, 1] + 0.114 * img_np[:, :, 2]
        text_y_indices, text_x_indices = np.where(luma < 100)
        
        self.assertGreater(len(text_x_indices), 0, "Text was not rendered onto the bubble!")
        
        max_dist = 0.0
        outside_pixels = 0
        
        for px, py in zip(text_x_indices, text_y_indices):
            dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
            # Exclude the border circle itself (radius 74..76)
            if dist < 73:
                if dist > max_dist:
                    max_dist = dist
            elif dist > 76:
                outside_pixels += 1
                
        # All text pixels must be within safe radius <= 88% of r
        self.assertEqual(outside_pixels, 0, f"Found {outside_pixels} text pixels leaking outside circle radius {r}px!")
        self.assertLessEqual(max_dist, r * 0.88, f"Text exceeded safe oval radius: max_dist={max_dist:.2f}px > {r * 0.88:.2f}px")

    def test_dark_bubble_contrast(self):
        # 2. Test dark bubble: black background with white text
        img_size = 160
        pil_img = Image.new("RGB", (img_size, img_size), (20, 20, 20))
        draw = ImageDraw.Draw(pil_img)
        
        cluster = {
            "id": 2,
            "box": [10, 10, 140, 140],
            "is_dark": True
        }
        
        shout_text = "СМЕРТЬ ТЕБЕ, ПРЕДАТЕЛЬ!"
        typeset_bubble(draw, pil_img, cluster, shout_text)
        
        img_np = np.array(pil_img)
        # Check for presence of bright white text (luminance > 220)
        luma = 0.299 * img_np[:, :, 0] + 0.587 * img_np[:, :, 1] + 0.114 * img_np[:, :, 2]
        white_pixels = np.sum(luma > 220)
        
        self.assertGreater(white_pixels, 50, "Dark bubble failed to render bright white text with auto-contrast!")


if __name__ == "__main__":
    unittest.main()
