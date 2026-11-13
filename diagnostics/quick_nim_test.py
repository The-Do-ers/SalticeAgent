import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

models_to_test = [
    "deepseek-ai/deepseek-r1",
    "qwen/qwen2.5-coder-32b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "mistralai/mistral-large-2407",
    "nvidia/nemotron-4-340b-instruct",
    "google/gemma-2-9b-it",
    "google/gemma-2-27b-it",
    "microsoft/phi-3-mini-4k-instruct",
    "microsoft/phi-3-medium-4k-instruct"
]

for m in models_to_test:
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "1+1="}],
                "max_tokens": 5
            },
            timeout=4
        )
        if r.status_code == 200:
            ans = r.json()["choices"][0]["message"]["content"].strip()
            print(f"SUCCESS: {m} -> {ans}", flush=True)
        else:
            print(f"FAILED {r.status_code}: {m} -> {r.text[:90]}", flush=True)
    except Exception as e:
        print(f"ERR: {m} -> {e}", flush=True)
