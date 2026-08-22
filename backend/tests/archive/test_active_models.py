import os
import urllib.request
import json
import urllib.error

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

test_models = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free"
]

for model in test_models:
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Переведи на русский язык реплику из боевой маньхуа: 'NO, IT'S NOT YAO TRANSFORMATION. THIS STATE IS MUCH MORE POWERFUL!!' Ответь только переводом."}
        ]
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            reply = res['choices'][0]['message']['content'].strip()
            print(f"Model [{model}] -> {reply}")
            break
    except Exception as e:
        print(f"Model [{model}] failed: {e}")
