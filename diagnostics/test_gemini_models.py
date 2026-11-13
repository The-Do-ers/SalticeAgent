import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

models = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite"
]

for m in models:
    t0 = time.time()
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": "Write a python function to compute factorial."}]}],
                "generationConfig": {"maxOutputTokens": 60}
            },
            timeout=10
        )
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            ans = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            tokens = data.get("usageMetadata", {}).get("candidatesTokenCount", 0)
            spd = tokens / dt if dt > 0 else 0
            print(f"✅ Gemini [{m}] SUCCESS: {dt:.2f}s | {tokens} tokens ({spd:.1f} tok/s)")
            print(f"Snippet: {ans[:70]}...\n")
        else:
            print(f"❌ Gemini [{m}] FAILED {r.status_code}: {r.text[:80]}\n")
    except Exception as e:
        print(f"ERR {m}: {e}\n")
