import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

print("=== Testing Gemini with gemini-3.6-flash ===")
try:
    t0 = time.time()
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": "Write a python one-liner to reverse a string."}]}],
            "generationConfig": {"maxOutputTokens": 50}
        },
        timeout=15
    )
    dt = time.time() - t0
    if r.status_code == 200:
        res = r.json()
        text = res["candidates"][0]["content"]["parts"][0]["text"]
        print(f"✅ Gemini 3.6 Flash SUCCESS: {dt:.2f}s")
        print(f"Reply: {text.strip()}\n")
    else:
        print(f"❌ Gemini 3.6 Flash error {r.status_code}: {r.text}\n")
except Exception as e:
    print(f"❌ Gemini exception: {e}\n")


print("=== Testing NVIDIA NIM Candidate Models ===")
candidate_models = [
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "deepseek-ai/deepseek-v4-flash-0731",
    "google/codegemma-7b",
    "ibm/granite-34b-code-instruct",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "01-ai/yi-large",
    "google/gemma-3-12b-it",
    "google/gemma-4-31b-it"
]

for m in candidate_models:
    try:
        t0 = time.time()
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "Hello in 2 words."}],
                "max_tokens": 10
            },
            timeout=10
        )
        dt = time.time() - t0
        if r.status_code == 200:
            res = r.json()
            reply = res["choices"][0]["message"]["content"].strip()
            print(f"✅ NIM [{m}] SUCCESS ({dt:.2f}s): {reply}")
        else:
            print(f"❌ NIM [{m}] {r.status_code}: {r.json().get('detail', r.text[:80])}")
    except Exception as e:
        print(f"❌ NIM [{m}] exception: {e}")
