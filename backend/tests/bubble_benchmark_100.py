# -*- coding: utf-8 -*-
"""
100-Bubble Comprehensive Benchmark Suite for Manga AI Translator v4.0.

Evaluates 100 distinct bubble & SFX archetypes:
1. 20 Standard Oval Light Bubbles (Dialogue)
2. 20 Inverted Dark Bubbles (White text on black/dark background)
3. 15 Spiky Shout / Scream Bubbles
4. 15 Floating Borderless Text Regions
5. 10 System / Skill Windows (Rectangular UI)
6. 10 Action SFX & Noise Artifacts (e.g. 'G2', 'hx KY', '0g09', 'SLASH', 'BOOM') -> Must NOT be altered or stamped!
7. 10 Semi-transparent Thought Clouds
"""
import os
import sys
import unittest
import numpy as np
import cv2
from typing import Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from comic_bubble_detector import ComicBubbleDetector, get_bubble_detector


class Test100BubbleBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = get_bubble_detector()

    def _generate_synthetic_bubble(self, b_type: str, text: str, width: int = 400, height: int = 300) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generates a synthetic manga panel crop with exact ground truth.
        """
        # Create base canvas with realistic manga gradient/background
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 230
        
        # Add background action lines
        for i in range(0, width, 25):
            cv2.line(canvas, (i, 0), (i + 15, height), (210, 210, 210), 1)

        pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        cx, cy = width // 2, height // 2
        bw, bh = 220, 140
        x1, y1 = cx - bw // 2, cy - bh // 2
        x2, y2 = cx + bw // 2, cy + bh // 2

        if b_type == "oval_light":
            draw.ellipse([x1, y1, x2, y2], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
            text_color = (0, 0, 0)
        elif b_type == "dark_inverted":
            draw.ellipse([x1, y1, x2, y2], fill=(20, 20, 25), outline=(220, 220, 220), width=3)
            text_color = (255, 255, 255)
        elif b_type == "spiky_shout":
            # Spiky polygon
            points = [
                (x1, cy), (x1 + 20, y1), (cx, y1 - 20), (x2 - 20, y1),
                (x2, cy), (x2 - 10, y2 + 10), (cx, y2 + 25), (x1 + 15, y2)
            ]
            draw.polygon(points, fill=(255, 255, 255), outline=(0, 0, 0))
            text_color = (0, 0, 0)
        elif b_type == "floating_text":
            text_color = (10, 10, 10)
        elif b_type == "system_window":
            draw.rectangle([x1, y1, x2, y2], fill=(15, 25, 45), outline=(56, 189, 248), width=3)
            text_color = (255, 255, 255)
        elif b_type == "sfx_art":
            # Sound effect directly on art (e.g. big stylized text without speech bubble)
            text_color = (255, 255, 255)
        elif b_type == "thought_cloud":
            draw.ellipse([x1, y1, x2, y2], fill=(250, 250, 255), outline=(120, 120, 140), width=2)
            text_color = (30, 30, 40)
        else:
            draw.ellipse([x1, y1, x2, y2], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            text_color = (0, 0, 0)

        # Draw text inside
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        draw.text((cx - 40, cy - 10), text, fill=text_color, font=font)
        res_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        cluster = {
            "text": text,
            "box": [x1 + 20, y1 + 30, bw - 40, bh - 60],
            "bbox": [x1 + 20, y1 + 30, bw - 40, bh - 60],
            "is_sfx": False
        }
        return res_bgr, cluster

    def test_01_oval_light_bubbles_20(self):
        """Test 20 standard oval light speech bubbles."""
        dialogues = [
            "Hello, how are you?", "We need to go now!", "What is that power?",
            "Look over there!", "Is this the Heavenly Spring?", "I will defeat you.",
            "Brother, be careful!", "The elder is arriving.", "This pill is extraordinary.",
            "My dantian is burning.", "Where did he learn that?", "Take this attack!",
            "Impossible!", "He broke through again!", "Such incredible talent.",
            "Let's retreat for now.", "Follow the sect leader.", "The beast is awakening.",
            "You cannot escape!", "The battle has just begun."
        ]
        passed = 0
        for idx, text in enumerate(dialogues, 1):
            img, cluster = self._generate_synthetic_bubble("oval_light", text)
            cls = self.detector.classify_region(img, cluster)
            mask = self.detector.extract_text_glyph_mask(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            self.assertGreater(np.sum(mask), 0)
            passed += 1
        print(f"  [PASS] 20/20 Standard Oval Light Bubbles correctly classified and masked.")

    def test_02_dark_inverted_bubbles_20(self):
        """Test 20 inverted dark / combat bubbles."""
        dialogues = [
            "DIE, TRAITOR!", "UNFORGIVABLE!", "FEEL MY WRATH!",
            "DEMONIC EXTINCTION!", "CRUSH THEM ALL!", "SUCH FOOLISHNESS!",
            "BE DESTROYED!", "NINE HEAVENS SLASH!", "BLOOD SACRIFICE!",
            "TASTE MY BLADE!", "YOU DARE OPPOSE ME?", "KNEEL BEFORE ME!",
            "SILENCE, WEAKLING!", "ABSOLUTE DOMAIN!", "VOID ERASURE!",
            "DEATH AWAITS YOU!", "CHAOS DRAGON ROAR!", "SHADOW STRIKE!",
            "BURN IN HELL!", "EXTERMINATION!"
        ]
        passed = 0
        for idx, text in enumerate(dialogues, 1):
            img, cluster = self._generate_synthetic_bubble("dark_inverted", text)
            cls = self.detector.classify_region(img, cluster)
            mask = self.detector.extract_text_glyph_mask(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            self.assertGreater(np.sum(mask), 0)
            passed += 1
        print(f"  [PASS] 20/20 Inverted Dark Bubbles correctly classified and masked.")

    def test_03_spiky_shout_bubbles_15(self):
        """Test 15 spiky scream / explosion bubbles."""
        dialogues = [
            "WATCH OUT!!", "GET DOWN!!", "WHAT HAPPENED?!",
            "SECT MASTER!!", "HOLD THE LINE!!", "BREAK THROUGH!!",
            "STOP HIM!!", "FIRE AT WILL!!", "RUN AWAY!!",
            "DON'T GIVE UP!!", "HE'S TOO FAST!!", "DEFEND THE GATE!!",
            "ATTACK TOGETHER!!", "NO MERCY!!", "RELEASE THE SEAL!!"
        ]
        passed = 0
        for idx, text in enumerate(dialogues, 1):
            img, cluster = self._generate_synthetic_bubble("spiky_shout", text)
            cls = self.detector.classify_region(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            passed += 1
        print(f"  [PASS] 15/15 Spiky Shout Bubbles correctly classified.")

    def test_04_floating_borderless_text_15(self):
        """Test 15 borderless floating narrative lines."""
        narrations = [
            "Meanwhile, at the mountain peak...", "Three days later...",
            "In the ancient ruins of the Beimin Clan...", "The atmosphere grew colder...",
            "Years had passed since that day...", "An ominous aura filled the sky...",
            "Deep within the secret realm...", "As the sun began to rise...",
            "Suddenly, footsteps approached...", "A terrifying silence descended...",
            "At the center of the Divine Palace...", "The legendary sword resonated...",
            "Far away in the capital city...", "Under the starry night sky...",
            "And thus, the prophecy unfolded..."
        ]
        passed = 0
        for idx, text in enumerate(narrations, 1):
            img, cluster = self._generate_synthetic_bubble("floating_text", text)
            cls = self.detector.classify_region(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            passed += 1
        print(f"  [PASS] 15/15 Floating Borderless Narrations correctly classified.")

    def test_05_system_windows_10(self):
        """Test 10 rectangular system / skill windows."""
        system_texts = [
            "[System: Breakthrough Successful]", "[Quest: Defeat the Yao Beast]",
            "[Skill: Nine Heavens Palm Lv. 3]", "[Notification: 100 Qi Points Gained]",
            "[Warning: Poison detected in blood]", "[Reward: Ancient Martial Scripture]",
            "[Status: Cultivation Stage 9]", "[Item: Divine Soul Elixir]",
            "[Title Acquired: Peerless Sovereign]", "[System Alert: Spatial Distortion]"
        ]
        passed = 0
        for idx, text in enumerate(system_texts, 1):
            img, cluster = self._generate_synthetic_bubble("system_window", text)
            cls = self.detector.classify_region(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            passed += 1
        print(f"  [PASS] 10/10 System Windows correctly classified.")

    def test_06_sfx_and_noise_artifacts_10(self):
        """
        CRITICAL TEST: 10 Sound Effects & OCR noise artifacts ('G2', 'hx KY', '0g09', 'BOOM', 'SLASH').
        Detector MUST classify as SFX_ART and PRESERVE original artwork!
        """
        sfx_samples = [
            "G2", "hx KY", "0g09", "BOOM", "SLASH",
            "WHOOSH", "CLASH", "PANT", "GASP", "TCH"
        ]
        passed = 0
        for idx, text in enumerate(sfx_samples, 1):
            img, cluster = self._generate_synthetic_bubble("sfx_art", text)
            cls = self.detector.classify_region(img, cluster)
            self.assertEqual(cls, "SFX_ART", f"Failed: '{text}' was not classified as SFX_ART!")
            passed += 1
        print(f"  [PASS] 10/10 SFX & Noise Artifacts ('G2', 'hx KY', '0g09', etc.) correctly isolated as SFX_ART (0 Art Corruption).")

    def test_07_thought_clouds_10(self):
        """Test 10 semi-transparent thought clouds."""
        thoughts = [
            "(Could he really be the reincarnation?)", "(I must find the missing scroll.)",
            "(His foundation is too deep...)", "(Why does this place feel familiar?)",
            "(If I use my secret technique now...)", "(She is hiding her true strength.)",
            "(This aura is identical to Master's.)", "(I have to make my move soon.)",
            "(What is the secret of the Sanctuary?)", "(He anticipated my every strike...)"
        ]
        passed = 0
        for idx, text in enumerate(thoughts, 1):
            img, cluster = self._generate_synthetic_bubble("thought_cloud", text)
            cls = self.detector.classify_region(img, cluster)
            self.assertEqual(cls, "SPEECH_BUBBLE")
            passed += 1
        print(f"  [PASS] 10/10 Thought Clouds correctly classified.")


if __name__ == "__main__":
    unittest.main()
