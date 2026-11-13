"""
Unified LLM Provider Client with Dynamic Rate-Limit Shield & Load Balancing
Supports:
1. Groq (Qwen 3.8 27B / GPT-OSS 20B)
2. Mistral AI (Codestral Latest)
3. Cloudflare Workers AI (@cf/qwen/qwen2.5-coder-32b-instruct)
4. NVIDIA NIM (Llama 3.2 11B Vision)
5. Google Gemini (Gemini 3.6 Flash)
6. Cohere (Command R 08-2024)
7. SambaNova Cloud (Meta Llama 3.3 70B)
8. Local Server (Qwencoder 7B 4-bit)

Features:
- Rate-Limit Shield: Tracks cooldowns when 429s are encountered
- Automatic failover across healthy providers
- Accurate token metrics and latency recording
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
# Always load assistant API keys from multi_agent_cli/.env first
load_dotenv(os.path.join(CLI_DIR, ".env"))
# Also load any local .env in the current working directory
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
SAMBANOVA_KEY = os.getenv("SAMBANOVA_API_KEY", "").strip()
COHERE_KEY = os.getenv("COHERE_API_KEY", "").strip()
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
CEREBRAS_KEY = os.getenv("CEREBRAS_API_KEY", "").strip()
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "").strip()
LOCAL_URL = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434/v1").strip()
LOCAL_MODEL = os.getenv("LOCAL_MODEL_NAME", "qwencoder:7b-4bit").strip()

class RateLimitShield:
    """Tracks provider cooldowns to avoid hammering rate-limited APIs."""
    def __init__(self):
        self.cooldowns = {}  # {provider_name: cooldown_until_timestamp}

    def mark_rate_limited(self, provider: str, cooldown_seconds: int = 40):
        until = time.time() + cooldown_seconds
        self.cooldowns[provider] = until

    def is_available(self, provider: str) -> bool:
        if provider not in self.cooldowns:
            return True
        if time.time() > self.cooldowns[provider]:
            del self.cooldowns[provider]
            return True
        return False

    def get_remaining_cooldown(self, provider: str) -> int:
        if provider in self.cooldowns:
            rem = int(self.cooldowns[provider] - time.time())
            return max(0, rem)
        return 0

SHIELD = RateLimitShield()

class ProviderStats:
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_calls = 0
        self.total_time = 0.0

    def record(self, prompt_tokens: int, completion_tokens: int, duration: float):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_calls += 1
        self.total_time += duration

    def summary(self):
        avg_speed = (self.total_completion_tokens / self.total_time) if self.total_time > 0 else 0
        return {
            "calls": self.total_calls,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_time_seconds": round(self.total_time, 2),
            "avg_tokens_per_second": round(avg_speed, 1)
        }

GLOBAL_STATS = ProviderStats()

def call_groq(messages: list, model: str = "qwen/qwen3.8-27b", max_tokens: int = 8192, temperature: float = 0.2):
    if not SHIELD.is_available("groq"):
        raise RuntimeError(f"Groq is on cooldown ({SHIELD.get_remaining_cooldown('groq')}s remaining)")
    
    t0 = time.time()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0
    
    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "groq", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code == 429:
        SHIELD.mark_rate_limited("groq", cooldown_seconds=45)
        raise RuntimeError(f"Groq Rate Limit (429): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"Groq error {r.status_code}: {r.text}")

def call_mistral(messages: list, model: str = "codestral-latest", max_tokens: int = 8192, temperature: float = 0.2):
    if not SHIELD.is_available("mistral"):
        raise RuntimeError(f"Mistral is on cooldown ({SHIELD.get_remaining_cooldown('mistral')}s remaining)")

    t0 = time.time()
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0

    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "mistral", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code == 429:
        SHIELD.mark_rate_limited("mistral", cooldown_seconds=45)
        raise RuntimeError(f"Mistral Rate Limit (429): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"Mistral error {r.status_code}: {r.text}")

def call_cloudflare_ai(messages: list, model: str = "@cf/qwen/qwen2.5-coder-32b-instruct", max_tokens: int = 1500, temperature: float = 0.2):
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        raise RuntimeError("Cloudflare Account ID or API Token not configured")
    if not SHIELD.is_available("cloudflare"):
        raise RuntimeError(f"Cloudflare AI is on cooldown ({SHIELD.get_remaining_cooldown('cloudflare')}s remaining)")

    t0 = time.time()
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0

    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0) or (len(content.split()) * 4 // 3)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "cloudflare", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code == 429:
        SHIELD.mark_rate_limited("cloudflare", cooldown_seconds=45)
        raise RuntimeError(f"Cloudflare Rate Limit (429): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"Cloudflare error {r.status_code}: {r.text}")

def call_nvidia_nim(messages: list, model: str = "meta/llama-3.2-11b-vision-instruct", max_tokens: int = 1500, temperature: float = 0.2):
    if not SHIELD.is_available("nvidia_nim"):
        raise RuntimeError(f"NVIDIA NIM is on cooldown ({SHIELD.get_remaining_cooldown('nvidia_nim')}s remaining)")

    t0 = time.time()
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature, "stream": True}
    r = requests.post(url, headers=headers, json=payload, timeout=45, stream=True)
    
    if r.status_code == 429:
        SHIELD.mark_rate_limited("nvidia_nim", cooldown_seconds=45)
        raise RuntimeError(f"NVIDIA NIM Rate Limit (429): Placed on cooldown for 45s.")
    if r.status_code != 200:
        raise RuntimeError(f"NVIDIA NIM error {r.status_code}: {r.text}")

    full_content = ""
    for line in r.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        full_content += delta
                except Exception:
                    pass
    dt = time.time() - t0
    ct = len(full_content.split()) * 4 // 3
    pt = sum(len(m.get("content", "").split()) for m in messages) * 4 // 3
    GLOBAL_STATS.record(pt, ct, dt)
    return {"content": full_content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "nvidia_nim", "speed": (ct/dt) if dt>0 else 0}

def call_gemini(messages: list, model: str = "gemini-flash-latest", max_tokens: int = 8192, temperature: float = 0.2):
    if not SHIELD.is_available("gemini"):
        raise RuntimeError(f"Gemini is on cooldown ({SHIELD.get_remaining_cooldown('gemini')}s remaining)")

    t0 = time.time()
    contents = []
    for m in messages:
        role = "user" if m.get("role") in ["user", "system"] else "model"
        contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}}
    r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
    dt = time.time() - t0

    if r.status_code == 200:
        data = r.json()
        candidates = data.get("candidates", [])
        cand = candidates[0]
        parts = cand.get("content", {}).get("parts", [])
        content = ""
        for p in parts:
            if "text" in p:
                content += p["text"]
        if not content and cand.get("finishReason"):
            content = f"[Response finished with reason: {cand.get('finishReason')}]"
        meta = data.get("usageMetadata", {})
        pt = meta.get("promptTokenCount", 0)
        ct = meta.get("candidatesTokenCount", 0) or (len(content.split()) * 4 // 3)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "gemini", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code in [429, 503]:
        SHIELD.mark_rate_limited("gemini", cooldown_seconds=45)
        raise RuntimeError(f"Gemini Unavailable ({r.status_code}): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"Gemini error {r.status_code}: {r.text}")

def call_cohere(messages: list, model: str = "command-r-08-2024", max_tokens: int = 1500, temperature: float = 0.2):
    if not SHIELD.is_available("cohere"):
        raise RuntimeError(f"Cohere is on cooldown ({SHIELD.get_remaining_cooldown('cohere')}s remaining)")

    t0 = time.time()
    url = "https://api.cohere.com/v2/chat"
    headers = {"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"}
    
    formatted_messages = []
    for m in messages:
        role = "user" if m.get("role") == "user" else "assistant"
        if m.get("role") == "system":
            role = "system"
        formatted_messages.append({"role": role, "content": m.get("content", "")})

    payload = {"model": model, "messages": formatted_messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0

    if r.status_code == 200:
        data = r.json()
        parts = data.get("message", {}).get("content", [])
        content = parts[0].get("text", "") if parts else ""
        meta = data.get("usage", {}).get("tokens", {})
        pt = meta.get("input_tokens", 0)
        ct = meta.get("output_tokens", 0)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "cohere", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code == 429:
        SHIELD.mark_rate_limited("cohere", cooldown_seconds=45)
        raise RuntimeError(f"Cohere Rate Limit (429): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"Cohere error {r.status_code}: {r.text}")

def call_sambanova(messages: list, model: str = "Meta-Llama-3.3-70B-Instruct", max_tokens: int = 1500, temperature: float = 0.2):
    if not SHIELD.is_available("sambanova"):
        raise RuntimeError(f"SambaNova is on cooldown ({SHIELD.get_remaining_cooldown('sambanova')}s remaining)")
    t0 = time.time()
    url = "https://api.sambanova.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {SAMBANOVA_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0
    if r.status_code == 200:
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        GLOBAL_STATS.record(pt, ct, dt)
        return {"content": content, "prompt_tokens": pt, "completion_tokens": ct, "duration": dt, "model": model, "provider": "sambanova", "speed": (ct/dt) if dt>0 else 0}
    elif r.status_code == 429:
        SHIELD.mark_rate_limited("sambanova", cooldown_seconds=45)
        raise RuntimeError(f"SambaNova Rate Limit (429): Placed on cooldown for 45s.")
    else:
        raise RuntimeError(f"SambaNova error {r.status_code}: {r.text}")

def call_openrouter(messages: list, model: str = "cohere/north-mini-code:free", max_tokens: int = 4000, temperature: float = 0.2):
    if not OPENROUTER_KEY:
        raise RuntimeError("OpenRouter API Key not configured in .env")
    if not SHIELD.is_available("openrouter"):
        raise RuntimeError(f"OpenRouter is on cooldown ({SHIELD.get_remaining_cooldown('openrouter')}s remaining)")

    t0 = time.time()
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com/antigravity-cli",
        "X-Title": "Saltice Autonomous Agent",
        "Content-Type": "application/json"
    }

    model_chain = [model]
    for alt in [
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3.5-lightning:free",
        "z-ai/glm-5.2:free",
        "nex-agi/nex-n2.5-pro:free",
        "openrouter/free"
    ]:
        if alt not in model_chain:
            model_chain.append(alt)

    last_error = None
    for target_model in model_chain:
        payload = {"model": target_model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=18)
            dt = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or msg.get("reasoning") or ""
                if not content:
                    last_error = f"Empty content from {target_model}"
                    continue
                usage = data.get("usage", {})
                pt = usage.get("prompt_tokens", 0)
                ct = usage.get("completion_tokens", 0) or (len(content.split()) * 4 // 3)
                GLOBAL_STATS.record(pt, ct, dt)
                return {
                    "content": content,
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "duration": dt,
                    "model": target_model,
                    "provider": "openrouter",
                    "speed": (ct / dt) if dt > 0 else 0
                }
            elif r.status_code == 429:
                last_error = f"OpenRouter Rate Limit on {target_model}"
                continue
            else:
                last_error = f"OpenRouter error {r.status_code}: {r.text[:80]}"
                continue
        except Exception as e:
            last_error = str(e)
            continue

    SHIELD.mark_rate_limited("openrouter", cooldown_seconds=45)
    raise RuntimeError(f"OpenRouter failed across free models: {last_error}")

def call_cerebras(messages: list, model: str = "qwen-3.8-27b", max_tokens: int = 3500, temperature: float = 0.2):
    """
    Cerebras Cloud Ultra-Fast Wafer-Scale Inference.
    Available models: 'qwen-3.8-27b', 'gpt-oss-120b'
    """
    if not CEREBRAS_KEY:
        raise RuntimeError("Cerebras API Key not configured in .env")
    if not SHIELD.is_available("cerebras"):
        raise RuntimeError(f"Cerebras is on cooldown ({SHIELD.get_remaining_cooldown('cerebras')}s remaining)")

    t0 = time.time()
    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_KEY}",
        "Content-Type": "application/json"
    }

    model_chain = [model]
    for alt in ["qwen-3.8-27b", "gpt-oss-120b"]:
        if alt not in model_chain:
            model_chain.append(alt)

    last_error = None
    for target_model in model_chain:
        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            dt = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or msg.get("reasoning") or ""
                if not content:
                    last_error = f"Empty content from {target_model}"
                    continue
                usage = data.get("usage", {})
                pt = usage.get("prompt_tokens", 0)
                ct = usage.get("completion_tokens", 0) or (len(content.split()) * 4 // 3)
                GLOBAL_STATS.record(pt, ct, dt)
                return {
                    "content": content,
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "duration": dt,
                    "model": target_model,
                    "provider": "cerebras",
                    "speed": (ct / dt) if dt > 0 else 0
                }
            elif r.status_code == 429:
                SHIELD.mark_rate_limited("cerebras", cooldown_seconds=45)
                last_error = f"Cerebras Rate Limit on {target_model}"
                break
            elif r.status_code == 402:
                raise RuntimeError("Cerebras requires billing activation: Visit cloud.cerebras.ai billing tab to claim free credits.")
            else:
                last_error = f"Cerebras error {r.status_code}: {r.text[:80]}"
                continue
        except RuntimeError:
            raise
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"Cerebras call failed: {last_error}")

_HF_MODEL_COOLDOWNS = {}

def call_huggingface(messages: list, model: str = "Qwen/Qwen2.5-Coder-32B-Instruct", max_tokens: int = 8192, temperature: float = 0.2):
    """
    Hugging Face Serverless Inference API (Router).
    Supported free models:
    - 'Qwen/Qwen2.5-Coder-32B-Instruct' (Dedicated state-of-the-art coder)
    - 'meta-llama/Llama-3.3-70B-Instruct' (70B reasoning powerhouse)
    - 'deepseek-ai/DeepSeek-V4.1-Flash' (1M context reasoning model)
    - 'Qwen/Qwen3.8-27B' (27B Coder)
    - 'meta-llama/Llama-3.1-8B-Instruct' (Ultra-reliable generalist)
    """
    if not HUGGINGFACE_TOKEN:
        raise RuntimeError("Hugging Face Token not configured in .env")
    if not SHIELD.is_available("huggingface"):
        raise RuntimeError(f"Hugging Face is on cooldown ({SHIELD.get_remaining_cooldown('huggingface')}s remaining)")

    t0 = time.time()
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
        "Content-Type": "application/json"
    }

    model_chain = [model]
    for alt in [
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct",
        "deepseek-ai/DeepSeek-V4.1-Flash",
        "Qwen/Qwen3.8-27B",
        "meta-llama/Llama-3.1-8B-Instruct"
    ]:
        if alt not in model_chain:
            model_chain.append(alt)

    now = time.time()
    available_chain = [m for m in model_chain if _HF_MODEL_COOLDOWNS.get(m, 0) < now]
    if not available_chain:
        available_chain = sorted(model_chain, key=lambda m: _HF_MODEL_COOLDOWNS.get(m, 0))

    last_error = None
    rate_limited_count = 0
    for target_model in available_chain:
        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=65)
            dt = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or msg.get("reasoning_content") or ""
                if not content:
                    last_error = f"Empty content from {target_model}"
                    continue
                usage = data.get("usage", {})
                pt = usage.get("prompt_tokens", 0)
                ct = usage.get("completion_tokens", 0) or (len(content.split()) * 4 // 3)
                GLOBAL_STATS.record(pt, ct, dt)
                return {
                    "content": content,
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "duration": dt,
                    "model": target_model,
                    "provider": "huggingface",
                    "speed": (ct / dt) if dt > 0 else 0
                }
            elif r.status_code == 429:
                _HF_MODEL_COOLDOWNS[target_model] = time.time() + 45
                rate_limited_count += 1
                last_error = f"Hugging Face Rate Limit on {target_model}"
                continue
            else:
                last_error = f"Hugging Face error {r.status_code}: {r.text[:80]}"
                continue
        except Exception as e:
            last_error = str(e)
            continue

    if rate_limited_count >= len(available_chain):
        SHIELD.mark_rate_limited("huggingface", cooldown_seconds=30)

    raise RuntimeError(f"Hugging Face call failed across models: {last_error}")

def call_local_model(messages: list, model: str = None, max_tokens: int = 2500, temperature: float = 0.2):
    """
    Execute inference against a local model server (Ollama or LM Studio).
    Auto-discovers running endpoints on port 11434 (Ollama) or port 1234 (LM Studio),
    and auto-detects installed models if the configured model name differs.
    """
    target_model = model or LOCAL_MODEL
    candidate_urls = []
    if LOCAL_URL:
        candidate_urls.append(LOCAL_URL.rstrip("/"))
    for fallback_url in ["http://localhost:11434/v1", "http://localhost:1234/v1"]:
        if fallback_url not in candidate_urls:
            candidate_urls.append(fallback_url)

    last_error = None
    for base_url in candidate_urls:
        endpoint = f"{base_url}/chat/completions"
        t0 = time.time()
        active_model = target_model
        try:
            payload = {"model": active_model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
            r = requests.post(endpoint, json=payload, timeout=60)
            
            # If model name not found (404), auto-query /models to find available models on this server
            if r.status_code == 404:
                try:
                    models_res = requests.get(f"{base_url}/models", timeout=5)
                    if models_res.status_code == 200:
                        m_data = models_res.json()
                        avail = [m.get("id") for m in m_data.get("data", []) if m.get("id")]
                        if avail:
                            active_model = avail[0]
                            payload["model"] = active_model
                            r = requests.post(endpoint, json=payload, timeout=60)
                except Exception:
                    pass

            dt = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"].get("content") or ""
                usage = data.get("usage", {})
                pt = usage.get("prompt_tokens", 0)
                ct = usage.get("completion_tokens", 0) or (len(content.split()) * 4 // 3)
                GLOBAL_STATS.record(pt, ct, dt)
                return {
                    "content": content,
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "duration": dt,
                    "model": active_model,
                    "provider": "local",
                    "speed": (ct / dt) if dt > 0 else 0
                }
            else:
                last_error = f"{base_url} returned HTTP {r.status_code}: {r.text[:120]}"
                continue
        except requests.exceptions.ConnectionError:
            last_error = f"Cannot connect to {base_url} (server not running)"
            continue
        except Exception as ex:
            last_error = f"{base_url} error: {ex}"
            continue

    raise RuntimeError(
        f"Local model server offline: {last_error}\n"
        "[Offline Setup Guide]:\n"
        "   1. Start Ollama ('ollama run qwen2.5-coder:7b' or launch Ollama desktop), OR\n"
        "   2. Start LM Studio Local Server (port 1234).\n"
        "   Check that LOCAL_MODEL_URL in SalticeAgent/.env points to your local server."
    )

def call_llm(messages: list, preferred_provider: str = "gemini", max_tokens: int = 8192, temperature: float = 0.2, allowed_providers: list = None):
    """
    Intelligent rate-shielded router with automatic fallback chain across all configured providers.
    Order of preference: preferred_provider -> gemini -> mistral -> huggingface -> groq -> cloudflare -> openrouter -> nvidia_nim -> cohere -> local -> cerebras
    """
    all_providers = ["gemini", "mistral", "huggingface", "groq", "cloudflare", "openrouter", "nvidia_nim", "cohere", "local", "cerebras", "sambanova"]
    
    if allowed_providers:
        active_list = [p for p in allowed_providers if p in all_providers]
    else:
        active_list = all_providers

    providers_chain = []
    if preferred_provider in active_list:
        providers_chain.append(preferred_provider)
    for p in active_list:
        if p not in providers_chain:
            providers_chain.append(p)

    errors = []
    for prov in providers_chain:
        try:
            if prov == "cerebras":
                return call_cerebras(messages, model="qwen-3.8-27b", max_tokens=max_tokens, temperature=temperature)
            elif prov == "huggingface":
                return call_huggingface(messages, model="Qwen/Qwen2.5-Coder-32B-Instruct", max_tokens=max_tokens, temperature=temperature)
            elif prov == "openrouter":
                return call_openrouter(messages, model="nex-agi/nex-n2.5-pro:free", max_tokens=max_tokens, temperature=temperature)
            elif prov == "mistral":
                return call_mistral(messages, model="codestral-latest", max_tokens=max_tokens, temperature=temperature)
            elif prov == "cloudflare":
                return call_cloudflare_ai(messages, model="@cf/qwen/qwen2.5-coder-32b-instruct", max_tokens=max_tokens, temperature=temperature)
            elif prov == "gemini":
                return call_gemini(messages, model="gemini-flash-latest", max_tokens=max_tokens, temperature=temperature)
            elif prov == "groq":
                return call_groq(messages, model="qwen/qwen3.8-27b", max_tokens=max_tokens, temperature=temperature)
            elif prov == "nvidia_nim":
                return call_nvidia_nim(messages, model="meta/llama-3.2-11b-vision-instruct", max_tokens=max_tokens, temperature=temperature)
            elif prov == "cohere":
                return call_cohere(messages, model="command-r-08-2024", max_tokens=max_tokens, temperature=temperature)
            elif prov == "local":
                return call_local_model(messages, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            errors.append(f"{prov}: {str(e)}")
            continue

    raise RuntimeError(f"All available providers failed or are rate-limited:\n" + "\n".join(errors))

