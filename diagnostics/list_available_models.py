import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

print("=== Checking Groq Models ===")
try:
    r = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        timeout=10
    )
    if r.status_code == 200:
        models = [m["id"] for m in r.json().get("data", [])]
        print(f"Groq Available Models ({len(models)}):")
        for m in sorted(models):
            print(f"  - {m}")
    else:
        print(f"Groq Models Error {r.status_code}: {r.text}")
except Exception as e:
    print(f"Groq error: {e}")

print("\n=== Checking NVIDIA NIM Models ===")
try:
    r = requests.get(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {NVIDIA_KEY}"},
        timeout=10
    )
    if r.status_code == 200:
        models = [m["id"] for m in r.json().get("data", [])]
        print(f"NVIDIA Available Models ({len(models)}):")
        # Print top 15 coding / general models
        for m in sorted(models)[:20]:
            print(f"  - {m}")
    else:
        print(f"NVIDIA Models Error {r.status_code}: {r.text}")
except Exception as e:
    print(f"NVIDIA error: {e}")

print("\n=== Checking Gemini Models ===")
try:
    r = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}",
        timeout=10
    )
    if r.status_code == 200:
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Gemini Available Models ({len(models)}):")
        for m in sorted(models):
            print(f"  - {m}")
    else:
        print(f"Gemini Models Error {r.status_code}: {r.text}")
except Exception as e:
    print(f"Gemini error: {e}")
