import os
import urllib.request
import json

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        models = json.loads(resp.read().decode('utf-8'))['data']
        free_models = [m['id'] for m in models if ':free' in m['id']]
        print(f"Found {len(free_models)} free models:")
        for m in free_models[:10]:
            print(" -", m)
except Exception as e:
    print("Error:", e)
