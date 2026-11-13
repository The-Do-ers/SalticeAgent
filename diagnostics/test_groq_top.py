import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()

models = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "groq/compound-mini"
]

for m in models:
    t0 = time.time()
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "Write a python function to compute factorial."}],
                "max_tokens": 60
            },
            timeout=10
        )
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            ans = data["choices"][0]["message"]["content"].strip()
            tokens = data.get("usage", {}).get("completion_tokens", 0)
            spd = tokens / dt if dt > 0 else 0
            print(f"✅ Groq [{m}] SUCCESS: {dt:.2f}s | {tokens} tokens ({spd:.1f} tok/s)")
            print(f"Snippet: {ans[:80]}...\n")
        else:
            print(f"❌ Groq [{m}] FAILED {r.status_code}: {r.text[:80]}\n")
    except Exception as e:
        print(f"ERR {m}: {e}\n")
