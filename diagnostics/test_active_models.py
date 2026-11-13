import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

print("--- Testing Groq with qwen/qwen3.8-27b ---")
try:
    t0 = time.time()
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={
            "model": "qwen/qwen3.8-27b",
            "messages": [{"role": "user", "content": "Write a python one-liner to reverse a string."}],
            "max_tokens": 50
        },
        timeout=10
    )
    dt = time.time() - t0
    if r.status_code == 200:
        res = r.json()
        text = res["choices"][0]["message"]["content"]
        tokens = res.get("usage", {}).get("completion_tokens", 0)
        speed = tokens / dt if dt > 0 else 0
        print(f"✅ Groq SUCCESS: {dt:.2f}s | {tokens} tokens ({speed:.1f} tok/s)")
        print(f"Reply: {text.strip()}\n")
    else:
        print(f"❌ Groq error {r.status_code}: {r.text}\n")
except Exception as e:
    print(f"❌ Groq exception: {e}\n")

print("--- Testing NVIDIA NIM with deepseek-ai/deepseek-coder-6.7b-instruct ---")
try:
    t0 = time.time()
    r = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-ai/deepseek-coder-6.7b-instruct",
            "messages": [{"role": "user", "content": "Write a python one-liner to reverse a string."}],
            "max_tokens": 50
        },
        timeout=15
    )
    dt = time.time() - t0
    if r.status_code == 200:
        res = r.json()
        text = res["choices"][0]["message"]["content"]
        tokens = res.get("usage", {}).get("completion_tokens", 0)
        speed = tokens / dt if dt > 0 else 0
        print(f"✅ NVIDIA NIM DeepSeek SUCCESS: {dt:.2f}s | {tokens} tokens ({speed:.1f} tok/s)")
        print(f"Reply: {text.strip()}\n")
    else:
        print(f"❌ NVIDIA NIM error {r.status_code}: {r.text}\n")
except Exception as e:
    print(f"❌ NVIDIA NIM exception: {e}\n")

print("--- Testing Gemini with gemini-2.5-flash ---")
try:
    t0 = time.time()
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
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
        print(f"✅ Gemini 2.5 Flash SUCCESS: {dt:.2f}s")
        print(f"Reply: {text.strip()}\n")
    else:
        print(f"❌ Gemini error {r.status_code}: {r.text}\n")
except Exception as e:
    print(f"❌ Gemini exception: {e}\n")
