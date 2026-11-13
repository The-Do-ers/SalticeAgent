import sys
import requests
import json
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CF_ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
COHERE_KEY = os.getenv("COHERE_API_KEY", "")

print("=== 1. Testing Cloudflare Token Verify ===")
try:
    rv = requests.get(
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        headers={"Authorization": f"Bearer {CF_TOKEN}"},
        timeout=10
    )
    print("Token Verify Status:", rv.status_code)
    print("Token Verify Response:", rv.json())
except Exception as e:
    print("Token Verify Exception:", e)

print("\n=== 2. Testing Cloudflare Workers AI Chat ===")
try:
    # Test Llama 3.1 8B or Llama 3.3 70B
    test_models = [
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3.3-70b-instruct",
        "@cf/qwen/qwen2.5-coder-32b-instruct"
    ]
    for tm in test_models:
        t0 = time.time()
        rc = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"},
            json={
                "model": tm,
                "messages": [{"role": "user", "content": "Hello in 3 words."}],
                "max_tokens": 15
            },
            timeout=15
        )
        dt = time.time() - t0
        if rc.status_code == 200:
            ans = rc.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ Cloudflare AI [{tm}] SUCCESS ({dt:.2f}s): {ans}")
            break
        else:
            print(f"❌ Cloudflare AI [{tm}] {rc.status_code}: {rc.text[:150]}")
except Exception as e:
    print("Cloudflare AI Exception:", e)

print("\n=== 3. Testing Cohere API ===")
try:
    # Test Cohere v2 chat
    t0 = time.time()
    rc = requests.post(
        "https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"},
        json={
            "model": "command-r-08-2024",
            "messages": [{"role": "user", "content": "Hello in 3 words."}],
            "max_tokens": 15
        },
        timeout=15
    )
    dt = time.time() - t0
    if rc.status_code == 200:
        ans = rc.json()["message"]["content"][0]["text"].strip()
        print(f"✅ Cohere v2 SUCCESS ({dt:.2f}s): {ans}")
    else:
        print(f"⚠️ Cohere v2 {rc.status_code}: {rc.text[:150]}")
        # Try Cohere v1 chat fallback
        rc1 = requests.post(
            "https://api.cohere.com/v1/chat",
            headers={"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"},
            json={"model": "command-r", "message": "Hello in 3 words.", "max_tokens": 15},
            timeout=15
        )
        if rc1.status_code == 200:
            ans = rc1.json()["text"].strip()
            print(f"✅ Cohere v1 SUCCESS: {ans}")
        else:
            print(f"❌ Cohere v1 {rc1.status_code}: {rc1.text[:150]}")
except Exception as e:
    print("Cohere Exception:", e)
