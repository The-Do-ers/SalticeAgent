"""
Flexible Multi-Agent Workflow & Discussion Council for Saltice
Features:
- Builder Mode: Antigravity-style Lead Architect with Subagent Orchestration!
- Council Discussion Mode: Round-table debate where AIs critique each other before building!
- Committee Swarm Mode: Architect -> Coder -> Reviewer -> Autonomous Executor with Workspace Awareness!
- Bulletproof File Extraction: Captures code blocks, comments, and fallbacks so no code is ever lost.
"""

import sys
import os
import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from providers import call_llm
from caveman import CAVEMAN_PROMPTS
from engine import ReActAgent, SalticeArchitectAgent
from tools import write_file, run_command, get_workspace_summary
from artifacts import ARTIFACT_MANAGER

console = Console(force_terminal=True, legacy_windows=False)

class MultiAgentWorkflow:
    def __init__(self, caveman_level: str = "lite"):
        self.caveman_level = caveman_level
        self.system_caveman = CAVEMAN_PROMPTS.get(caveman_level, "")
        self.active_team = ["gemini", "mistral", "cloudflare", "openrouter", "groq", "nvidia_nim", "cohere", "local"]

    def set_active_team(self, team_list: list):
        """Set which AIs are active in the workflow."""
        valid_providers = ["gemini", "mistral", "cloudflare", "openrouter", "groq", "nvidia_nim", "cohere", "local"]
        if "all" in team_list:
            self.active_team = valid_providers
        else:
            self.active_team = [p for p in team_list if p in valid_providers]
            if not self.active_team:
                self.active_team = valid_providers
        console.print(f"[bold cyan]Active Team updated:[/bold cyan] {', '.join(self.active_team).upper()}")

    def set_caveman_level(self, level: str):
        if level in CAVEMAN_PROMPTS:
            self.caveman_level = level
            self.system_caveman = CAVEMAN_PROMPTS.get(level, "")
            console.print(f"[bold cyan]Caveman mode set to: {level.upper()}[/bold cyan]")
        else:
            console.print(f"[bold red]Unknown level: {level}. Options: lite, full, ultra, off[/bold red]")

    def run_builder(self, user_goal: str) -> str:
        """
        Flagship Antigravity-style Builder Mode:
        Lead Architect inspects workspace, creates implementation plan, spawns subagents,
        verifies code, and saves walkthrough.
        """
        builder = SalticeArchitectAgent(caveman_level=self.caveman_level)
        return builder.run(user_goal)

    def run_discussion(self, topic: str, auto_execute: bool = True):
        """
        Council Discussion Mode:
        AIs debate and critique each other to reach the optimal solution!
        """
        console.print(Panel(f"[bold white]{topic}[/bold white]", title="[bold magenta]🏛️ Council Discussion: Multi-Agent Debate[/bold magenta]", border_style="magenta"))
        workspace_info = get_workspace_summary()

        # --- ROUND 1: Gemini (Architect) presents the initial proposal ---
        console.print("[yellow]🧠 [Architect / Gemini] Formulating initial architectural proposal...[/yellow]")
        p1 = f"""{self.system_caveman}
Role: Chief Architect.
Workspace Context:
{workspace_info}

Task: Propose a clear technical architecture and approach for:
{topic}
Highlight core components, target files, and state management."""
        r1 = call_llm([{"role": "user", "content": p1}], preferred_provider="gemini", allowed_providers=self.active_team)
        speech1 = r1["content"].strip()
        console.print(Panel(Markdown(speech1), title=f"[yellow]Architect Proposal ({r1['provider']})[/yellow]", border_style="yellow"))

        # --- ROUND 2: Mistral Codestral critiques and proposes code structure ---
        console.print("[cyan]⚡ [Lead Coder / Mistral Codestral] Critiquing proposal & designing code modules...[/cyan]")
        p2 = f"""{self.system_caveman}
Role: Principal Software Engineer.
Review the Architect's proposal below. Point out practical implementation details or missing edge cases. Propose the exact file structure and functions.
Architect Proposal:
{speech1}

Original Request:
{topic}"""
        r2 = call_llm([{"role": "user", "content": p2}], preferred_provider="mistral", allowed_providers=self.active_team)
        speech2 = r2["content"].strip()
        console.print(Panel(Markdown(speech2), title=f"[cyan]Coder Critique & Architecture ({r2['provider']})[/cyan]", border_style="cyan"))

        # --- ROUND 3: Cohere / NVIDIA NIM challenges edge cases & failure modes ---
        console.print("[blue]🔍 [Security & Reliability / Cohere/NIM] Stress-testing and checking edge cases...[/blue]")
        p3 = f"""{self.system_caveman}
Role: Reliability & Edge-Case Specialist.
Critique the Coder and Architect discussion. What happens when inputs are invalid? What are edge cases, rate limits, or potential failure points?
Coder's design:
{speech2}"""
        r3 = call_llm([{"role": "user", "content": p3}], preferred_provider="cohere", allowed_providers=self.active_team)
        speech3 = r3["content"].strip()
        console.print(Panel(Markdown(speech3), title=f"[blue]Reliability Review ({r3['provider']})[/blue]", border_style="blue"))

        # --- ROUND 4: Cloudflare / Groq synthesizes consensus and outputs code ---
        console.print("[green]🚀 [Consensus & Implementation / Cloudflare/Groq] Synthesizing consensus into complete code...[/green]")
        p4 = f"""{self.system_caveman}
Role: Implementation Master.
The council has reached consensus. Based on the Architect's plan, Coder's structure, and Reliability specialist's edge cases, generate the COMPLETE, final, runnable code.
Use `# filepath: <path>` or `<!-- filepath: <path> -->` at the top of each code block.
Summary of debate:
{speech1}
{speech2}
{speech3}"""
        r4 = call_llm([{"role": "user", "content": p4}], preferred_provider="cloudflare", allowed_providers=self.active_team, max_tokens=1500)
        final_code = r4["content"].strip()
        console.print(Panel(Markdown(final_code), title=f"[green]Final Consensus Code ({r4['provider']})[/green]", border_style="green"))

        # Save Council Artifact
        safe_slug = re.sub(r'[^a-zA-Z0-9_]', '_', topic[:25].strip()).lower()
        council_art = f"""## Multi-Agent Debate Record

### Round 1: Architect (Gemini)
{speech1}

### Round 2: Lead Coder Critique (Mistral Codestral)
{speech2}

### Round 3: Reliability & Edge Cases (Cohere/NIM)
{speech3}

### Round 4: Consensus Code ({r4['provider'].upper()})
{final_code}
"""
        ARTIFACT_MANAGER.save_artifact(f"council_{safe_slug}.md", f"Council Debate: {topic[:40]}", "council_debate", council_art)

        # --- ROUND 5: Autonomous Executor tests and validates ---
        if auto_execute:
            console.print("[magenta]🛠️ [Autonomous Executor] Applying consensus files and running tests...[/magenta]")
            saved = self._extract_and_save_files(final_code)
            test_goal = f"Verify the solution for '{topic}'. Created files: {saved}. Run self-tests or syntax checks. If errors occur, diagnose, patch, and re-run until all tests pass."
            executor = ReActAgent(mode="groq", caveman_level=self.caveman_level, max_iterations=6)
            executor.run(test_goal)

        console.print("[bold green]✔ Council Discussion and Implementation Complete.[/bold green]\n")

    def run_builder(self, user_prompt: str):
        """
        Flagship Builder Mode:
        Autonomous Lead Architect with live workspace awareness, dual-mode parser, and subagents on demand.
        """
        from engine import SalticeAntigravityEngine
        engine = SalticeAntigravityEngine(mode="openrouter", caveman_level=self.caveman_level, max_iterations=8)
        return engine.run(user_prompt)

    def run_task(self, user_prompt: str, auto_execute: bool = True):
        """
        The Standard Swarm Committee:
        Architect (Gemini) -> Coder (Mistral/Groq) -> Reviewer (NIM/Cohere) -> Autonomous Executor.
        Equipped with Workspace Awareness!
        """
        console.print(Panel(f"[bold white]{user_prompt}[/bold white]", title="[bold blue]Swarm Task: Multi-Agent Committee[/bold blue]", border_style="blue"))
        workspace_info = get_workspace_summary()

        # 1. ARCHITECT
        console.print("[yellow]🧠 [Architect] Inspecting workspace & designing blueprint...[/yellow]")
        arch_prompt = f"""{self.system_caveman}
Role: Senior Software Architect.
Workspace Context:
{workspace_info}

Decompose this user request into concise steps, target files to create or update, and verification criteria.
Request: {user_prompt}"""
        arch_res = call_llm([{"role": "user", "content": arch_prompt}], preferred_provider="gemini", allowed_providers=self.active_team, max_tokens=600)
        plan = arch_res["content"].strip()
        console.print(Panel(Markdown(plan), title=f"[yellow]Plan ({arch_res['provider']})[/yellow]", border_style="yellow"))

        # 2. CODER
        console.print("[green]⚡ [Coder] Writing complete code implementation...[/green]")
        coder_prompt = f"""{self.system_caveman}
Role: Expert Software Engineer.
Write complete, executable code based on this plan.
For web apps/games (like Flappy Bird), create self-contained code in index.html (with CSS & JS embedded or standard <script src="game.js"> WITHOUT type="module") so it runs immediately when double-clicked!
Use `# filepath: <filename>` or `<!-- filepath: <filename> -->` inside each code block.
Workspace Context:
{workspace_info}

Plan: {plan}
Request: {user_prompt}"""
        coder_res = call_llm([{"role": "user", "content": coder_prompt}], preferred_provider="mistral", allowed_providers=self.active_team, max_tokens=1500)
        code = coder_res["content"].strip()
        console.print(Panel(Markdown(code), title=f"[green]Code ({coder_res['provider']})[/green]", border_style="green"))

        # 3. REVIEWER
        console.print("[cyan]🔍 [Reviewer] Auditing code quality & security...[/cyan]")
        rev_prompt = f"""{self.system_caveman}
Role: Security Auditor & Code Reviewer.
Inspect code for bugs and edge cases. Be telegraphic: 'L<line>: <issue>. <fix>' or 'APPROVED'.
Code: {code}"""
        rev_res = call_llm([{"role": "user", "content": rev_prompt}], preferred_provider="nvidia_nim", allowed_providers=self.active_team, max_tokens=500)
        review = rev_res["content"].strip()
        console.print(Panel(Markdown(review), title=f"[cyan]Audit ({rev_res['provider']})[/cyan]", border_style="cyan"))

        # Save Swarm Committee Artifact
        safe_slug = re.sub(r'[^a-zA-Z0-9_]', '_', user_prompt[:25].strip()).lower()
        swarm_art = f"""## Swarm Committee Implementation Plan & Audit

### 1. Architectural Plan ({arch_res['provider'].upper()})
{plan}

### 2. Code Implementation ({coder_res['provider'].upper()})
{code}

### 3. Security Audit & Review ({rev_res['provider'].upper()})
{review}
"""
        ARTIFACT_MANAGER.save_artifact(f"swarm_{safe_slug}.md", f"Swarm Plan: {user_prompt[:40]}", "swarm_plan", swarm_art)

        # 4. AUTONOMOUS EXECUTOR & SAVER
        if auto_execute:
            console.print("[magenta]🚀 [Autonomous Executor] Applying files to disk...[/magenta]")
            saved = self._extract_and_save_files(code)

            # Web application verification
            if any(f.endswith(('.html', '.js')) for f in saved):
                console.print(Panel(f"[bold green]✔ Web project saved![/bold green]\nSaved files: {', '.join(saved)}", title="[bold green]Generated Files[/bold green]", border_style="green"))
            elif any(f.endswith('.py') for f in saved):
                py_files = [f for f in saved if f.endswith('.py')]
                for pf in py_files:
                    test_out = run_command(f"python -m py_compile {pf}")
                    if "[SUCCESS" in test_out:
                        console.print(f"  [bold green]✔ Syntax verified clean:[/bold green] {pf}")
                    else:
                        console.print(f"  [bold red]⚠️ Syntax error in {pf}:[/bold red] patching...")
                        executor = ReActAgent(mode="groq", caveman_level=self.caveman_level, max_iterations=4)
                        executor.run(f"Fix the syntax error in {pf}: {test_out}")

        console.print("[bold green]✔ Swarm Pipeline Finished.[/bold green]\n")

    def _extract_and_save_files(self, text: str) -> list:
        """
        Robust, multi-strategy file extractor:
        1. Checks comments `# filepath: ...`, `// filepath: ...`, `<!-- filepath: ... -->` inside the block.
        2. Checks headings / filename labels right above the block (`### index.html`).
        3. Fallback: inspects content for `<!DOCTYPE html>`, `import pygame`, etc.
        """
        saved = []
        valid_exts = ('.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.sh', '.bat', '.txt', '.yaml', '.yml')

        block_pattern = r"```([a-zA-Z0-9_\-\.]*)?\s*[\r\n]+([\s\S]*?)```"
        blocks = list(re.finditer(block_pattern, text))

        for match in blocks:
            lang_tag = (match.group(1) or "").strip().lower()
            code_content = match.group(2).strip()

            start_pos = match.start()
            prefix_text = text[max(0, start_pos - 120):start_pos]

            filepath = None

            first_lines = "\n".join(code_content.splitlines()[:5])
            # A. Check for filepath comment
            fp_match = re.search(r"(?:#|//|<!--|/\*)\s*(?:filepath|file):\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", first_lines, re.IGNORECASE)
            if fp_match:
                filepath = fp_match.group(1).strip()

            # B. Check for simple filename comment
            if not filepath:
                simple_match = re.search(r"(?:#|//|<!--)\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", first_lines)
                if simple_match:
                    cand = simple_match.group(1).strip()
                    if cand.endswith(valid_exts):
                        filepath = cand

            # C. Check prefix heading right before code block
            if not filepath and prefix_text:
                pre_match = re.search(r"(?:###|####|\*\*|`|File:?|Save to:?)\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", prefix_text, re.IGNORECASE)
                if pre_match:
                    cand = pre_match.group(1).strip("`* :")
                    if cand.endswith(valid_exts):
                        filepath = cand

            # D. If lang tag has filename (e.g. ```html:index.html)
            if not filepath and ":" in lang_tag:
                cand = lang_tag.split(":", 1)[1]
                if cand.endswith(valid_exts):
                    filepath = cand

            # E. Intelligent content fallback
            if not filepath:
                if "<!doctype html" in code_content.lower() or "<html" in code_content.lower():
                    filepath = "index.html"
                elif lang_tag in ["css"] or ("body {" in code_content and "}" in code_content and not "<html" in code_content):
                    filepath = "style.css"
                elif lang_tag in ["python", "py"] or "import " in code_content or "def " in code_content:
                    filepath = "game.py" if "game" in text.lower() else "main.py"
                elif lang_tag in ["javascript", "js"]:
                    filepath = "game.js" if "game" in text.lower() else "app.js"

            if filepath:
                filepath = filepath.strip("`* \t\r\n")
                if any(filepath.endswith(ext) for ext in valid_exts):
                    write_file(filepath, code_content)
                    saved.append(filepath)
                    console.print(f"  [bold green]✔ Saved file:[/bold green] {filepath}")

        return saved
