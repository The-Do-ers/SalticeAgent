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
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
LOCAL_URL = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434/v1").strip()

results = {}

def test_groq():
    print("\n--- Testing Groq API ---")
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    # Test models endpoint or simple completion
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Respond in 3 words: Ready to code."}],
        "max_tokens": 20
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            print(f"✅ Groq SUCCESS ({dt:.2f}s): {reply.strip()}")
            print(f"   Usage: {usage}")
            return {"status": "ok", "latency": dt, "reply": reply.strip(), "usage": usage}
        else:
            print(f"❌ Groq FAILED ({r.status_code}): {r.text}")
            return {"status": "error", "code": r.status_code, "error": r.text}
    except Exception as e:
        print(f"❌ Groq EXCEPTION: {e}")
        return {"status": "exception", "error": str(e)}

def test_nvidia():
    print("\n--- Testing NVIDIA NIM API ---")
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": "Respond in 3 words: Ready to code."}],
        "max_tokens": 20
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            print(f"✅ NVIDIA NIM SUCCESS ({dt:.2f}s): {reply.strip()}")
            print(f"   Usage: {usage}")
            return {"status": "ok", "latency": dt, "reply": reply.strip(), "usage": usage}
        else:
            print(f"❌ NVIDIA NIM FAILED ({r.status_code}): {r.text}")
            return {"status": "error", "code": r.status_code, "error": r.text}
    except Exception as e:
        print(f"❌ NVIDIA NIM EXCEPTION: {e}")
        return {"status": "exception", "error": str(e)}

def test_deepseek():
    print("\n--- Testing DeepSeek API ---")
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Respond in 3 words: Ready to code."}],
        "max_tokens": 20
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            print(f"✅ DeepSeek SUCCESS ({dt:.2f}s): {reply.strip()}")
            print(f"   Usage: {usage}")
            return {"status": "ok", "latency": dt, "reply": reply.strip(), "usage": usage}
        else:
            print(f"❌ DeepSeek FAILED ({r.status_code}): {r.text}")
            return {"status": "error", "code": r.status_code, "error": r.text}
    except Exception as e:
        print(f"❌ DeepSeek EXCEPTION: {e}")
        return {"status": "exception", "error": str(e)}

def test_gemini():
    print("\n--- Testing Gemini API ---")
    # Test 1: As query param key
    url1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": "Respond in 3 words: Ready to code."}]}]
    }
    t0 = time.time()
    try:
        r = requests.post(url1, json=payload, timeout=15)
        dt = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"✅ Gemini (API Key query) SUCCESS ({dt:.2f}s): {text.strip()}")
            return {"status": "ok", "method": "api_key", "latency": dt, "reply": text.strip()}
        else:
            print(f"⚠️ Gemini (API Key query) HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"⚠️ Gemini query exception: {e}")

    # Test 2: As Bearer token
    url2 = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"Authorization": f"Bearer {GEMINI_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.post(url2, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"✅ Gemini (Bearer token) SUCCESS: {text.strip()}")
            return {"status": "ok", "method": "bearer", "reply": text.strip()}
        else:
            print(f"❌ Gemini (Bearer token) HTTP {r.status_code}: {r.text[:200]}")
            return {"status": "error", "code": r.status_code, "error": r.text}
    except Exception as e:
        print(f"❌ Gemini Bearer exception: {e}")
        return {"status": "exception", "error": str(e)}

def test_local():
    print("\n--- Testing Local Model Endpoint ---")
    try:
        r = requests.get(f"{LOCAL_URL}/models", timeout=3)
        if r.status_code == 200:
            print(f"✅ Local Server running at {LOCAL_URL}: {r.json()}")
            return {"status": "ok", "models": r.json()}
        else:
            print(f"⚠️ Local server replied with {r.status_code}")
            return {"status": "error", "code": r.status_code}
    except Exception as e:
        print(f"ℹ️ Local server not currently active at {LOCAL_URL} ({e})")
        return {"status": "offline", "note": "Ollama or LM Studio not running on port 11434"}

if __name__ == "__main__":
    results["groq"] = test_groq()
    results["nvidia"] = test_nvidia()
    results["deepseek"] = test_deepseek()
    results["gemini"] = test_gemini()
    results["local"] = test_local()
    
    with open("key_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to key_test_results.json")
