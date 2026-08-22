# -*- coding: utf-8 -*-
"""
LLM Translator Agent with Strict JSON Schema Validation and ID Integrity Guard.
Supports Local Ollama (llama3.2:3b), OpenRouter Free Models, and Offline Glossary.
"""
import os
import re
import json
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LLMTranslatorAgent")

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free"
]

FALLBACK_GLOSSARY = {
    "hello": "Привет",
    "master": "Мастер",
    "die": "Умри!",
    "kill": "Убить!",
    "what": "Что?!",
    "impossible": "Невозможно...",
    "stop": "Стой!",
    "who": "Кто ты?",
    "scythescans": "",
    "chapter": "Глава"
}

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

def check_ollama_status() -> tuple[bool, str]:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3.0)
        if r.status_code == 200:
            models_data = r.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models_data]
            for m in models_data:
                full_name = m.get("name", "")
                if "llama3.2" in full_name or "llama3" in full_name or "qwen" in full_name:
                    return True, full_name
            if models_data:
                return True, models_data[0].get("name", OLLAMA_MODEL)
            return True, OLLAMA_MODEL
    except Exception:
        pass
    return False, ""

def extract_json_array(text: str) -> list:
    """
    Safely parses JSON array from model responses, stripping markdown code blocks.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()
        
    # Match JSON array [ ... ]
    arr_match = re.search(r"\[\s*\{.*?\}\s*\]", cleaned, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group(0))
        except Exception:
            pass
            
    # Try direct parse
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [{"id": k, "translated": v} for k, v in parsed.items()]
    except Exception:
        pass
        
    return []

def call_ollama_batch(items: list[dict], model: str) -> list[dict]:
    prompt = (
        "You are an expert manga/manhua translator into Russian.\n"
        "Translate each text bubble accurately and naturally into Russian with suitable tone.\n"
        "Input format: JSON array of objects with 'id' and 'text'.\n"
        "Output format: STRICT JSON array of objects with 'id' (integer) and 'translated' (string in Russian).\n"
        "IMPORTANT: You MUST include every single 'id' from the input in the output.\n"
        "Do NOT include explanations or markdown outside the JSON.\n\n"
        f"Input:\n{json.dumps(items, ensure_ascii=False, indent=2)}\n\n"
        "Output JSON:"
    )
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 1024
        }
    }
    
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=25.0)
    if resp.status_code == 200:
        raw_res = resp.json().get("response", "")
        return extract_json_array(raw_res)
    return []

def call_openrouter_batch(items: list[dict], api_key: str, model_name: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://manga-ai-translator.local",
        "X-Title": "Manga AI Translator"
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a manga translation engine. Translate speech bubbles into natural Russian. Output strictly a JSON array of objects with keys 'id' (int) and 'translated' (str). Every input ID must be translated."
        },
        {
            "role": "user",
            "content": f"Input:\n{json.dumps(items, ensure_ascii=False, indent=2)}"
        }
    ]
    
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024
    }
    
    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=20.0)
    if resp.status_code == 200:
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        return extract_json_array(raw_text)
    return []

def fallback_translate_text(text: str) -> str:
    """
    Offline fallback translation for a single bubble text.
    """
    clean_t = text.strip()
    if not clean_t:
        return ""
    words = clean_t.split()
    translated_words = []
    for w in words:
        w_low = re.sub(r'[^a-zA-Z]', '', w).lower()
        if w_low in FALLBACK_GLOSSARY:
            rep = FALLBACK_GLOSSARY[w_low]
            translated_words.append(rep if rep else w)
        else:
            translated_words.append(w)
            
    res = " ".join(translated_words)
    if res == clean_t:
        # If no words changed, add punctuation formatting
        return clean_t.upper() if clean_t.isupper() else clean_t
    return res

def translate_bubbles_batch(items: list[dict]) -> list[dict]:
    """
    Strict batch translation function.
    Input:  [{"id": 1, "text": "Hello master!"}, ...]
    Output: [{"id": 1, "translated": "Привет, мастер!"}, ...]
    Guarantees every input ID is present in the returned list.
    """
    if not items:
        return []
        
    input_ids = [item["id"] for item in items]
    results_map = {}
    
    # 1. Check local persistent translation cache
    cache = load_translations_cache()
    missing_items = []
    
    for item in items:
        b_id = item["id"]
        raw_text = item["text"].strip()
        if not raw_text:
            results_map[b_id] = ""
            continue
        if raw_text in cache:
            results_map[b_id] = cache[raw_text]
        else:
            missing_items.append(item)
            
    if not missing_items:
        logger.info("All bubbles resolved from local translation cache.")
        return [{"id": i_id, "translated": results_map.get(i_id, "")} for i_id in input_ids]
        
    # 2. Try Local Ollama if available
    ollama_ok, ollama_model = check_ollama_status()
    if ollama_ok and missing_items:
        try:
            logger.info(f"Attempting translation via local Ollama ({ollama_model})...")
            llm_results = call_ollama_batch(missing_items, ollama_model)
            for res in llm_results:
                if isinstance(res, dict) and "id" in res and "translated" in res:
                    res_id = res["id"]
                    try:
                        res_id = int(res_id)
                    except Exception:
                        pass
                    trans_text = str(res["translated"]).strip()
                    if trans_text:
                        results_map[res_id] = trans_text
                        for orig in missing_items:
                            if orig["id"] == res_id:
                                cache[orig["text"].strip()] = trans_text
            save_translations_cache(cache)
        except Exception as e:
            logger.warning(f"Local Ollama attempt failed: {e}")
            
    # Check if any IDs still missing
    still_missing = [item for item in items if item["id"] not in results_map or not results_map[item["id"]]]
    
    # 3. Try OpenRouter free models if API key exists
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if still_missing and openrouter_api_key:
        for model in OPENROUTER_FREE_MODELS:
            try:
                logger.info(f"Attempting OpenRouter translation via model: {model}...")
                or_results = call_openrouter_batch(still_missing, openrouter_api_key, model)
                for res in or_results:
                    if isinstance(res, dict) and "id" in res and "translated" in res:
                        res_id = res["id"]
                        try:
                            res_id = int(res_id)
                        except Exception:
                            pass
                        trans_text = str(res["translated"]).strip()
                        if trans_text:
                            results_map[res_id] = trans_text
                            for orig in still_missing:
                                if orig["id"] == res_id:
                                    cache[orig["text"].strip()] = trans_text
                save_translations_cache(cache)
                still_missing = [item for item in items if item["id"] not in results_map or not results_map[item["id"]]]
                if not still_missing:
                    break
            except Exception as e:
                logger.warning(f"OpenRouter model {model} failed: {e}")
                
    # 4. Offline Fallback for any remaining unmapped IDs
    for item in items:
        b_id = item["id"]
        if b_id not in results_map or not results_map[b_id]:
            fb_text = fallback_translate_text(item["text"])
            results_map[b_id] = fb_text
            cache[item["text"].strip()] = fb_text
            
    save_translations_cache(cache)
    
    # Assemble final guaranteed array
    final_output = []
    for item in items:
        b_id = item["id"]
        final_output.append({
            "id": b_id,
            "translated": results_map.get(b_id, item["text"])
        })
        
    return final_output

def translate_bubbles_with_openrouter(bubbles: dict) -> dict:
    """
    Legacy dictionary interface for backward compatibility:
    Input:  {"bubble_1": "Hello", ...}
    Output: {"bubble_1": "Привет", ...}
    """
    items = []
    key_to_id = {}
    for idx, (k, txt) in enumerate(bubbles.items(), 1):
        items.append({"id": idx, "text": txt})
        key_to_id[idx] = k
        
    translated_items = translate_bubbles_batch(items)
    out_dict = {}
    for item in translated_items:
        k = key_to_id.get(item["id"], f"bubble_{item['id']}")
        out_dict[k] = item["translated"]
    return out_dict

if __name__ == "__main__":
    print("LLM Translator Agent ready.")
