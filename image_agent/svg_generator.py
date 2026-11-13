"""
SVG Logo & Vector Generator for ImageAgent.
Inspired by SalticeAgent's Vector Asset Engine.

Provides:
1. LLM-Powered Semantic SVG Logo Synthesis via Gemini 3.1 Flash Lite.
2. Iconify Open-Source Vector Registry Query (200,000+ free vectors, 0 API keys).
3. Curated Offline Logo & Emblem Presets (works completely offline).
4. Direct .svg export and optional SVG-to-PNG rasterization for Diffusion Reference Mode.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
import requests

def _load_env_keys():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(agent_dir, ".env"),
        os.path.abspath(os.path.join(agent_dir, "..", ".env")),
        os.path.abspath(os.path.join(agent_dir, "..", "..", ".env")),
        os.path.join(os.getcwd(), ".env")
    ]
    for c in candidates:
        if os.path.exists(c):
            load_dotenv(dotenv_path=c, override=False)

_load_env_keys()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


# ─────────────────────────────────────────────────────────────────────────────
# CURATED OFFLINE LOGO & EMBLEM PRESETS
# ─────────────────────────────────────────────────────────────────────────────

CURATED_LOGO_PRESETS = {
    "falcon": {
        "viewBox": "0 0 512 512",
        "description": "Cybernetic sleek falcon predator emblem with swept aerodynamic wings",
        "elements": """
            <defs>
                <linearGradient id="gradFalcon" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#38bdf8"/>
                    <stop offset="50%" stop-color="#0284c7"/>
                    <stop offset="100%" stop-color="#0369a1"/>
                </linearGradient>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="12" result="blur"/>
                    <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                </filter>
            </defs>
            <rect width="512" height="512" rx="100" fill="#090d16"/>
            <circle cx="256" cy="256" r="210" fill="none" stroke="rgba(56, 189, 248, 0.2)" stroke-width="4"/>
            <circle cx="256" cy="256" r="185" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="2" stroke-dasharray="10 8"/>
            <g transform="translate(106, 116) scale(1.2)" filter="url(#glow)">
                <path d="M125 15 L145 75 L210 110 L150 140 L165 215 L125 175 L85 215 L100 140 L40 110 L105 75 Z" fill="url(#gradFalcon)"/>
                <path d="M125 45 L135 90 L175 115 L135 130 L145 175 L125 150 L105 175 L115 130 L75 115 L115 90 Z" fill="#ffffff" opacity="0.3"/>
                <circle cx="125" cy="115" r="18" fill="#ffffff"/>
                <circle cx="125" cy="115" r="9" fill="#0284c7"/>
            </g>
        """
    },
    "cyber_falcon": {
        "viewBox": "0 0 512 512",
        "description": "Cybernetic falcon tech logo with geometric accents",
        "elements": """
            <defs>
                <linearGradient id="cyberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00f2fe"/>
                    <stop offset="100%" stop-color="#4facfe"/>
                </linearGradient>
            </defs>
            <rect width="512" height="512" rx="128" fill="#0b0f19"/>
            <path d="M256 60 L420 180 L360 400 L256 460 L152 400 L92 180 Z" fill="none" stroke="url(#cyberGrad)" stroke-width="6"/>
            <path d="M256 120 L370 200 L320 360 L256 400 L192 360 L142 200 Z" fill="rgba(79, 172, 254, 0.08)" stroke="rgba(0, 242, 254, 0.4)" stroke-width="3"/>
            <g transform="translate(256, 260) scale(4)">
                <path d="M0 -25 L12 -5 L30 -2 L16 10 L18 28 L0 18 L-18 28 L-16 10 L-30 -2 L-12 -5 Z" fill="url(#cyberGrad)"/>
            </g>
            <circle cx="256" cy="256" r="8" fill="#ffffff"/>
        """
    },
    "rocket": {
        "viewBox": "0 0 512 512",
        "description": "Aerodynamic aerospace rocket badge with twin booster flames",
        "elements": """
            <defs>
                <linearGradient id="rocketGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#f43f5e"/>
                    <stop offset="100%" stop-color="#fb923c"/>
                </linearGradient>
            </defs>
            <rect width="512" height="512" rx="128" fill="#0f172a"/>
            <circle cx="256" cy="256" r="200" fill="none" stroke="rgba(244, 63, 94, 0.3)" stroke-width="4"/>
            <path d="M256 80 C290 140 330 230 330 320 L280 320 L280 370 L256 350 L232 370 L232 320 L182 320 C182 230 222 140 256 80 Z" fill="#ffffff"/>
            <circle cx="256" cy="200" r="28" fill="#0f172a"/>
            <circle cx="256" cy="200" r="20" fill="#38bdf8"/>
            <path d="M236 370 L256 450 L276 370 Z" fill="url(#rocketGrad)"/>
            <path d="M182 280 L120 330 L182 340 Z" fill="#f43f5e"/>
            <path d="M330 280 L392 330 L330 340 Z" fill="#f43f5e"/>
        """
    },
    "shield": {
        "viewBox": "0 0 512 512",
        "description": "Modern cyber defense crest shield with quantum core",
        "elements": """
            <defs>
                <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#10b981"/>
                    <stop offset="100%" stop-color="#065f46"/>
                </linearGradient>
            </defs>
            <rect width="512" height="512" rx="128" fill="#041f1a"/>
            <path d="M256 60 C360 60 410 100 410 220 C410 350 256 440 256 440 C256 440 102 350 102 220 C102 100 152 60 256 60 Z" fill="url(#shieldGrad)" stroke="#34d399" stroke-width="8"/>
            <path d="M256 110 C330 110 366 140 366 230 C366 325 256 395 256 395 C256 395 146 325 146 230 C146 140 182 110 256 110 Z" fill="#064e3b" opacity="0.6"/>
            <path d="M220 250 L245 275 L305 215" fill="none" stroke="#a7f3d0" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        """
    },
    "brain": {
        "viewBox": "0 0 512 512",
        "description": "Neural AI intelligence node logo with synaptic pathways",
        "elements": """
            <defs>
                <linearGradient id="aiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#a855f7"/>
                    <stop offset="100%" stop-color="#6366f1"/>
                </linearGradient>
            </defs>
            <rect width="512" height="512" rx="128" fill="#0e0c1f"/>
            <circle cx="256" cy="256" r="190" fill="none" stroke="rgba(168, 85, 247, 0.25)" stroke-width="4"/>
            <circle cx="256" cy="256" r="60" fill="url(#aiGrad)"/>
            <circle cx="160" cy="180" r="24" fill="#c084fc"/>
            <circle cx="352" cy="180" r="24" fill="#818cf8"/>
            <circle cx="150" cy="320" r="24" fill="#c084fc"/>
            <circle cx="362" cy="320" r="24" fill="#818cf8"/>
            <line x1="256" y1="256" x2="160" y2="180" stroke="#a855f7" stroke-width="6"/>
            <line x1="256" y1="256" x2="352" y2="180" stroke="#6366f1" stroke-width="6"/>
            <line x1="256" y1="256" x2="150" y2="320" stroke="#a855f7" stroke-width="6"/>
            <line x1="256" y1="256" x2="362" y2="320" stroke="#6366f1" stroke-width="6"/>
            <line x1="160" y1="180" x2="150" y2="320" stroke="rgba(168, 85, 247, 0.4)" stroke-width="4" stroke-dasharray="6 6"/>
            <line x1="352" y1="180" x2="362" y2="320" stroke="rgba(99, 102, 241, 0.4)" stroke-width="4" stroke-dasharray="6 6"/>
        """
    },
    "drone": {
        "viewBox": "0 0 512 512",
        "description": "Quadcopter autonomous drone logo with optical gimbal",
        "elements": """
            <defs>
                <linearGradient id="droneGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#3b82f6"/>
                    <stop offset="100%" stop-color="#1d4ed8"/>
                </linearGradient>
            </defs>
            <rect width="512" height="512" rx="128" fill="#0f172a"/>
            <line x1="140" y1="140" x2="372" y2="372" stroke="#64748b" stroke-width="12" stroke-linecap="round"/>
            <line x1="372" y1="140" x2="140" y2="372" stroke="#64748b" stroke-width="12" stroke-linecap="round"/>
            <circle cx="140" cy="140" r="50" fill="none" stroke="#38bdf8" stroke-width="8"/>
            <circle cx="372" cy="140" r="50" fill="none" stroke="#38bdf8" stroke-width="8"/>
            <circle cx="140" cy="372" r="50" fill="none" stroke="#38bdf8" stroke-width="8"/>
            <circle cx="372" cy="372" r="50" fill="none" stroke="#38bdf8" stroke-width="8"/>
            <rect x="206" y="206" width="100" height="100" rx="30" fill="url(#droneGrad)"/>
            <circle cx="256" cy="256" r="24" fill="#0f172a"/>
            <circle cx="256" cy="256" r="14" fill="#38bdf8"/>
        """
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# ICONIFY OPEN SOURCE VECTOR ASSET MATCHER (Saltice Engine Logic)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_iconify_svg(entity_name: str) -> Optional[str]:
    """
    Queries open-source icon registries (Lucide, MDI, Tabler, FontAwesome)
    via public Iconify API with zero credentials required.
    """
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', (entity_name or "").lower().strip())
    if not clean_name:
        return None

    providers = ["lucide", "tabler", "mdi", "fa6-solid", "fluent"]
    for prov in providers:
        url = f"https://api.iconify.design/{prov}/{clean_name}.svg"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ImageAgent-SVG/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    raw_svg = resp.read().decode('utf-8')
                    if "<svg" in raw_svg and "</svg>" in raw_svg:
                        return raw_svg.strip()
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI SEMANTIC SVG LOGO GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_SVG = """
You are an elite vector graphic designer and SVG architect specializing in modern high-tech company logos, app icons, geometric emblems, and brand identity marks.

