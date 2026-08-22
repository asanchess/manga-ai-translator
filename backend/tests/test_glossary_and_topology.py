# -*- coding: utf-8 -*-
"""
Unit tests for Milestone M2:
1. Persistent Glossary loading and category integrity.
2. Prompt injection of glossary terms.
3. Topological bubble sorting (y_center * 10000 + x_center) and 1-based sequential ID assignment.
4. Batch JSON translation request/response with strict ID preservation.
5. Offline fallback glossary substitution for Xianxia terms.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents")))

from llm_translator import (
    load_manga_glossary,
    format_glossary_for_prompt,
    fallback_translate_text,
    translate_bubbles_batch
)
from ocr_engine import topological_reading_sort_key

class TestGlossaryAndTopology(unittest.TestCase):

    def test_01_glossary_loading(self):
        """Verify glossary.json exists and loads all required character, faction, and cultivation terms."""
        glossary = load_manga_glossary("The_Ultimate_of_All_Ages")
        self.assertIsInstance(glossary, dict)
        self.assertGreaterEqual(len(glossary), 30, f"Expected >= 30 terms, got {len(glossary)}")
        
        # Test character names
        self.assertEqual(glossary.get("Gu Feiyang"), "Гу Фэйян")
        self.assertEqual(glossary.get("Li Yunxiao"), "Ли Юньсяо")
        self.assertEqual(glossary.get("Luo Yunshang"), "Ло Юньшан")
        
        # Test factions / locations
        self.assertEqual(glossary.get("Beimin Clan"), "Клан Бэймин")
        self.assertEqual(glossary.get("Sanctuary"), "Святилище")
        self.assertEqual(glossary.get("Heavenly Water Nation"), "Страна Небесной Воды")
        
        # Test cultivation terms & ranks
        self.assertEqual(glossary.get("Martial Sovereign"), "Боевой Владыка")
        self.assertEqual(glossary.get("Nine Heavens"), "Девять Небес")
        self.assertEqual(glossary.get("Primordial Divine Realm"), "Изначальное Божественное Царство")
        self.assertEqual(glossary.get("Dantian"), "Даньтянь")
        self.assertEqual(glossary.get("Qi"), "Ци")
        self.assertEqual(glossary.get("Yao Beast"), "Демонический Зверь")
        print("  [PASS] test_01_glossary_loading: All required Xianxia terms present and accurate.")

    def test_02_prompt_injection(self):
        """Verify format_glossary_for_prompt produces valid prompt instructions."""
        glossary = {
            "Gu Feiyang": "Гу Фэйян",
            "Martial Sovereign": "Боевой Владыка"
        }
        prompt_block = format_glossary_for_prompt(glossary)
        self.assertIn("CRITICAL MANDATORY TERMINOLOGY GLOSSARY", prompt_block)
        self.assertIn('"Gu Feiyang" -> "Гу Фэйян"', prompt_block)
        self.assertIn('"Martial Sovereign" -> "Боевой Владыка"', prompt_block)
        print("  [PASS] test_02_prompt_injection: Glossary successfully formatted for prompt injection.")

    def test_03_topological_sorting_math(self):
        """Verify topological sorting using y_center * 10000 + x_center logic."""
        b1 = (50, 50, 100, 40)
        b2 = (400, 60, 80, 40)
        b3 = (100, 300, 120, 50)
        b4 = (200, 800, 150, 60)
        
        k1 = topological_reading_sort_key(b1, row_height=50, direction="ltr")
        k2 = topological_reading_sort_key(b2, row_height=50, direction="ltr")
        k3 = topological_reading_sort_key(b3, row_height=50, direction="ltr")
        k4 = topological_reading_sort_key(b4, row_height=50, direction="ltr")
        
        self.assertLess(k1, k2)
        self.assertLess(k2, k3)
        self.assertLess(k3, k4)
        
        bubbles = [
            {"id": None, "box": b4, "text": "Bottom"},
            {"id": None, "box": b2, "text": "Top Right"},
            {"id": None, "box": b1, "text": "Top Left"},
            {"id": None, "box": b3, "text": "Middle"}
        ]
        
        bubbles.sort(key=lambda c: topological_reading_sort_key(c["box"], row_height=50, direction="ltr"))
        for idx, b in enumerate(bubbles, 1):
            b["id"] = idx
            
        self.assertEqual([b["text"] for b in bubbles], ["Top Left", "Top Right", "Middle", "Bottom"])
        self.assertEqual([b["id"] for b in bubbles], [1, 2, 3, 4])
        print("  [PASS] test_03_topological_sorting_math: Topological sort key and sequential IDs verified.")

    def test_04_batch_json_translation_contract(self):
        """Verify batch translation preserves 1-based sequential integer IDs."""
        input_items = [
            {"id": 1, "text": "Who are you?"},
            {"id": 2, "text": "I am Li Yunxiao, the rebirth of Martial Sovereign Gu Feiyang!"},
            {"id": 3, "text": "Impossible! Gu Feiyang died at Mount Xuanyuan!"}
        ]
        
        output = translate_bubbles_batch(input_items, manga_title="The_Ultimate_of_All_Ages")
        self.assertEqual(len(output), 3)
        
        # Verify 1-based sequential IDs match exactly
        self.assertEqual([item["id"] for item in output], [1, 2, 3])
        
        # Verify glossary term substitution in fallback/translation
        t2 = output[1]["translated"]
        t3 = output[2]["translated"]
        
        self.assertIn("Ли Юньсяо", t2)
        self.assertIn("Гу Фэйян", t2)
        self.assertIn("Боевой Владыка", t2)
        self.assertIn("Гу Фэйян", t3)
        self.assertIn("Гора Сюаньюань", t3)
        print("  [PASS] test_04_batch_json_translation_contract: Strict 1-based ID contract & glossary substitution verified.")

    def test_05_fallback_translate_xianxia_terms(self):
        """Verify offline fallback translation correctly replaces complex multi-word Xianxia terms."""
        glossary = load_manga_glossary("The_Ultimate_of_All_Ages")
        
        text1 = "A Yao Beast entered the Dantian of the Martial Sovereign!"
        translated1 = fallback_translate_text(text1, glossary=glossary)
        self.assertIn("Демонический Зверь", translated1)
        self.assertIn("Даньтянь", translated1)
        self.assertIn("Боевой Владыка", translated1)
        
        text2 = "Welcome to the Sanctuary of Heavenly Water Nation, Master!"
        translated2 = fallback_translate_text(text2, glossary=glossary)
        self.assertIn("Святилище", translated2)
        self.assertIn("Страна Небесной Воды", translated2)
        self.assertIn("Мастер", translated2)
        print("  [PASS] test_05_fallback_translate_xianxia_terms: Complex multi-word terms replaced correctly.")

if __name__ == "__main__":
    unittest.main()
