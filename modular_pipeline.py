"""
Modular Subsystem Decomposition & Assembly Pipeline for Saltice (Full-Stack Edition)
Architecture:
1. Domain-Aware Architect Phase (Gemini 1.5 Flash):
   - Categorizes user goal into Game, WebApp, Dashboard, or Tool.
   - For Games: Allocates Groq to Web Audio & FX.
   - For WebApps/Tools: Allocates Groq to High-Speed Interactivity, Validation & Event Handlers (ZERO unwanted audio!).
2. Heterogeneous Subsystem Specialists with 4-Tier Fallback Chains:
   - Primary specialists with automated fallback across Gemini, Mistral, Hugging Face, Groq, Cloudflare.
3. Assembler / Integrator:
   - Fuses subsystem code directly into disk using slot replacement.
4. Autonomous Headless Runtime Tester Agent:
   - Simulates DOM, Web Audio, and 2D Canvas in Node.js.
   - Verifies loop execution, event listeners, and non-blank rendering.
5. Multi-Tier Self-Healing Loop:
   - Turn 1: Gemini 1.5 Flash (1M context)
   - Turn 2: Cloudflare DeepSeek-R1 Distill (Deep Algorithmic Reasoning)
   - Turn 3: Mistral Codestral
6. Cloudflare Pages 1-Click Live Deployment:
   - Deploys clean deliverable to a public, shareable *.pages.dev URL.
7. Telemetry & Performance Tracking:
   - Logs task metrics to local SQLite and Cloudflare D1.
"""

import sys
import os
import re
import json
import time
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console(force_terminal=True, legacy_windows=False)

from providers import call_llm
from tools import (
    write_file,
    read_file,
    replace_file_content,
    validate_code_syntax,
    verify_runtime_execution,
    create_plan,
    create_walkthrough,
    create_readme,
    infer_target_filename
)
from cloudflare_platform import deploy_to_pages, call_cloudflare_reasoning
from agents_auxiliary import TELEMETRY

SLOT_FALLBACK_CHAINS = {
    "SLOT_STYLES": ["gemini", "groq", "cloudflare", "huggingface"],
    "SLOT_CONTROLS": ["mistral", "huggingface", "groq", "cloudflare"],
    "SLOT_COMPONENTS": ["mistral", "huggingface", "groq", "cloudflare"],
    "SLOT_ENTITIES": ["huggingface", "mistral", "cloudflare", "groq"],
    "SLOT_DATA_STORE": ["huggingface", "mistral", "cloudflare", "groq"],
    "SLOT_AUDIO_OR_VFX": ["groq", "cloudflare", "mistral", "gemini"],
    "SLOT_AUDIO": ["groq", "cloudflare", "mistral", "gemini"],
    "SLOT_INTERACTIVITY": ["groq", "cloudflare", "mistral", "gemini"],
}


from engine import SalticeAntigravityEngine

class ModularDecompositionPipeline:
    """
    Modernized Pipeline that leverages the Antigravity Engine for multi-file, full-stack development.
    No more forced HTML single-file constraints.
    """
    def __init__(self, architect_provider: str = "gemini"):
        self.architect_provider = architect_provider
        self.engine = SalticeAntigravityEngine(mode=architect_provider)

    def run(self, user_goal: str, auto_deploy: bool = False, session_context: list = None, target_override: str = None) -> tuple[bool, str]:
        console.print(Panel(f"[bold white]{user_goal}[/bold white]", title="[bold bright_cyan]⚡ Autonomous Software Engineer (ReAct) ⚡[/bold bright_cyan]", border_style="cyan"))
        console.print("  [dim]• Modular mode is now powered by the Antigravity tool-using engine.[/dim]")
        console.print("  [dim]• Automatic Cloudflare deployment is disabled by default per user request.[/dim]")
        
        # We simply pass the goal into the Antigravity engine which can handle planning, multi-file TSX, etc.
        try:
            result = self.engine.run(user_goal, session_context=session_context, target_override=target_override)
            return True, result
        except Exception as e:
            return False, f"Pipeline execution failed: {e}"