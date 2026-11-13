import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

models_to_test = [
    "mistralai/codestral-22b-instruct-v0.1",
    "ibm/granite-8b-code-instruct",
    "nv-mistralai/mistral-nemo-12b-instruct",
    "nvidia/mistral-nemo-minitron-8b-8k-instruct",
    "meta/llama-3.2-11b-vision-instruct",
    "mistralai/mistral-large-2-instruct",
    "openai/gpt-oss-20b",
    "z-ai/glm-5.3-flash"
]

for m in models_to_test:
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "print('ok')"}],
                "max_tokens": 10
            },
            timeout=8
        )
        if r.status_code == 200:
            print(f"✅ NIM SUCCESS: {m} -> {r.json()['choices'][0]['message']['content'].strip()}", flush=True)
        else:
            print(f"❌ NIM FAILED ({r.status_code}): {m} -> {r.text[:80]}", flush=True)
    except Exception as e:
        print(f"ERR {m}: {e}", flush=True)
