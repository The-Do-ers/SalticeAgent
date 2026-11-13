"""
ImageAgent Unified Engines Module.
Consolidates all visual synthesis backends:
1. HFSpacesClient: Hugging Face ZeroGPU Spaces client with circuit-breaker failover.
2. CloudflareAIClient: Cloudflare Workers AI serverless GPU edge client (< 2.5s latency).
3. ParallelImageGenerator: Concurrent multi-model executor using ThreadPoolExecutor.
"""

import os
import io
import time
import json
import base64
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Multi-path .env loader
def _load_env_keys():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(agent_dir, ".env"),
        os.path.abspath(os.path.join(agent_dir, "..", "..", ".env")),
        os.path.abspath(os.path.join(agent_dir, "..", ".env")),
        os.path.join(os.getcwd(), ".env")
    ]
    for c in candidates:
        if os.path.exists(c):
            load_dotenv(dotenv_path=c, override=False)

_load_env_keys()

DEFAULT_HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
DEFAULT_CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
DEFAULT_CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")


# ─────────────────────────────────────────────────────────────────────────────
# 1. CLOUDFLARE WORKERS AI CLIENT (Edge GPU Acceleration)
# ─────────────────────────────────────────────────────────────────────────────

class CloudflareAIClient:
    """Cloudflare Workers AI Serverless Image Synthesis Client."""

    DEFAULT_MODELS = [
        "@cf/black-forest-labs/flux-1-schnell",
        "@cf/bytedance/stable-diffusion-xl-lightning"
    ]

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        _load_env_keys()
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID") or DEFAULT_CF_ACCOUNT_ID
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN") or DEFAULT_CF_API_TOKEN
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base_dir, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        return bool(self.account_id and self.api_token)

    def generate_image(
        self,
        prompt: str,
        model: str = "@cf/black-forest-labs/flux-1-schnell",
        output_path: Optional[str] = None,
        timeout: int = 25
    ) -> Dict[str, Any]:
        """Executes text-to-image synthesis on Cloudflare Workers AI edge GPUs."""
        if not self.is_configured:
            return {"success": False, "error": "Cloudflare credentials not configured in .env", "model": model}

        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        slug = model.split("/")[-1].replace("-", "_")

        if not output_path:
            filename = f"{timestamp}_CF_{slug}.png"
            output_path = os.path.join(self.output_dir, filename)

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        payload = {"prompt": prompt}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            duration = round((datetime.now() - start_time).total_seconds(), 2)

            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    data = resp.json()
                    img_b64 = data.get("result", {}).get("image")
                    if img_b64:
                        img_bytes = base64.b64decode(img_b64)
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        return {
                            "success": True, "model": model, "image_path": output_path,
                            "duration_seconds": duration, "backend": "Cloudflare Workers AI",
                            "file_size_bytes": len(img_bytes)
                        }
                else:
                    img_bytes = resp.content
                    if len(img_bytes) > 500:
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        return {
                            "success": True, "model": model, "image_path": output_path,
                            "duration_seconds": duration, "backend": "Cloudflare Workers AI",
                            "file_size_bytes": len(img_bytes)
                        }

            return {
                "success": False, "model": model, "duration_seconds": duration,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}"
            }
        except Exception as e:
            return {"success": False, "model": model, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# 2. HUGGING FACE ZEROGPU SPACES CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class HFSpacesClient:
    """Interacts with Hugging Face Spaces running state-of-the-art diffusion models."""

    DEFAULT_SPACES = {
        "black-forest-labs/FLUX.1-schnell": "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-dev": "black-forest-labs/FLUX.1-dev",
        "stabilityai/stable-diffusion-3.5-large": "stabilityai/stable-diffusion-3.5-large",
        "Tongyi-MAI/Z-Image-Turbo": "Tongyi-MAI/Z-Image-Turbo",
        "black-forest-labs/FLUX.1-Kontext-dev": "black-forest-labs/FLUX.1-Kontext-dev",
        "Qwen/Qwen-Image-Edit": "Qwen/Qwen-Image-Edit"
    }

    def __init__(self, token: Optional[str] = None):
        _load_env_keys()
        self.token = token or os.path.getenv("HUGGINGFACE_TOKEN") or DEFAULT_HF_TOKEN

    def generate_text_to_image(
        self,
        model_id: str,
        prompt: str,
        output_path: str,
        seed: int = 0,
        randomize_seed: bool = True,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: Optional[int] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Generates an image via Hugging Face Spaces Gradio Client with circuit-breaker failover."""
        start_time = datetime.now()
        space_name = self.DEFAULT_SPACES.get(model_id, model_id)

        try:
            from gradio_client import Client
            client = Client(space_name, hf_token=self.token)
            
            # Predict based on space signature
            if "schnell" in model_id.lower():
                result = client.predict(
                    prompt=prompt, seed=seed, randomize_seed=randomize_seed,
                    width=width, height=height, num_inference_steps=num_inference_steps or 4,
                    api_name="/infer"
                )
            elif "dev" in model_id.lower():
                result = client.predict(
                    prompt=prompt, seed=seed, randomize_seed=randomize_seed,
                    width=width, height=height, guidance_scale=3.5,
                    num_inference_steps=num_inference_steps or 28,
                    api_name="/infer"
                )
            elif "stable-diffusion-3.5" in model_id.lower():
                result = client.predict(
                    prompt=prompt, negative_prompt="", seed=seed,
                    randomize_seed=randomize_seed, width=width, height=height,
                    guidance_scale=4.5, num_inference_steps=num_inference_steps or 28,
                    api_name="/infer"
                )
            elif "z-image-turbo" in model_id.lower():
                result = client.predict(
                    prompt=prompt, seed=seed, randomize_seed=randomize_seed,
                    width=width, height=height, api_name="/generate"
                )
            else:
                result = client.predict(prompt=prompt, api_name="/infer")

            temp_path = result[0] if isinstance(result, (list, tuple)) else result
            if temp_path and os.path.exists(temp_path):
                img = Image.open(temp_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                img.save(output_path)
                duration = round((datetime.now() - start_time).total_seconds(), 2)
                return {
                    "success": True, "model": model_id, "image_path": output_path,
                    "duration_seconds": duration, "fallback_used": False, "backend": "ZeroGPU Spaces"
                }

        except Exception as e:
            # Automatic Failover to Cloudflare or Pollinations
            cf = CloudflareAIClient()
            if cf.is_configured:
                cf_res = cf.generate_image(prompt=prompt, output_path=output_path)
                if cf_res.get("success"):
                    cf_res["fallback_used"] = True
                    return cf_res

            # Secondary failover via Pollinations
            fb_res = self._fallback_generate(prompt, output_path, model_id)
            if fb_res.get("success"):
                duration = round((datetime.now() - start_time).total_seconds(), 2)
                fb_res["duration_seconds"] = duration
                fb_res["fallback_used"] = True
                return fb_res

            return {"success": False, "model": model_id, "error": str(e), "fallback_used": False}

    def _fallback_generate(self, prompt: str, output_path: str, model_id: str) -> Dict[str, Any]:
        """Pollinations high-speed unmetered fallback."""
        try:
            import urllib.parse
            encoded = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return {
                    "success": True, "model": model_id, "image_path": output_path,
                    "backend": "Pollinations Failover Engine"
                }
        except Exception as e:
            pass
        return {"success": False, "error": "All primary and failover image engines exhausted."}


# ─────────────────────────────────────────────────────────────────────────────
# 3. PARALLEL MULTI-MODEL DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

class ParallelImageGenerator:
    """Dispatches multiple diffusion model requests concurrently."""

    DEFAULT_MODELS = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-3.5-large",
        "Tongyi-MAI/Z-Image-Turbo"
    ]

    def __init__(self, token: Optional[str] = None, output_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base_dir, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.client = HFSpacesClient(token=token)
        self.cf_client = CloudflareAIClient(output_dir=self.output_dir)

    def generate_parallel(
        self,
        prompt: str,
        models: Optional[List[str]] = None,
        use_cf: bool = False
    ) -> Dict[str, Any]:
        """Generates images across multiple models simultaneously."""
        models_to_run = models or self.DEFAULT_MODELS
        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        results = []
        with ThreadPoolExecutor(max_workers=len(models_to_run)) as executor:
            future_to_model = {}
            for m in models_to_run:
                slug = m.split("/")[-1].replace(".", "_")
                out_path = os.path.join(self.output_dir, f"{timestamp}_{slug}.png")
                if use_cf or m.startswith("@cf/"):
                    f = executor.submit(self.cf_client.generate_image, prompt=prompt, model=m, output_path=out_path)
                else:
                    f = executor.submit(self.client.generate_text_to_image, model_id=m, prompt=prompt, output_path=out_path)
                future_to_model[f] = m

            for future in as_completed(future_to_model):
                res = future.result()
                results.append(res)

        total_duration = round((datetime.now() - start_time).total_seconds(), 2)
        successful = [r for r in results if r.get("success")]

        return {
            "prompt": prompt,
            "timestamp": timestamp,
            "total_duration_seconds": total_duration,
            "requested_count": len(models_to_run),
            "successful_count": len(successful),
            "results": results
        }
