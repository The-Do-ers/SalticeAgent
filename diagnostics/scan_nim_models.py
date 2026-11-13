import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

# Fetch all models
r = requests.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {NVIDIA_KEY}"},
    timeout=10
)
models = [m["id"] for m in r.json().get("data", [])]
print(f"Total models available: {len(models)}")

working_models = []

for m in models:
    try:
        t0 = time.time()
        res = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            },
            timeout=5
        )
        dt = time.time() - t0
        if res.status_code == 200:
            print(f"✅ NIM WORKING: {m} ({dt:.2f}s)")
            working_models.append(m)
            if len(working_models) >= 5:
                break
        else:
            err = res.json().get("title", "") or res.json().get("detail", "") or str(res.status_code)
            # print(f"❌ {m}: {err[:40]}")
    except Exception as e:
        pass

print("\n--- Summary of Working NVIDIA NIM Models ---")
for wm in working_models:
    print("  *", wm)