Given a user's logo prompt or brand name, produce a SINGLE, COMPLETE, BEAUTIFUL, PRODUCTION-READY SVG DOCUMENT.

STRICT DESIGN RULES:
1. Always output valid, well-formed XML: `<svg viewBox="0 0 512 512" width="512" height="512" xmlns="http://www.w3.org/2000/svg">...</svg>`
2. Visual Sophistication:
   - Deep background container: `<rect width="512" height="512" rx="128" fill="#0d1117"/>` (or dark aesthetic fitting the theme).
   - Rich Gradients: Define `<defs><linearGradient ...>` or `<radialGradient ...>` with vibrant modern color stops (cyan/blue, emerald/teal, violet/magenta, neon gold).
   - Drop Shadow / Glow filter: Include `<filter id="glow">` or subtle ambient accents.
   - Distinctive Focal Emblem: Intricate geometric paths (`<path d="...">`), interlocking polygons, circles, or monogram glyphs.
   - Center alignment and balanced composition.
3. OUTPUT FORMAT:
   - Output ONLY the raw `<svg ...> ... </svg>` code.
   - Do NOT wrap in markdown codeblocks (no ```xml or ```svg).
   - Do NOT add explanations, notes, or introductions.
"""

def generate_svg_with_gemini(prompt: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Calls Gemini API to generate semantic SVG logo markup.
    """
    key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key:
        return None

    models_to_try = [GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
    seen = set()
    unique_models = []
    for m in models_to_try:
        if m not in seen:
            seen.add(m)
            unique_models.append(m)

    for model in unique_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT_SVG}]
            },
            "contents": [
                {"parts": [{"text": f"Design a cutting-edge vector logo for: {prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                res_json = resp.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    # Clean code fence if model included it
                    cleaned = re.sub(r'^```(?:xml|svg)?\s*', '', raw_text, flags=re.IGNORECASE)
                    cleaned = re.sub(r'```$', '', cleaned).strip()
                    if "<svg" in cleaned and "</svg>" in cleaned:
                        start_idx = cleaned.find("<svg")
                        end_idx = cleaned.rfind("</svg>") + 6
                        return cleaned[start_idx:end_idx]
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# LOGO GENERATOR MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class SVGLogoGenerator:
    """
    Unified Vector Logo Generation Engine for ImageAgent.
    Integrates Gemini Vector Synthesis, Iconify Public API, and Curated Presets.
    """

    def __init__(self, output_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base_dir, "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_logo(
        self,
        prompt: str,
        style: str = "modern",
        rasterize_to_png: bool = True
    ) -> Dict[str, Any]:
        """
        Generates a vector logo from prompt.
        Saves .svg file and optionally rasterizes to .png for diffusion reference use.
        """
        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', prompt.lower().strip())[:30].strip('_')
        if not slug:
            slug = "logo"

        svg_content = None
        source = "unknown"

        # 1. Check if matches offline curated preset
        lower_prompt = prompt.lower()
        matched_preset = None
        for key in CURATED_LOGO_PRESETS:
            if key in lower_prompt:
                matched_preset = key
                break

        # 2. Try Gemini Vector Synthesis first for custom prompts
        if not matched_preset or "custom" in lower_prompt or "tech" in lower_prompt:
            gemini_svg = generate_svg_with_gemini(prompt)
            if gemini_svg:
                svg_content = gemini_svg
                source = "gemini_vector_synthesis"

        # 3. Fallback to Curated Preset
        if not svg_content and matched_preset:
            preset = CURATED_LOGO_PRESETS[matched_preset]
            svg_content = f'<svg viewBox="{preset["viewBox"]}" width="512" height="512" xmlns="http://www.w3.org/2000/svg">{preset["elements"]}</svg>'
            source = f"curated_preset_{matched_preset}"

        # 4. Fallback to Iconify API (Saltice vector logic)
        if not svg_content:
            first_word = re.findall(r'[a-zA-Z]+', lower_prompt)
            for word in first_word[:3]:
                icon_svg = fetch_iconify_svg(word)
                if icon_svg:
                    # Wrap Iconify path in a rich logo emblem container
                    m_path = re.search(r'd="([^"]+)"', icon_svg)
                    m_box = re.search(r'viewBox="([^"]+)"', icon_svg)
                    box = m_box.group(1) if m_box else "0 0 24 24"
                    path = m_path.group(1) if m_path else ""
                    svg_content = f"""<svg viewBox="0 0 512 512" width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="iconGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="128" fill="#0b0f19"/>
  <circle cx="256" cy="256" r="190" fill="none" stroke="rgba(56, 189, 248, 0.3)" stroke-width="4"/>
  <g transform="translate(106, 106) scale(12.5)">
    <svg viewBox="{box}" width="24" height="24">
      <path d="{path}" fill="url(#iconGrad)" stroke="#38bdf8" stroke-width="0.5"/>
    </svg>
  </g>
</svg>"""
                    source = f"iconify_{word}"
                    break

        # 5. Final Procedural Fallback (Cyber Falcon / Monogram)
        if not svg_content:
            preset = CURATED_LOGO_PRESETS["cyber_falcon"]
            svg_content = f'<svg viewBox="{preset["viewBox"]}" width="512" height="512" xmlns="http://www.w3.org/2000/svg">{preset["elements"]}</svg>'
            source = "procedural_cyber_emblem"

        # Save SVG file
        svg_filename = f"{timestamp}_{slug}_logo.svg"
        svg_path = os.path.join(self.output_dir, svg_filename)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        png_path = None
        if rasterize_to_png:
            png_path = self.rasterize_svg(svg_path)

        duration = round((datetime.now() - start_time).total_seconds(), 2)

        return {
            "success": True,
            "source": source,
            "prompt": prompt,
            "svg_path": svg_path,
            "png_reference_path": png_path,
            "duration_seconds": duration,
            "file_size_bytes": os.path.getsize(svg_path),
            "svg_code": svg_content
        }

    def rasterize_svg(self, svg_path: str) -> Optional[str]:
        """
        Rasterizes an SVG file to PNG for use as reference image in diffusion models.
        Uses svglib + reportlab, or falls back gracefully to a structured PNG placeholder.
        """
        png_path = svg_path.replace(".svg", ".png")
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            drawing = svg2rlg(svg_path)
            if drawing:
                renderPM.drawToFile(drawing, png_path, fmt="PNG")
                if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
                    return png_path
        except Exception:
            pass

        # Fallback: PIL high-contrast canvas representation
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (512, 512), color=(11, 15, 25, 255))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([(32, 32), (480, 480)], radius=64, outline=(56, 189, 248), width=4)
            draw.ellipse([(96, 96), (416, 416)], outline=(2, 132, 199), width=3)
            # Center geometric diamond
            draw.polygon([(256, 140), (370, 256), (256, 372), (142, 256)], fill=(56, 189, 248, 180), outline=(255, 255, 255))
            img.save(png_path, "PNG")
            return png_path
        except Exception:
            return None


if __name__ == "__main__":
    generator = SVGLogoGenerator()
    print("Testing SVG Logo Generator...")
    res = generator.generate_logo("Cybernetic Falcon AI logo", rasterize_to_png=True)
    print(f"Result: {res['source']}, SVG: {res['svg_path']}, PNG: {res['png_reference_path']}, Time: {res['duration_seconds']}s")
