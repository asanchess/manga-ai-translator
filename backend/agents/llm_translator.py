# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import re
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LLMTranslatorAgent")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Active free models on OpenRouter with multi-provider fallback
MODEL_CASCADE = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-chat:free",
    "google/gemma-4-31b-it:free",
    "z-ai/glm-5.2:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-3-super-120b-a12b:free"
]

CACHE_FILE = os.path.join(os.path.dirname(__file__), "translations_db.json")

GLOSSARY_PROMPT = """
Ты — элитный переводчик и локализатор манги/маньхуа (культивация, сянься, уся) на русский язык.
Твоя задача — перевести реплики персонажей из манги максимально живо, эмоционально, с правильным сохранением характеров персонажей, боевого пафоса и юмора.

ГЛОССАРИЙ ИМЁН И ТЕРМИНОВ:
- Li Yunxiao / Yunxiao -> Ли Юньсяо (Главный герой, уверенный, саркастичный, великий мастер)
- Yang Chen -> Ян Чэнь
- Old Yuan -> Старый Юань
- Beiming Clan / Beiming Family -> Клан Бэймин
- Beiming Kang -> Бэймин Кан
- Beiming Gong -> Бэймин Гун
- Sanctuary -> Святилище
- Red Moon City -> Город Красной Луны
- Clear Bright Moon Pavilion -> Павильон Ясной Луны
- Martial Supreme / Emperor -> Боевой Владыка
- Earth Domain -> Домен Земли
- Profound Artifact -> Глубинный артефакт
- Yao Transformation -> Трансформация Демона
- Heavenly Soul Realm -> Сфера Небесной Души
- Divine Body -> Божественное тело
- Qi / True Essence -> Истинная Ци / Истинная сущность

ПРАВИЛА ПЕРЕВОДА:
1. Перевод должен быть естественным литературным русским языком с комиксной динамикой (без буквализма).
2. Длина реплики не должна быть избыточно длинной, чтобы текст комфортно помещался в бабл.
3. Сохраняй знаки препинания и эмоциональность (!, ?, ...).
4. Ты ПОЛУЧАЕШЬ JSON словарь с номерами баблов: {"bubble_1": "text", "bubble_2": "text", ...}.
5. Ты ДОЛЖЕН ВЕРНУТЬ СТРОГО ВАЛИДНЫЙ JSON с теми же ключами: {"bubble_1": "перевод", "bubble_2": "перевод", ...}. Без лишнего текста, без markdown обёрток!
"""

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

def lookup_in_db(raw_text: str, cache_data: dict) -> str:
    """Checks cache dictionary, structured dialogue pattern list, and SFX list."""
    clean_text = raw_text.strip()
    if not clean_text:
        return ""
    
    # 1. Direct dictionary match
    if clean_text in cache_data:
        return cache_data[clean_text]
        
    lower_text = re.sub(r'[^a-z0-9 ]', '', clean_text.lower()).strip()
    
    # 2. SFX dictionary match
    sfx_dict = cache_data.get("sfx", {})
    if lower_text in sfx_dict:
        return sfx_dict[lower_text]
    for s_k, s_v in sfx_dict.items():
        if s_k == lower_text or lower_text.startswith(s_k) or lower_text.endswith(s_k):
            return s_v
            
    # 3. Structured dialogue pattern list
    dialogues = cache_data.get("dialogue", [])
    for entry in dialogues:
        patterns = entry.get("patterns", [])
        for pat in patterns:
            pat_clean = re.sub(r'[^a-z0-9 ]', '', pat.lower()).strip()
            if pat_clean and (pat_clean in lower_text or lower_text in pat_clean):
                return entry.get("ru", "")
                
    return None

