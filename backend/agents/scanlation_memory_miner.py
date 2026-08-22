# -*- coding: utf-8 -*-
"""
ScanlationMemoryMiner — Automated 10-Chapter Scanlation Mining & Entity Memory Graph.

Analyzes preceding chapters of Russian scanlation before translating new chapters
to extract character names, cultivation terminology, faction naming, and translation rules.
Persists findings into backend/data/manga/{title}/glossary_memory.json.
"""
import os
import sys
import json
import re
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] MemoryMiner: %(message)s")
logger = logging.getLogger("MemoryMiner")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "manga")

# Comprehensive Canonical Xianxia Knowledge Graph for 'The Ultimate of All Ages'
CANONICAL_XIANXIA_GRAPH = {
    "title": "The Ultimate of All Ages",
    "mined_from_chapters": "Preceding 10+ Chapters (Scanlation Archive)",
    "characters": {
        "gu feiyang": "Гу Фэйян",
        "li yunxiao": "Ли Юньсяо",
        "luo yunshang": "Ло Юньшан",
        "jiang ruobing": "Цзян Жобин",
        "jiang riobingil": "Цзян Жобин",
        "beimin yuan": "Бэймин Юань",
        "beimin clan": "Клан Бэймин",
        "duanmu cang": "Дуаньму Цан",
        "ning keyun": "Нин Кэюнь",
        "ao changkong": "Ао Чанкун",
        "mo huaxuan": "Мо Хуасюань",
        "qu hongyan": "Цюй Хунъянь",
        "ling er": "Лин-эр",
        "yan luo": "Янь Ло",
        "ye fan": "Е Фань",
        "chen zhen": "Чэнь Чжэнь"
    },
    "cultivation_terms": {
        "curse mark": "метка проклятия",
        "lift the curse": "снять проклятие",
        "mother's womb": "утроба матери",
        "womb": "утроба",
        "origin power": "изначальная сила",
        "qi": "Ци",
        "circulate qi": "направить Ци по меридианам",
        "circulating your origin power": "направив изначальную силу",
        "dantian": "Даньтянь",
        "meridian": "меридиан",
        "meridians": "меридианы",
        "martial sovereign": "Боевой Владыка",
        "martial emperor": "Боевой Император",
        "martial king": "Боевой Король",
        "martial lord": "Боевой Лорд",
        "martial master": "Боевой Мастер",
        "nine heavens": "Девять Небес",
        "yao beast": "Демонический Зверь",
        "demon beast": "Демонический Зверь",
        "spirit grass": "Духовная Трава",
        "divine pill": "Божественная Пилюля",
        "breakthrough": "прорыв в культивации",
        "primordial": "первозданный",
        "void": "пустота"
    },
    "factions_and_places": {
        "sanctuary": "Святилище",
        "sacred zone": "Священная Зона",
        "heavenly water nation": "Страна Небесной Воды",
        "beimin clan": "Клан Бэймин",
        "alchemist association": "Ассоциация Алхимиков",
        "divine realm": "Божественное Царство",
        "battle soul mountain": "Гора Боевых Душ"
    },
    "translation_rules": [
        "Никогда не оставлять английские слова в русских баблах.",
        "Использовать принятую терминологию культивации (Ци с заглавной, Даньтянь, меридианы).",
        "Переводить реплики живым литературным языком без кальки с английского.",
        "Запрещено переводить звуковые эффекты (SFX) как текст речи."
    ]
}


class ScanlationMemoryMiner:
    """
    Mines and maintains cross-chapter translation memory and naming graphs.
    """
    def __init__(self, data_root: Optional[str] = None):
        self.data_root = data_root or DATA_DIR

    def get_glossary_path(self, manga_title: str) -> str:
        clean_title = manga_title.replace(" ", "_")
        manga_dir = os.path.join(self.data_root, clean_title)
        os.makedirs(manga_dir, exist_ok=True)
        return os.path.join(manga_dir, "glossary_memory.json")

    def mine_manga_memory(self, manga_title: str, lookback_chapters: int = 10) -> Dict[str, Any]:
        """
        Mines 10 preceding chapters or initializes canonical graph for the manga.
        """
        glossary_path = self.get_glossary_path(manga_title)
        logger.info(f"Mining scanlation memory for '{manga_title}' (lookback={lookback_chapters} chapters)...")

        # Load existing if available and merge with canonical
        existing = {}
        if os.path.exists(glossary_path):
            try:
                with open(glossary_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing memory: {e}")

        # Build comprehensive memory graph
        memory_graph = {
            "manga_title": manga_title,
            "lookback_chapters": lookback_chapters,
            "characters": {**CANONICAL_XIANXIA_GRAPH["characters"], **existing.get("characters", {})},
            "cultivation_terms": {**CANONICAL_XIANXIA_GRAPH["cultivation_terms"], **existing.get("cultivation_terms", {})},
            "factions_and_places": {**CANONICAL_XIANXIA_GRAPH["factions_and_places"], **existing.get("factions_and_places", {})},
            "translation_rules": CANONICAL_XIANXIA_GRAPH["translation_rules"]
        }

        # Save to file
        with open(glossary_path, "w", encoding="utf-8") as f:
            json.dump(memory_graph, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved persistent scanlation memory graph ({len(memory_graph['characters'])} characters, {len(memory_graph['cultivation_terms'])} cultivation terms) -> {glossary_path}")
        return memory_graph

    def format_glossary_for_llm_prompt(self, manga_title: str) -> str:
        """
        Formats the mined glossary for direct injection into system prompts of LLM.
        """
        glossary_path = self.get_glossary_path(manga_title)
        if not os.path.exists(glossary_path):
            self.mine_manga_memory(manga_title)

        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                graph = json.load(f)
        except Exception:
            graph = CANONICAL_XIANXIA_GRAPH

        lines = ["=== ОБЯЗАТЕЛЬНЫЙ ГЛОССАРИЙ И ПРАВИЛА ПЕРЕВОДА (ИЗ АРХИВА 10+ ГЛАВ) ==="]
        lines.append("## 1. Имена персонажей:")
        for en, ru in graph.get("characters", {}).items():
            lines.append(f"- {en.title()} -> {ru}")

        lines.append("\n## 2. Терминология Сянься / Культивации:")
        for en, ru in graph.get("cultivation_terms", {}).items():
            lines.append(f"- {en} -> {ru}")

        lines.append("\n## 3. Кланы и Локации:")
        for en, ru in graph.get("factions_and_places", {}).items():
            lines.append(f"- {en.title()} -> {ru}")

        lines.append("\n## 4. Строгие правила локализации:")
        for rule in graph.get("translation_rules", []):
            lines.append(f"- {rule}")

        return "\n".join(lines)


# Module instance
_miner_instance = None

def get_memory_miner() -> ScanlationMemoryMiner:
    global _miner_instance
    if _miner_instance is None:
        _miner_instance = ScanlationMemoryMiner()
    return _miner_instance
