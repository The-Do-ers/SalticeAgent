---
name: image-agent
description: Autonomous visual diffusion and vector graphic studio for SalticeAgent. Covers Cloudflare Workers AI edge diffusion (<2.5s), Hugging Face ZeroGPU / Pollinations multi-model parallel generation, 4-tier vector SVG brand marks, C.R.A.P. design scoring, and wordmark typography typesetting.
when-to-use:
  - generate image
  - create logo
  - design brand mark
  - visual assets
  - ui mockup
  - svg vector
  - image generation
user-invocable: true
argument-hint: "[prompt or logo concept]"
allowed-tools:
  - generate_image
  - generate_svg_logo
  - inspect_image_quality
  - run_command
  - read_file
  - write_file
---

# SalticeAgent Image & Vector Studio Skill

This skill guides the autonomous generation of visual assets, high-resolution diffusion images, and mathematical vector SVG logos.

## Architectural Capabilities

### 1. Dual-Engine Generation Matrix
- **Edge Diffusion (Cloudflare Workers AI)**:
  - Ultra-low latency (<2.5s) serverless GPU inference.
  - Models: `@cf/black-forest-labs/flux-1-schnell`, `@cf/stabilityai/stable-diffusion-xl-base-1.0`.
  - Zero-queue, deterministic execution.
- **ZeroGPU / Multi-Model (Hugging Face Spaces + Pollinations Fallback)**:
  - Parallel generation across FLUX.1-schnell, FLUX.1-dev, SD 3.5 Large, and Z-Image-Turbo.
  - Automatic fallback to Pollinations.ai if Hugging Face queues are saturated.

### 2. 4-Layer Resilient Vector SVG Engine
When generating logos or vector branding:
- **Layer 1 (Gemini 2.5/3.1 XML Synthesis)**: Direct mathematical XML code generation with viewBox `0 0 800 800`, `<defs>` linear/radial gradients, and glowing dropshadow filters.
- **Layer 2 (Iconify Registry)**: 200,000+ open-source icon primitives fetched via API.
- **Layer 3 (Curated Offline Presets)**: Beautiful geometric fallbacks (tech shields, neural nodes, modern abstract monograms).
- **Layer 4 (svglib + reportlab Rasterizer)**: Lossless compilation to high-res PNG (`output.png`).

### 3. Typography & Wordmark Typesetting
- Diffusion models notoriously hallucinate or garble textual characters.
- Use `add_wordmark` or pass `wordmark="Company Name"` to `generate_image` to overlay clean, auto-fitted PIL fonts with subtle dropshadows.

---

## Tool Execution Guide

### Generating a Diffusion Image
```python
generate_image(
    prompt="A futuristic holographic workstation with neon cybernetic accents",
    model="flux-schnell",       # or "sdxl", "flux-dev"
    backend="auto",             # selects cloudflare -> hf -> pollinations
    wordmark="SALTICE AI",      # optional typography overlay
    enhance=True,               # visual prompt engineer expansion
    output_path="artifacts/workspace.png"
)
```

### Generating a Vector Logo
```python
generate_svg_logo(
    concept="Cybernetic falcon with geometric wings and deep indigo glowing gradients",
    output_path="artifacts/logo.svg",
    style="modern-tech",        # or "minimalist", "cyberpunk", "abstract"
    rasterize_to_png=True       # also outputs artifacts/logo.png
)
```

### Visual Quality Inspection
```python
inspect_image_quality(image_path="artifacts/logo.png")
```
Inspects dimensions, color mode, entropy, file size, and verifies that the file is not corrupted or blank.