def check_ollama_available(timeout: float = 3.0) -> tuple:
    """Checks if local Ollama daemon is running with a strict timeout (3.0s)."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=timeout)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_name = models[0]["name"] if models else "llama3.2:3b"
            return True, model_name
    except Exception:
        pass
    return False, ""

def apply_rule_based_fallback(text: str) -> str:
    """Smart martial arts & conversational translation fallback"""
    text_lower = text.lower().strip()
    
    # Common battle SFX
    if "boom" in text_lower or "rumble" in text_lower:
        return "ГРОХОТ!!"
    if "slash" in text_lower or "swish" in text_lower:
        return "ВЖУХ!"
    if "clash" in text_lower or "clang" in text_lower:
        return "ДЗЫНЬ!"
    if "pant" in text_lower or "gasp" in text_lower:
        return "Хаа... Хаа..."
    if "cough" in text_lower:
        return "Кхе-кхе!"

    # Specific phrase replacements
    rules = [
        ("li yunxiao", "Ли Юньсяо"),
        ("yang chen", "Ян Чэнь"),
        ("old yuan", "Старый Юань"),
        ("beiming", "Бэймин"),
        ("sanctuary", "Святилище"),
        ("what?!", "Что?!"),
        ("how is this possible?!", "Как такое возможно?!"),
        ("impossible!", "Невозможно!"),
        ("damn it!", "Проклятье!"),
        ("die!", "Сдохни!"),
        ("court death!", "Ищешь смерти!"),
        ("martial supreme", "Боевой Владыка"),
        ("earth domain", "Домен Земли"),
        ("profound artifact", "Глубинный артефакт"),
    ]

    res = text
    for eng, rus in rules:
        if eng in res.lower():
            res = re.sub(re.escape(eng), rus, res, flags=re.IGNORECASE)
            
    if res != text:
        return res

    return text

def translate_bubbles_with_openrouter(bubbles_dict: dict) -> dict:
    """
    Translates a dictionary of { "bubble_X": "original english text" }
    using:
    1. Local database cache
    2. Local Ollama (with fast 3s connection check)
    3. OpenRouter Free Cascade
    4. Safe offline rule-based fallback
    """
    if not bubbles_dict:
        return {}

    cache = load_cache()
    result = {}
    missing_to_translate = {}

    # Check cache and pattern database first
    for key, text in bubbles_dict.items():
        matched = lookup_in_db(text, cache)
        if matched:
            result[key] = matched
        else:
            missing_to_translate[key] = text.strip()

    if not missing_to_translate:
        logger.info("All bubbles resolved from local translation cache & database.")
        return result

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://manga-translator.local",
        "X-Title": "Manga Agentic Scanlation Pipeline",
        "Content-Type": "application/json"
    }

    # Check local Ollama availability with 3.0s timeout
    ollama_ok, ollama_model = check_ollama_available(timeout=3.0)
    OLLAMA_URL = "http://localhost:11434/api/generate"
    
    missing_items = list(missing_to_translate.items())
    chunk_size = 8
    
    for i in range(0, len(missing_items), chunk_size):
        chunk_dict = dict(missing_items[i:i+chunk_size])
        user_payload = {
            "manga": "Manga Translation",
            "bubbles": chunk_dict
        }

        translated_chunk = None
        
        # 1. Try Local Ollama if available
        if ollama_ok:
            try:
                logger.info(f"Attempting translation via local Ollama (Model: {ollama_model})...")
                prompt_text = f"{GLOSSARY_PROMPT}\nПереведи следующие баблы в JSON:\n{json.dumps(user_payload, ensure_ascii=False)}"
                ollama_body = {
                    "model": ollama_model,
                    "prompt": prompt_text,
                    "stream": False,
                    "format": "json"
                }
                ollama_resp = requests.post(OLLAMA_URL, json=ollama_body, timeout=25)
                if ollama_resp.status_code == 200:
                    resp_json = ollama_resp.json()
                    content = resp_json.get("response", "").strip()
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        if "bubbles" in parsed and isinstance(parsed["bubbles"], dict):
                            parsed = parsed["bubbles"]
                        translated_chunk = parsed
                        logger.info(f"✓ Successful translation from local Ollama ({ollama_model}).")
            except Exception as e:
                logger.warning(f"Local Ollama failed: {e}")

        # 2. Fallback to OpenRouter Cloud API
        if not translated_chunk and OPENROUTER_API_KEY:
            for model in MODEL_CASCADE:
                logger.info(f"Translating chunk ({len(chunk_dict)} bubbles) via model: {model}...")
                try:
                    body = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": GLOSSARY_PROMPT},
                            {"role": "user", "content": f"Переведи следующие баблы в JSON:\n{json.dumps(user_payload, ensure_ascii=False)}"}
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    }

                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=body,
                        timeout=10
                    )

                    if resp.status_code == 200:
                        resp_json = resp.json()
                        content = resp_json["choices"][0]["message"]["content"].strip()
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                        
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            content = json_match.group(0)

                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            if "bubbles" in parsed and isinstance(parsed["bubbles"], dict):
                                parsed = parsed["bubbles"]
                            sanitized = {}
                            for bk, bv in parsed.items():
                                if isinstance(bv, str):
                                    bv = re.sub(r'[\ufffd\u25a0\u25a1\u25aa\u25ab]', '', bv)
                                    bv = re.sub(r'\[\s*\]', '', bv)
                                    bv = re.sub(r'\s+', ' ', bv).strip()
                                sanitized[bk] = bv
                            translated_chunk = sanitized
                            logger.info(f"✓ Successful translation from {model} for {len(translated_chunk)} bubbles.")
                            break
                except Exception as e:
                    logger.warning(f"Model {model} chunk failed: {e}")

        if translated_chunk:
            for k, v in translated_chunk.items():
                if k in chunk_dict:
                    clean_orig = chunk_dict[k]
                    result[k] = str(v)
                    cache[clean_orig] = str(v)
        else:
            for k, orig_val in chunk_dict.items():
                fb = apply_rule_based_fallback(orig_val)
                result[k] = fb
                cache[orig_val] = fb

    for k, orig_text in missing_to_translate.items():
        if k not in result:
            fallback_text = apply_rule_based_fallback(orig_text)
            result[k] = fallback_text
            cache[orig_text] = fallback_text

    save_cache(cache)
    return result

def translate_bubbles_batch(items: list) -> list:
    """
    Accepts a list of dicts: [{"id": 0, "text": "..."}, ...]
    Returns a list of dicts: [{"id": 0, "translated": "..."}]
    """
    if not items:
        return []
        
    payload_dict = {f"bubble_{item['id']}": item.get("text", "") for item in items}
    trans_map = translate_bubbles_with_openrouter(payload_dict)
    
    result = []
    for item in items:
        b_id = item["id"]
        key = f"bubble_{b_id}"
        result.append({
            "id": b_id,
            "translated": trans_map.get(key, item.get("text", ""))
        })
    return result

if __name__ == "__main__":
    print("LLM Translator Agent initialized.")
    is_up, mod = check_ollama_available()
    print(f"Ollama status: {'Running (' + mod + ')' if is_up else 'Not running (will use OpenRouter/Rule Fallback)'}")
