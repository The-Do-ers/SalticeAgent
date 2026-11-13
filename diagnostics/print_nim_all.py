import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

r = requests.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {NVIDIA_KEY}"},
    timeout=10
)
models = [m["id"] for m in r.json().get("data", [])]
print(f"Total NVIDIA models: {len(models)}")
for m in sorted(models):
    print(m)
