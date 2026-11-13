"""
Saltice Visual & Vector Studio (ImageAgent).
Autonomous image synthesis, precision vector SVG logo generation,
and Cloudflare Workers AI edge diffusion engine.
"""

import os
import sys

# Ensure package directory is on path
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

from .intelligence import (
    enhance_prompt,
    add_wordmark,
    validate_image_integrity,
    extract_brand_palette,
    evaluate_crap_design
)
from .engines import (
    CloudflareAIClient,
    HFSpacesClient,
    ParallelImageGenerator
)
from .svg_generator import (
    SVGLogoGenerator,
    fetch_iconify_svg,
    CURATED_LOGO_PRESETS
)
from .agent import ImageAgent

__all__ = [
    "ImageAgent",
    "CloudflareAIClient",
    "HFSpacesClient",
    "ParallelImageGenerator",
    "SVGLogoGenerator",
    "fetch_iconify_svg",
    "CURATED_LOGO_PRESETS",
    "enhance_prompt",
    "add_wordmark",
    "validate_image_integrity",
    "extract_brand_palette",
    "evaluate_crap_design"
]
