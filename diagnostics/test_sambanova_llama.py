import sys
import requests
import json
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "")
SAMBANOVA_KEY = os.getenv("SAMBANOVA_API_KEY", "")

print("--- Testing SambaNova: Meta-Llama-3.3-70B-Instruct ---")
try:
    t0 = time.time()
    rc = requests.post(
        "https://api.sambanova.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {SAMBANOVA_KEY}", "Content-Type": "application/json"},
        json={"model": "Meta-Llama-3.3-70B-Instruct", "messages": [{"role": "user", "content": "Say hello in 3 words."}], "max_tokens": 15},
        timeout=10
    )
    dt = time.time() - t0
    if rc.status_code == 200:
        ans = rc.json()["choices"][0]["message"]["content"].strip()
        print(f"✅ SambaNova SUCCESS ({dt:.2f}s): {ans}")
    else:
        print(f"❌ SambaNova Error {rc.status_code}: {rc.text[:200]}")
except Exception as e:
    print("SambaNova exception:", e)

print("\n--- Testing Mistral: codestral-latest ---")
try:
    t0 = time.time()
    rc = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
        json={"model": "codestral-latest", "messages": [{"role": "user", "content": "def add(a, b):"}], "max_tokens": 15},
        timeout=10
    )
    dt = time.time() - t0
    if rc.status_code == 200:
        ans = rc.json()["choices"][0]["message"]["content"].strip()
        print(f"✅ Mistral Codestral SUCCESS ({dt:.2f}s): {ans}")
    else:
        print(f"❌ Mistral Codestral Error {rc.status_code}: {rc.text[:200]}")
except Exception as e:
    print("Mistral exception:", e)
