import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

models = [
    "meta/llama-3.2-11b-vision-instruct",
    "meta/llama-3.2-90b-vision-instruct"
]

for m in models:
    t0 = time.time()
    r = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
        json={
            "model": m,
            "messages": [{"role": "user", "content": "Write a python function to add two numbers."}],
            "max_tokens": 50
        },
        timeout=15
    )
    dt = time.time() - t0
    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens", 0)
        speed = tokens / dt if dt > 0 else 0
        print(f"✅ NIM [{m}] SUCCESS: {dt:.2f}s | {tokens} tokens ({speed:.1f} tok/s)")
        print(f"Content:\n{content.strip()}\n")
    else:
        print(f"❌ NIM [{m}] FAILED {r.status_code}: {r.text[:100]}")
