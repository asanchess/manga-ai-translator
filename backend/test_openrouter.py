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

data = {
    "model": "meta-llama/llama-3.3-70b-instruct:free",
    "messages": [{"role": "user", "content": "Translate 'Hello Master' to Russian."}]
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        res = json.loads(response.read().decode('utf-8'))
        print("Success:", res)
except urllib.error.HTTPError as e:
    err_content = e.read().decode('utf-8')
    print("HTTP Error:", e.code, err_content)
except Exception as e:
    print("Other error:", e)
