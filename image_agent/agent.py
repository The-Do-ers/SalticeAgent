"""
ImageAgent: Autonomous Multi-Model Image Generation Studio.
Orchestrates Gemini Prompt Enhancement, Parallel Hugging Face ZeroGPU Execution,
and Saltice-Inspired Vector SVG Logo Synthesis.
"""

import os
import re
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
try:
    from .intelligence import enhance_prompt, add_wordmark, validate_image_integrity, extract_brand_palette
    from .engines import ParallelImageGenerator, CloudflareAIClient
    from .svg_generator import SVGLogoGenerator
except ImportError:
    from intelligence import enhance_prompt, add_wordmark, validate_image_integrity, extract_brand_palette
    from engines import ParallelImageGenerator, CloudflareAIClient
    from svg_generator import SVGLogoGenerator


class ImageAgent:
    """Autonomous Image Generation Agent with Hybrid Diffusion & Vector SVG Engines."""

    DEFAULT_T2I_MODELS = [
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-dev",
        "stabilityai/stable-diffusion-3.5-large",
        "Tongyi-MAI/Z-Image-Turbo"
    ]

    DEFAULT_I2I_MODELS = [
        "black-forest-labs/FLUX.1-Kontext-dev",
        "Qwen/Qwen-Image-Edit",
        "black-forest-labs/FLUX.2-dev"
    ]

    def __init__(
        self,
        output_dir: Optional[str] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base_dir, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN", "")
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.generator = ParallelImageGenerator(output_dir=self.output_dir, token=self.hf_token)
        self.svg_generator = SVGLogoGenerator(output_dir=self.output_dir)
        self.cf_client = CloudflareAIClient(output_dir=self.output_dir)

    def generate_vector_logo(
        self,
        prompt: str,
        rasterize: bool = True
    ) -> Dict[str, Any]:
        """
        Generates a standalone vector SVG logo.
        Queries Gemini semantic vector synthesis, Iconify open-source vectors,
        or curated offline presets.
        """
        return self.svg_generator.generate_logo(prompt, rasterize_to_png=rasterize)

    def generate_cloudflare_image(
        self,
        prompt: str,
        model: str = "@cf/black-forest-labs/flux-1-schnell"
    ) -> Dict[str, Any]:
        """Directly invokes Cloudflare Workers AI edge GPU diffusion."""
        return self.cf_client.generate_image(prompt=prompt, model=model)

    def run(
        self,
        user_prompt: str,
        reference_image_path: Optional[str] = None,
        models: Optional[List[str]] = None,
        enhance: bool = True,
        generate_svg: bool = False,
        use_svg_as_reference: bool = False,
        use_cloudflare: bool = False,
        wordmark: Optional[str] = None,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Runs the complete end-to-end studio pipeline:
        1. Optional Vector SVG Logo generation (standalone or as diffusion reference)
        2. Prompt Enhancement via Gemini
        3. Parallel Multi-Model ZeroGPU Dispatch
        4. Persistence and Session Manifest Logging
        """
        start_time = datetime.now()
        svg_result = None

        # Auto-detect logo/icon intent if not explicitly set
        is_logo_intent = generate_svg or bool(
            re.search(r'\b(logo|icon|emblem|badge|brand mark|vector logo|svg)\b', user_prompt, re.IGNORECASE)
        )

        # 1. Generate Vector SVG if requested or detected
        if is_logo_intent:
            if progress_callback:
                progress_callback("generating_svg", user_prompt)
            svg_result = self.generate_vector_logo(user_prompt, rasterize=True)
            if progress_callback:
                progress_callback("svg_completed", svg_result)

            # If user wants to style the vector logo with diffusion or requested SVG reference
            if (use_svg_as_reference or generate_svg) and svg_result.get("png_reference_path"):
                if not reference_image_path:
                    reference_image_path = svg_result["png_reference_path"]

        is_i2i = bool(reference_image_path and os.path.exists(reference_image_path))

        # 2. Enhance Prompt
        if enhance:
            if progress_callback:
                progress_callback("enhancing_prompt", user_prompt)
            effective_prompt = enhance_prompt(
                raw_prompt=user_prompt,
                is_reference=is_i2i,
                api_key=self.gemini_key
            )
        else:
            effective_prompt = user_prompt

        # 3. Select Models
        if models and len(models) > 0:
            active_models = models
        else:
            active_models = self.DEFAULT_I2I_MODELS if is_i2i else self.DEFAULT_T2I_MODELS

        if progress_callback:
            progress_callback("dispatching_models", active_models)

        # 4. Parallel Diffusion Execution
        batch_res = self.generator.generate_parallel(
            prompt=effective_prompt,
            models=active_models,
            reference_image_path=reference_image_path if is_i2i else None,
            callback=progress_callback
        )

        # 4b. Cloudflare Edge Diffusion (Explicit or Automatic ZeroGPU Congestion Failover)
        if use_cloudflare or (batch_res["successful_count"] == 0 and self.cf_client.is_configured):
            if progress_callback:
                progress_callback("dispatching_cloudflare", "@cf/black-forest-labs/flux-1-schnell")
            cf_res = self.cf_client.generate_image(
                prompt=effective_prompt,
                model="@cf/black-forest-labs/flux-1-schnell"
            )
            if cf_res.get("success"):
                batch_res["results"].append({
                    "model": "Cloudflare-FLUX.1-schnell (Edge GPU)",
                    "success": True,
                    "file_path": cf_res.get("file_path"),
                    "duration_seconds": cf_res.get("duration_seconds"),
                    "provider": "Cloudflare Workers AI"
                })
                batch_res["successful_count"] += 1
                if progress_callback:
                    progress_callback("completed", "Cloudflare FLUX.1-schnell")

        # 4c. Optional Typography Wordmark Typesetting
        if wordmark and wordmark.strip():
            for item in batch_res.get("results", []):
                fp = item.get("file_path")
                if fp and os.path.exists(fp) and fp.endswith(".png"):
                    add_wordmark(fp, wordmark.strip())
                    item["wordmark_applied"] = wordmark.strip()

        total_duration = round((datetime.now() - start_time).total_seconds(), 2)

        # 5. Session Manifest
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_data = {
            "timestamp": timestamp,
            "original_prompt": user_prompt,
            "enhanced_prompt": effective_prompt,
            "reference_image": reference_image_path if is_i2i else None,
            "mode": "Image-to-Image (SVG Reference)" if (is_i2i and svg_result) else ("Image-to-Image" if is_i2i else "Text-to-Image"),
            "models_tested": active_models,
            "total_duration_seconds": total_duration,
            "successful_images": batch_res["successful_count"] + (1 if svg_result and svg_result.get("success") else 0),
            "svg_logo": svg_result,
            "results": batch_res["results"]
        }

        # If an SVG logo was created, prepend it to the results list
        if svg_result and svg_result.get("success"):
            manifest_data["results"].insert(0, {
                "model": f"Vector-SVG ({svg_result.get('source', 'engine')})",
                "success": True,
                "file_path": svg_result.get("svg_path"),
                "duration_seconds": svg_result.get("duration_seconds", 0.5),
                "type": "vector_svg"
            })

        manifest_file = os.path.join(self.output_dir, f"session_{timestamp}.json")
        try:
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
            manifest_data["manifest_path"] = manifest_file
        except Exception:
            pass

        return manifest_data


if __name__ == "__main__":
    agent = ImageAgent()
    print("Testing ImageAgent with SVG Logo Generator...")
    res = agent.run("Falcon Aerospace vector logo", generate_svg=True, models=["black-forest-labs/FLUX.1-schnell"])
    print(f"Agent finished. SVG: {bool(res.get('svg_logo'))}, Successful: {res['successful_images']}")
