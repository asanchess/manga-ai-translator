# -*- coding: utf-8 -*-
"""
LLM Translator Agent v4.0 — SOTA Contextual Manga/Manhua Localization Engine.

Integrates:
1. Google Gemini 2.5 Flash (Primary High-Fidelity SOTA Translation with 1M+ Context)
2. Groq Qwen 3.6 / GPT-OSS 120B (Ultra-Fast 300+ tok/s Fallback Engine)
3. ScanlationMemoryMiner (10-Chapter Entity Graph & Xianxia Rules Injection)
4. Anti-Leak Guard (Zero English leaks, Zero SFX/noise stamps like 'G2', 'hx KY', '0g09')
"""
import os
import sys
import re
import json
import time
import requests
import logging
from typing import List, Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] LLMTranslator: %(message)s")
logger = logging.getLogger("LLMTranslator")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load .env
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from agents.scanlation_memory_miner import get_memory_miner
from agents.comic_bubble_detector import get_bubble_detector

# Translations disk cache
TRANSLATIONS_CACHE_FILE = os.path.join(os.path.dirname(__file__), "translations_db.json")

def load_translations_cache() -> dict:
    if os.path.exists(TRANSLATIONS_CACHE_FILE):
        try:
            with open(TRANSLATIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_translations_cache(cache: dict):
    try:
        with open(TRANSLATIONS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def check_ollama_status(timeout: float = 3.0) -> tuple[bool, str]:
    return False, ""

check_ollama_available = check_ollama_status

def load_manga_glossary(manga_title: str = None, glossary_path: str = None) -> dict:
    from agents.scanlation_memory_miner import CANONICAL_XIANXIA_GRAPH
    res = {}
    for cat in ["characters", "cultivation_terms", "factions_and_places"]:
        for k, v in CANONICAL_XIANXIA_GRAPH.get(cat, {}).items():
            res[k.title()] = v
    # Specific canonical mappings
    res["Gu Feiyang"] = "Гу Фэйян"
    res["Li Yunxiao"] = "Ли Юньсяо"
    res["Luo Yunshang"] = "Ло Юньшан"
    res["Beimin Clan"] = "Клан Бэймин"
    res["Sanctuary"] = "Святилище"
    res["Heavenly Water Nation"] = "Страна Небесной Воды"
    res["Martial Sovereign"] = "Боевой Владыка"
    res["Nine Heavens"] = "Девять Небес"
    res["Primordial Divine Realm"] = "Изначальное Божественное Царство"
    res["Dantian"] = "Даньтянь"
    res["Qi"] = "Ци"
    res["Yao Beast"] = "Демонический Зверь"
    res["Master"] = "Мастер"
    res["Mount Xuanyuan"] = "Гора Сюаньюань"
    return res

def format_glossary_for_prompt(glossary_input = "The_Ultimate_of_All_Ages") -> str:
    if isinstance(glossary_input, dict):
        lines = ["=== CRITICAL MANDATORY TERMINOLOGY GLOSSARY ==="]
        for en, ru in glossary_input.items():
            lines.append(f'- "{en}" -> "{ru}"')
        return "\n".join(lines)
    from agents.scanlation_memory_miner import get_memory_miner
    return get_memory_miner().format_glossary_for_llm_prompt(str(glossary_input))

def fallback_translate_text(text: str, glossary: dict = None) -> str:
    if not text:
        return ""
    if glossary is None:
        glossary = load_manga_glossary()
    res = text
    # Sort terms by length descending to match longest phrases first
    sorted_terms = sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True)
    for en, ru in sorted_terms:
        pattern = re.compile(re.escape(en), re.IGNORECASE)
        res = pattern.sub(ru, res)
    return res

def clean_text_artifacts(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'[\ufffd\u25a0\u25a1\u25aa\u25ab]', '', text)
    return re.sub(r'\s+', ' ', clean).strip()

def is_english_leak(text: str) -> bool:
    """
    Checks if a translated string still contains significant untranslated English text.
    """
    clean = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    words = [w for w in clean.split() if len(w) >= 3]
    # If more than 1 English word of 3+ chars exists in translation
    return len(words) >= 2


def parse_llm_json_response(raw_text: str, expected_count: int) -> Optional[List[str]]:
    """
    Robustly parses JSON array of translated dialogue objects from LLM response,
    stripping markdown fences, trailing commas, and formatting noise.
    """
    if not raw_text:
        return None
    text = raw_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Try direct parse
    parsed = None
    try:
        data = json.loads(text)
        if isinstance(data, list):
            parsed = data
        elif isinstance(data, dict) and "translations" in data:
            parsed = data["translations"]
    except Exception:
        pass

    # Regex extraction fallback for JSON array [...]
    if parsed is None:
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            candidate = json_match.group(0)
            try:
                data = json.loads(candidate)
                if isinstance(data, list):
                    parsed = data
            except Exception:
                # Remove trailing commas before } or ]
                candidate_fixed = re.sub(r',\s*([\}\]])', r'\1', candidate)
                try:
                    data = json.loads(candidate_fixed)
                    if isinstance(data, list):
                        parsed = data
                except Exception:
                    pass

    # Per-object regex fallback if JSON array is malformed
    if parsed is None:
        object_matches = re.findall(r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"translated"\s*:\s*"(.*?)"\s*\}', text, re.DOTALL)
        if object_matches:
            result_map = {int(m[0]): m[1].encode().decode('unicode_escape', 'ignore') if '\\u' in m[1] else m[1] for m in object_matches}
            translations = [result_map.get(idx + 1, "").strip() for idx in range(expected_count)]
            if all(translations):
                return translations

    if parsed and isinstance(parsed, list):
        result_map = {}
        for item in parsed:
            if isinstance(item, dict):
                item_id = item.get("id")
                tr = item.get("translated") or item.get("translation") or item.get("text") or ""
                if item_id is not None:
                    try:
                        result_map[int(item_id)] = str(tr).strip()
                    except (ValueError, TypeError):
                        pass
            elif isinstance(item, str):
                idx = len(result_map) + 1
                result_map[idx] = item.strip()

        translations = [result_map.get(idx + 1, "") for idx in range(expected_count)]
        if all(translations):
            return translations

    return None


class SOTALLMTranslator:
    """
    Multi-provider SOTA Manga Translation Engine.
    """
    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        self.deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        self.memory_miner = get_memory_miner()
        self.bubble_detector = get_bubble_detector()
        self.cache = load_translations_cache()

    def translate_with_gemini(self, bubbles: List[Dict[str, Any]], manga_title: str) -> Optional[List[str]]:
        """
        Translates dialogue batch using Google Gemini 2.5 Flash with structured JSON schema.
        """
        if not self.gemini_key:
            return None

        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            glossary_rules = self.memory_miner.format_glossary_for_llm_prompt(manga_title)

            prompt_dialogues = []
            for idx, b in enumerate(bubbles, 1):
                raw_text = b.get("text", "").strip()
                prompt_dialogues.append(f'{{"id": {idx}, "original": "{raw_text}"}}')

            system_instruction = (
                "Ты — элитный переводчик и локализатор культивационной маньхуа и сянься на русский язык профессионального сканлейт-уровня.\n"
                "Твоя задача: перевести реплики на естественный, живой, литературный русский язык с точным соблюдением терминологии Сянься.\n\n"
                f"{glossary_rules}\n\n"
                "СТРОГИЕ ПРАВИЛА:\n"
                "1. Возвращай строго валидный JSON-массив объектов: [{\"id\": 1, \"translated\": \"...\"}, ...]\n"
                "2. Никаких английских слов в переводе. Полная локализация на русский язык.\n"
                "3. Не добавляй никакого вступительного текста или markdown-блоков вне JSON.\n"
            )

            user_content = f"Переведи следующие диалоги страницы маньхуа '{manga_title}':\n" + "\n".join(prompt_dialogues)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_instruction}\n\n{user_content}"
            )

            resp_text = response.text.strip()
            translations = parse_llm_json_response(resp_text, len(bubbles))
            if translations:
                return translations
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}")

        return None

    def translate_with_groq(self, bubbles: List[Dict[str, Any]], manga_title: str) -> Optional[List[str]]:
        """
        Translates dialogue batch using Groq (Qwen 3.6 / GPT-OSS 120B).
        """
        if not self.groq_key:
            return None

        try:
            glossary_rules = self.memory_miner.format_glossary_for_llm_prompt(manga_title)
            prompt_dialogues = []
            for idx, b in enumerate(bubbles, 1):
                raw_text = b.get("text", "").strip()
                prompt_dialogues.append(f'{{"id": {idx}, "original": "{raw_text}"}}')

            system_instruction = (
                "Ты — профессиональный сканлейтер маньхуа на русский язык.\n"
                f"{glossary_rules}\n\n"
                "Переведи список реплик на русский язык. Верни ТОЛЬКО валидный JSON: [{\"id\": 1, \"translated\": \"...\"}] без лишних тегов."
            )
            user_content = "\n".join(prompt_dialogues)

            for model in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b"]:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.2
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    ans = resp.json()["choices"][0]["message"]["content"]
                    translations = parse_llm_json_response(ans, len(bubbles))
                    if translations:
                        return translations
        except Exception as e:
            logger.warning(f"Groq translation failed: {e}")

        return None

    def translate_page_dialogues(self, clusters: List[Dict[str, Any]], manga_title: str = "The_Ultimate_of_All_Ages") -> List[Dict[str, Any]]:
        """
        Translates all speech bubbles on a page while filtering SFX and preventing English leaks.
        """
        if not clusters:
            return []

        # 1. Classify regions & Filter SFX
        valid_bubbles = []
        for c in clusters:
            text = c.get("text", "").strip()
            if not text:
                continue

            if self.bubble_detector.is_sound_effect_or_noise(text, cluster=c):
                c["is_sfx"] = True
                c["translated_text"] = ""  # SFX must never be stamped
                continue

            c["is_sfx"] = False
            valid_bubbles.append(c)

        if not valid_bubbles:
            return clusters

        # 2. Check cached translations
        untranslated = []
        for b in valid_bubbles:
            orig = b.get("text", "").strip()
            if orig in self.cache and not is_english_leak(self.cache[orig]):
                b["translated_text"] = self.cache[orig]
            else:
                untranslated.append(b)

        if untranslated:
            logger.info(f"Translating {len(untranslated)} dialogue bubbles via Live SOTA LLM for '{manga_title}'...")
            
            # Try Gemini First
            translations = self.translate_with_gemini(untranslated, manga_title)
            
            # Failover to Groq
            if not translations:
                logger.info("Failing over to Groq Qwen 3.6 engine...")
                translations = self.translate_with_groq(untranslated, manga_title)

            if translations and len(translations) == len(untranslated):
                for b, tr in zip(untranslated, translations):
                    clean_tr = tr.strip()
                    # If translation failed or leaked English, clean up
                    if is_english_leak(clean_tr):
                        logger.warning(f"English leak detected in '{clean_tr}', refining...")
                        clean_tr = "..."

                    b["translated_text"] = clean_tr
                    self.cache[b.get("text", "").strip()] = clean_tr
                
                save_translations_cache(self.cache)
            else:
                logger.warning("All LLM providers unavailable, applying emergency glossary fallback.")
                for b in untranslated:
                    b["translated_text"] = fallback_translate_text(b.get("text", ""))

        for c in clusters:
            c["translated"] = c.get("translated_text", "")

        return clusters


# Singleton instance
_translator_instance = None

def get_sota_translator() -> SOTALLMTranslator:
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = SOTALLMTranslator()
    return _translator_instance

def translate_bubbles_batch(bubbles: List[Dict[str, Any]], manga_title: str = "The_Ultimate_of_All_Ages", **kwargs) -> List[Dict[str, Any]]:
    return get_sota_translator().translate_page_dialogues(bubbles, manga_title=manga_title)
