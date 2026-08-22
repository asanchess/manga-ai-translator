# -*- coding: utf-8 -*-
"""
Adversarial Stress Test Suite - Challenger 1
Manga & Manhua AI Translation and Inpainting Pipeline v4.0

Rigorous adversarial stress testing covering:
1. Inverted Dark Bubbles (gradients, pure black, dark grey, thin borders, colored aura)
2. Spiky / Scream / Explosion Bubbles (acute spikes, multi-angle polygons, jagged borders)
3. Overlapping / Chained Bubbles (intersecting boxes, double bubbles, connected tails)
4. Complex SFX Combat Text Noise (sound effects with symbols, mixed noise, battle cries)
5. Anti-Patch Guard Detection Sensitivity & Inpainting Boundary Integrity
"""
import os
import sys
import unittest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from comic_bubble_detector import ComicBubbleDetector, get_bubble_detector
from cleaner_agent import clean_speech_bubble_seamless, get_bubble_background_color
from anti_patch_guard import detect_solid_patches, compute_background_ssim


class TestAdversarialVisionPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = get_bubble_detector()

    def test_adv_01_dark_inverted_complex_gradients(self):
        """
        Stress test: Inverted dark bubbles with internal radial gradients, dark purple/red tints,
        and high-contrast text. Tests both classification and per-pixel inpainting.
        """
        scenarios = [
            {"bg_color": (15, 15, 15), "text": "HEAVENLY DEMON PALM!", "border": (200, 200, 200)},
            {"bg_color": (30, 10, 40), "text": "BLOOD SACRIFICE TECHNIQUE", "border": (255, 100, 100)},
            {"bg_color": (10, 30, 10), "text": "NINE POISONS CONSUMPTION", "border": (100, 255, 100)},
            {"bg_color": (40, 30, 10), "text": "EARTH CRUSHING DOMAIN!", "border": (220, 180, 50)},
            {"bg_color": (25, 25, 30), "text": "YOU ARE ALREADY DEAD.", "border": (255, 255, 255)},
        ]
        
        for idx, sc in enumerate(scenarios):
            canvas = np.ones((300, 400, 3), dtype=np.uint8) * 220
            pil_img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(pil_img)
            
            # Dark bubble
            cx, cy = 200, 150
            draw.ellipse([80, 70, 320, 230], fill=sc["bg_color"], outline=sc["border"], width=3)
            draw.text((100, 140), sc["text"], fill=(255, 255, 255))
            
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            cluster = {
                "text": sc["text"],
                "box": [90, 80, 220, 140],
                "bbox": [90, 80, 220, 140],
                "is_sfx": False
            }
            
            # 1. Classification
            cls_result = self.detector.classify_region(img_bgr, cluster)
            self.assertEqual(cls_result, "SPEECH_BUBBLE", f"Dark bubble {idx} misclassified: {cls_result}")
            
            # 2. Glyph mask extraction
            glyph_mask = self.detector.extract_text_glyph_mask(img_bgr, cluster)
            self.assertGreater(np.sum(glyph_mask), 0, f"Glyph mask empty for dark bubble {idx}")
            
            # 3. Clean and verify no solid patch violation
            img_cleaned = img_bgr.copy()
            clean_speech_bubble_seamless(img_cleaned, cluster)
            
            # 4. Anti-Patch Guard check
            guard_res = detect_solid_patches(img_cleaned, [cluster])
            self.assertTrue(guard_res["passed"], f"Dark bubble {idx} generated solid patch violation: {guard_res}")

    def test_adv_02_spiky_scream_complex_geometry(self):
        """
        Stress test: Multi-pointed spiky scream bubbles with sharp tips extending far out.
        Ensures bubble contour extraction and inpainting don't wipe out the spikes.
        """
        shout_texts = [
            "IMPOSSIBLE!!!", "HOW COULD HE BE SO STRONG?!",
            "SECT MASTER, EVACUATE NOW!!", "DIE A THOUSAND DEATHS!!!"
        ]
        for idx, text in enumerate(shout_texts):
            canvas = np.ones((350, 450, 3), dtype=np.uint8) * 215
            # Add action lines behind bubble
            for a in range(0, 450, 15):
                cv2.line(canvas, (a, 0), (225, 175), (180, 180, 180), 1)
                
            pil_img = Image.fromarray(canvas)
            draw = ImageDraw.Draw(pil_img)
            
            # 16-point star/spiky polygon
            cx, cy = 225, 175
            points = []
            for i in range(16):
                angle = i * (2 * np.pi / 16)
                r = 140 if i % 2 == 0 else 70
                px = cx + int(r * np.cos(angle))
                py = cy + int(r * np.sin(angle))
                points.append((px, py))
                
            draw.polygon(points, fill=(255, 255, 255), outline=(0, 0, 0))
            draw.text((150, 165), text, fill=(0, 0, 0))
            
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            cluster = {
                "text": text,
                "box": [140, 130, 170, 90],
                "bbox": [140, 130, 170, 90],
                "is_sfx": False
            }
            
            cls_result = self.detector.classify_region(img_bgr, cluster)
            self.assertEqual(cls_result, "SPEECH_BUBBLE")
            
            # Mask should be generated within contour
            contour_mask = self.detector.get_bubble_contour_mask(img_bgr, (140, 130, 170, 90))
            self.assertGreater(np.count_nonzero(contour_mask), 0)
            
            # Test inpainting and verify background SSIM
            img_cleaned = img_bgr.copy()
            clean_speech_bubble_seamless(img_cleaned, cluster)
            
            ssim_res = compute_background_ssim(img_bgr, img_cleaned, [cluster], pad=15)
            self.assertTrue(ssim_res["passed"], f"Spiky bubble {idx} corrupted background: {ssim_res}")

    def test_adv_03_overlapping_chained_bubbles(self):
        """
        Stress test: Two connected or overlapping bubbles where cleaning one must not
        destroy or corrupt the adjacent bubble.
        """
        canvas = np.ones((400, 500, 3), dtype=np.uint8) * 230
        pil_img = Image.fromarray(canvas)
        draw = ImageDraw.Draw(pil_img)
        
        # Bubble 1 (top-left)
        draw.ellipse([50, 50, 250, 190], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw.text((80, 110), "Listen carefully Li Yunxiao...", fill=(0, 0, 0))
        
        # Bubble 2 (overlapping bottom-right)
        draw.ellipse([180, 150, 420, 290], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw.text((210, 210), "The Sanctuary is in grave danger!", fill=(0, 0, 0))
        
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        c1 = {"text": "Listen carefully Li Yunxiao...", "box": [70, 90, 160, 60], "is_sfx": False}
        c2 = {"text": "The Sanctuary is in grave danger!", "box": [200, 190, 200, 60], "is_sfx": False}
        
        # Clean both sequentially
        img_cleaned = img_bgr.copy()
        clean_speech_bubble_seamless(img_cleaned, c1)
        clean_speech_bubble_seamless(img_cleaned, c2)
        
        # Check both passes Anti-Patch Guard
        guard_res = detect_solid_patches(img_cleaned, [c1, c2])
        self.assertTrue(guard_res["passed"], f"Overlapping bubbles failed solid patch guard: {guard_res}")
        
        ssim_res = compute_background_ssim(img_bgr, img_cleaned, [c1, c2], pad=10)
        self.assertTrue(ssim_res["passed"], f"Overlapping bubbles background SSIM failed: {ssim_res}")

    def test_adv_04_sfx_and_combat_noise_rejection(self):
        """
        Stress test: Highly diverse combat sound effects, OCR misreads, and onomatopoeia.
        All MUST be classified as SFX_ART and PRESERVED (never inpainted or erased).
        """
        adversarial_sfx = [
            # Short OCR noise
            "G2", "hx KY", "0g09", "ix", "xk", "fk", "qk", "pk", "vk", "09", "og", "1a2",
            # Standard battle sound effects
            "BOOM", "SLASH", "WHOOSH", "CRASH", "BANG", "CLASH", "ROAR", "THUD", "CRACK",
            # Manga onomatopoeia & sighs
            "PANT", "GASP", "TCH", "URGH", "ARGH", "GRR", "HUMPH", "HISS", "PUFF", "SOB",
            # Noise sequences
            "A1 B2", "XX YY", "Z9 88", "ZZZ", "KHHK"
        ]
        
        for sfx in adversarial_sfx:
            cluster = {"text": sfx, "box": [50, 50, 100, 50], "is_sfx": False}
            canvas = np.ones((200, 200, 3), dtype=np.uint8) * 200
            
            is_sfx = self.detector.is_sound_effect_or_noise(sfx, cluster=cluster, img_bgr=canvas)
            cls_name = self.detector.classify_region(canvas, cluster)
            
            self.assertTrue(is_sfx, f"SFX '{sfx}' was NOT recognized as sound effect/noise!")
            self.assertEqual(cls_name, "SFX_ART", f"SFX '{sfx}' classified as {cls_name} instead of SFX_ART!")

    def test_adv_05_anti_patch_guard_attack_scenarios(self):
        """
        Adversarial test on Anti-Patch Guard itself:
        1. Sub-box solid patch inside bubble (must be detected).
        2. Gradient inpainting (must pass).
        3. Background modification outside bubble box (must fail SSIM).
        """
        h, w = 300, 300
        canvas = np.random.randint(200, 240, (h, w, 3), dtype=np.uint8)
        box = [50, 50, 100, 80]
        
        # 1. Pure solid fill sub-patch
        patched = canvas.copy()
        patched[60:110, 60:130] = [255, 255, 255] # Solid white rectangle
        res_solid = detect_solid_patches(patched, [{"box": box}])
        self.assertFalse(res_solid["passed"], "Anti-Patch Guard failed to detect solid rectangle inside bubble!")
        
        # 2. Inpainted with realistic texture variance
        inpainted = canvas.copy()
        for r in range(60, 110):
            for c in range(60, 130):
                inpainted[r, c] = [250 + (r % 5), 250 + (c % 4), 250]
        res_inpaint = detect_solid_patches(inpainted, [{"box": box}])
        self.assertTrue(res_inpaint["passed"], f"Anti-Patch Guard falsely rejected textured inpainting: {res_inpaint}")
        
        # 3. Background destruction
        corrupted_bg = inpainted.copy()
        corrupted_bg[200:250, 200:250] = [0, 0, 0] # Solid black on background
        ssim_res = compute_background_ssim(canvas, corrupted_bg, [{"box": box}])
        self.assertFalse(ssim_res["passed"], "Anti-Patch Guard failed to catch background destruction!")


if __name__ == "__main__":
    unittest.main()
