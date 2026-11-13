import sys
import requests
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "")
SAMBANOVA_KEY = os.getenv("SAMBANOVA_API_KEY", "")

print("=== 1. Testing Mistral API ===")
try:
    r = requests.get("https://api.mistral.ai/v1/models", headers={"Authorization": f"Bearer {MISTRAL_KEY}"}, timeout=10)
    print("Mistral Models Status:", r.status_code)
    if r.status_code == 200:
        models = [m["id"] for m in r.json().get("data", [])]
        print(f"Mistral Models ({len(models)}):", models[:10])
        # Test completion
        rc = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
            json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10},
            timeout=10
        )
        print("Mistral Completion Status:", rc.status_code)
        if rc.status_code == 200:
            print("Mistral Reply:", rc.json()["choices"][0]["message"]["content"].strip())
        else:
            print("Mistral Completion Error:", rc.text[:200])
    else:
        print("Mistral Error:", r.text[:200])
except Exception as e:
    print("Mistral Exception:", e)

print("\n=== 2. Testing SambaNova Cloud API ===")
try:
    r = requests.get("https://api.sambanova.ai/v1/models", headers={"Authorization": f"Bearer {SAMBANOVA_KEY}"}, timeout=10)
    print("SambaNova Models Status:", r.status_code)
    if r.status_code == 200:
        models = [m["id"] for m in r.json().get("data", [])]
        print(f"SambaNova Models ({len(models)}):", models[:10])
        # Test completion
        test_model = models[0] if models else "Meta-Llama-3.1-70B-Instruct"
        rc = requests.post(
            "https://api.sambanova.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {SAMBANOVA_KEY}", "Content-Type": "application/json"},
            json={"model": test_model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10},
            timeout=10
        )
        print("SambaNova Completion Status:", rc.status_code)
        if rc.status_code == 200:
            print(f"SambaNova ({test_model}) Reply:", rc.json()["choices"][0]["message"]["content"].strip())
        else:
            print("SambaNova Completion Error:", rc.text[:200])
    else:
        print("SambaNova Error:", r.text[:200])
except Exception as e:
    print("SambaNova Exception:", e)
