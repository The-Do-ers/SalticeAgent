import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()

def test_stream(model):
    print(f"Testing streaming for {model}...", flush=True)
    t0 = time.time()
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Count from 1 to 5."}],
                "stream": True,
                "max_tokens": 30
            },
            stream=True,
            timeout=30
        )
        if r.status_code != 200:
            print(f"FAILED {r.status_code}: {r.text[:100]}", flush=True)
            return
            
        first_token_time = None
        full_text = ""
        chunk_count = 0
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            if first_token_time is None:
                                first_token_time = time.time() - t0
                            full_text += delta
                            chunk_count += 1
                    except Exception:
                        pass
        total_time = time.time() - t0
        print(f"✅ SUCCESS: TTFT={first_token_time:.2f}s, Total={total_time:.2f}s, Chunks={chunk_count}")
        print(f"Text: {full_text.strip()}\n", flush=True)
    except Exception as e:
        print(f"Error {model}: {e}\n", flush=True)

test_stream("meta/llama-3.2-90b-vision-instruct")
