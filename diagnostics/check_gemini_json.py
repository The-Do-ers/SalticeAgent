import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

r = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}",
    headers={"Content-Type": "application/json"},
    json={
        "contents": [{"parts": [{"text": "Hello, answer in 3 words."}]}],
    },
    timeout=15
)
print("Status:", r.status_code)
print("Response JSON:")
print(json.dumps(r.json(), indent=2))
