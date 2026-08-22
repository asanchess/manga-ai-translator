# -*- coding: utf-8 -*-
import sys
import requests
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://localhost:11434/api/generate'
payload = {
    'model': 'llama3.2:3b',
    'prompt': 'Translate this manga dialogue to Russian in JSON: {"bubble_1": "Impossible! He deflected my strike with one finger!"}',
    'format': 'json',
    'stream': False
}

try:
    r = requests.post(url, json=payload, timeout=20)
    print("Ollama Response:")
    print(r.json().get("response"))
except Exception as e:
    print("Ollama Error:", e)
