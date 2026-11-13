"""
Saltice Autonomous Terminal Coding Assistant
Features:
- Flagship Builder Mode: Antigravity-style Lead Architect + Subagent Swarm
- Committee Swarm Mode: Architect -> Coder -> Reviewer -> Executor with Workspace Awareness
- Council Debate Mode: Round-table multi-agent critique and consensus synthesis
- Normal / Solo Mode: Local Qwencoder 7B or any single cloud engine with autonomous ReAct self-healing
- Proactive Web Search & Live Page Fetching
- RateLimitShield: Automatic failover across 9 AI providers
"""

import sys
import os
import re
import os
import sys

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
if CLI_DIR not in sys.path:
    sys.path.insert(0, CLI_DIR)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

from workflow import MultiAgentWorkflow
from engine import SalticeAntigravityEngine, ReActAgent, SalticeArchitectAgent
from providers import GLOBAL_STATS, LOCAL_URL, LOCAL_MODEL
from benchmark import run_benchmark
from tools import run_command, search_web, fetch_webpage, get_workspace_summary
from skills import SKILL_MANAGER
from artifacts import ARTIFACT_MANAGER
from token_monitor import display_token_and_limit_dashboard
from cloudflare_platform import deploy_to_pages, scan_url, semantic_code_search
from agents_auxiliary import TELEMETRY
from session_manager import SESSION_MANAGER

def show_banner():
    banner_content = (
        "[bold cyan]• Primary Engine:[/bold cyan] [white]Antigravity Autonomous Loop (Powered by OpenRouter & Cloud Pool)[/white]\n"
        "[bold cyan]• Toolbelt:[/bold cyan]       [white]Direct File Writing, Slice Viewer, Shell Commands, Live Web Search[/white]\n"
        "[bold cyan]• Developer APIs:[/bold cyan] [white]GitHub Code Search (PAT Connected) & Snyk Vulnerability Shield[/white]\n"
        "[bold cyan]• Workers:[/bold cyan]        [white]Parallel Subagents on Demand (Spawned only when necessary)[/white]\n"
        "[bold cyan]• Modes:[/bold cyan]          [white]openrouter (default), mistral, cloudflare, groq, gemini, local, swarm[/white]"
    )
    panel = Panel(
        banner_content,
        title="[bold bright_cyan]⚡ SALTICE • AUTONOMOUS CODING TERMINAL ⚡[/bold bright_cyan]",
        subtitle="[dim]Type [bold white]/help[/bold white] for commands | Active Mode: [bold green]openrouter[/bold green] (Antigravity Flow)[/dim]",
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(panel)


def print_help():
    table = Table(title="Saltice Terminal Commands", border_style="bright_blue", box=box.ROUNDED)
    table.add_column("Command", style="bold bright_cyan")
    table.add_column("Description", style="white")
    table.add_row("/ui | /web", "Launch modern Glassy Web UI in browser with persistent chat history")
    table.add_row("/mode [builder|swarm|council|local|...]", "Select operating mode: builder (Antigravity flow), swarm, council, local")
    table.add_row("/team [providers...]", "Customize active models in multi-agent team (e.g. /team gemini mistral groq)")
    table.add_row("/skills", "List installed specialized coding & workflow skills")
    table.add_row("/artifacts [name]", "List or view generated project artifacts (plans, blueprints, audits)")
    table.add_row("/search <query>", "Explicit web search (Note: AI also searches automatically in chat!)")
    table.add_row("/fetch <url>", "Fetch and extract text content from any webpage")
    table.add_row("/caveman [level]", "Change token compression: [lite | full | ultra | off]")
    table.add_row("/iterations [N]", "Set or view action iteration limit per task (0 for unlimited, default: unlimited)")
    table.add_row("/tokens", "Display live token limits (TPM), request quotas (RPM/RPD), and remaining balance")
    table.add_row("/models", "Check live connection and latency to all models")
    table.add_row("/deploy <file>", "Deploy any generated app to Cloudflare Pages (returns live *.pages.dev URL)")
    table.add_row("/browser <url>", "Inspect live web page or local HTML with headless Chrome DevTools (DOM, console, a11y)")
    table.add_row("/mcp <query>", "Search 4,200+ curated MCP servers by keyword or category")
    table.add_row("/scan <url>", "Run Cloudflare URL Scanner on any live URL for security & DOM audit")
    table.add_row("/semantic <query>", "Semantic code search across workspace using Cloudflare BGE embeddings")
    table.add_row("/telemetry", "Display persistent swarm win-rates, latencies, and speed metrics")
    table.add_row("/stats", "Display cumulative token usage and speed statistics")
    table.add_row("/benchmark", "Run the 5-iteration live benchmark test suite")
    table.add_row("/history | /chat", "Display conversational multi-turn session history and touched files")
    table.add_row("/sessions", "List all persistent saved sessions from disk")
    table.add_row("/resume <id>", "Resume and reload a past session transcript")
    table.add_row("/new", "Start a fresh session with clean conversation history")
    table.add_row("/state", "Inspect structured session state memory across all 4 tiers (app, user, session, temp)")
    table.add_row("/set <k> <v>", "Set structured state variable (e.g. /set user:theme aero-frost or /set target_object rocket)")
    table.add_row("/get <key>", "Retrieve exact value of a state variable across namespaces")
    table.add_row("/clear-state [scope]", "Clear memory state ('temp', 'session', 'user', 'app', or 'all')")
    table.add_row("/docs", "Display living project documentation (README.md, implementation_plan.md, walkthrough.md)")
    table.add_row("/stop | /cancel", "Stop active task generation cleanly and return to prompt")
    table.add_row("/pwd", "Print current working directory where files are created")
    table.add_row("/cd <path>", "Change the active working directory for file operations")
    table.add_row("/run <cmd>", "Execute an arbitrary shell command directly")
    table.add_row("/clear", "Clear terminal screen")
    table.add_row("/help", "Show this help table")
    table.add_row("exit | quit", "Exit Saltice")
    console.print(table)


def show_models_status():
    import requests
    from providers import (
        GROQ_KEY, NVIDIA_KEY, GEMINI_KEY, MISTRAL_KEY, SAMBANOVA_KEY,
        CF_ACCOUNT_ID, CF_API_TOKEN, COHERE_KEY, OPENROUTER_KEY,
        CEREBRAS_KEY, HUGGINGFACE_TOKEN, LOCAL_MODEL
    )

    table = Table(title="Live Model & Provider Status", border_style="green")
    table.add_column("Provider", style="bold yellow")
    table.add_column("Model Assigned", style="white")
    table.add_column("Status", style="green")
    table.add_column("Latency", style="cyan")

    # 1. Groq check
    try:
        t0 = time.time()
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=5
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Groq", "qwen/qwen3.8-27b (Coder)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Groq", "qwen/qwen3.8-27b", "[red]OFFLINE[/red]", "-")

    # 2. Mistral check
    try:
        t0 = time.time()
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
            json={"model": "codestral-latest", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=5
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Mistral AI", "codestral-latest (Coder)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Mistral AI", "codestral-latest", "[red]OFFLINE[/red]", "-")

    # 3. Cloudflare Workers AI check
    if CF_ACCOUNT_ID and CF_API_TOKEN:
        try:
            t0 = time.time()
            r = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"},
                json={"model": "@cf/qwen/qwen2.5-coder-32b-instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                timeout=8
            )
            dt = time.time() - t0
            st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
            table.add_row("Cloudflare AI", "@cf/qwen/qwen2.5-coder-32b-instruct", st, f"{dt:.2f}s")
        except Exception:
            table.add_row("Cloudflare AI", "@cf/qwen/qwen2.5-coder-32b-instruct", "[red]OFFLINE[/red]", "-")
    else:
        table.add_row("Cloudflare AI", "Workers AI (10k Neurons/day free)", "[dim]NOT CONFIGURED[/dim]", "-")

    # 4. NVIDIA NIM check
    try:
        t0 = time.time()
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
            json={"model": "meta/llama-3.2-11b-vision-instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=8
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("NVIDIA NIM", "meta/llama-3.2-11b-vision-instruct (Reviewer)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("NVIDIA NIM", "meta/llama-3.2-11b-vision-instruct", "[red]OFFLINE[/red]", "-")

    # 5. Gemini check
    try:
        t0 = time.time()
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "hi"}]}], "generationConfig": {"maxOutputTokens": 5}},
            timeout=8
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Google Gemini", "gemini-3.6-flash (Architect)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Google Gemini", "gemini-3.6-flash", "[red]OFFLINE[/red]", "-")

    # 6. Cohere check
    try:
        t0 = time.time()
        r = requests.post(
            "https://api.cohere.com/v2/chat",
            headers={"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"},
            json={"model": "command-r-08-2024", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=8
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Cohere", "command-r-08-2024", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Cohere", "command-r-08-2024", "[red]OFFLINE[/red]", "-")

    # 7. OpenRouter check
    try:
        t0 = time.time()
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={"model": "cohere/north-mini-code:free", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=8
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("OpenRouter", "cohere/north-mini-code:free (Router)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("OpenRouter", "cohere/north-mini-code:free", "[red]OFFLINE[/red]", "-")

    # 8. Hugging Face Router
    try:
        t0 = time.time()
        r = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}", "Content-Type": "application/json"},
            json={"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=8
        )
        dt = time.time() - t0
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Hugging Face", "deepseek-ai/DeepSeek-V4.1-Flash", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Hugging Face", "deepseek-ai/DeepSeek-V4.1-Flash", "[red]OFFLINE[/red]", "-")

    # 9. Cerebras AI
    try:
        t0 = time.time()
        r = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"},
            json={"model": "qwen-3.8-27b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
            timeout=5
        )
        dt = time.time() - t0
        if r.status_code == 200:
            st = "[green]ONLINE[/green]"
        elif r.status_code == 402:
            st = "[yellow]ACTIVATION REQ[/yellow]"
        else:
            st = f"[red]HTTP {r.status_code}[/red]"
        table.add_row("Cerebras AI", "qwen-3.8-27b (Wafer-Scale)", st, f"{dt:.2f}s")
    except Exception:
        table.add_row("Cerebras AI", "qwen-3.8-27b", "[red]OFFLINE[/red]", "-")

    # 10. Local check
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        st = "[green]ONLINE[/green]" if r.status_code == 200 else f"[yellow]HTTP {r.status_code}[/yellow]"
        table.add_row("Local Server", f"{LOCAL_MODEL} (Local Engine)", st, "<0.01s")
    except Exception:
        table.add_row("Local Server", f"{LOCAL_MODEL}", "[dim]STANDBY (port 11434)[/dim]", "-")

    console.print(table)


def show_stats():
    st = GLOBAL_STATS.summary()
    panel_content = f"""
**Total API Calls:** {st['calls']}
**Total Tokens Consumed:** {st['total_tokens']:,}
  • Prompt Tokens: {st['prompt_tokens']:,}
  • Completion Tokens: {st['completion_tokens']:,}
**Cumulative Inference Time:** {st['total_time_seconds']}s
**Average Generation Speed:** {st['avg_tokens_per_second']} tokens/sec
"""
    console.print(Panel(Markdown(panel_content), title="[bold cyan]Session Token & Performance Stats[/bold cyan]", border_style="cyan"))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Saltice Autonomous Coding Agent", add_help=False)
    parser.add_argument("--mode", "-m", type=str, default="builder", help="Engine/Provider mode")
    parser.add_argument("--caveman", "-c", type=str, default="lite", help="Caveman compression level (lite, full, ultra, off)")
    parser.add_argument("--iterations", "-i", "--max-turns", type=int, default=0, help="Maximum action iterations before pausing (default: 0 for unlimited)")
    parser.add_argument("--tokens", "--limits", "--quota", "-t", action="store_true", help="Display token and limit dashboard")
    parser.add_argument("--models", action="store_true", help="Show models status")
    parser.add_argument("--goal", "-g", type=str, default=None, help="Autonomous goal to execute")
    parser.add_argument("pos_args", nargs="*", help="Positional arguments or goal")

    # Fast-path for Web UI
    if any(arg.lower() in ["ui", "--ui", "web", "--web", "gui", "--gui"] for arg in sys.argv[1:]):
        from ui_server import start_ui_server
        start_ui_server()
        return

    # Fast-path for quick dashboard or status flags
    if any(arg in sys.argv for arg in ["tokens", "limits", "quota", "balance", "--tokens", "--limits", "--quota", "-t", "-l"]):
        display_token_and_limit_dashboard()
        return

    parsed, unknown = parser.parse_known_args()

    if parsed.tokens:
        display_token_and_limit_dashboard()
        return

    if parsed.models:
        show_models_status()
        return

    show_banner()

    current_mode = parsed.mode.lower()
    if current_mode in ["modular", "subsystems", "split"]:
        current_mode = "builder"
    current_caveman = parsed.caveman.lower()
    current_iterations = getattr(parsed, "iterations", 0)

    swarm_workflow = MultiAgentWorkflow(caveman_level=current_caveman)
    session_history = []
    active_project = {"target_file": None, "domain": None}

    initial_goal = parsed.goal
    if not initial_goal and parsed.pos_args:
        initial_goal = " ".join(parsed.pos_args).strip()

    # One-shot command-line execution
    if initial_goal:
        console.print(f"[bold bright_cyan]saltice[/bold bright_cyan] [dim]({current_mode})[/dim] [bold green]>[/bold green] {initial_goal}\n")
        try:
            if current_mode == "council":
                swarm_workflow.run_discussion(initial_goal, auto_execute=True)
            elif current_mode == "swarm":
                swarm_workflow.run_task(initial_goal, auto_execute=True)
            else:
                engine = SalticeAntigravityEngine(mode=current_mode, caveman_level=current_caveman, max_iterations=current_iterations)
                engine.run(initial_goal, session_context=session_history)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠️ Task cancelled by user (Ctrl+C).[/bold yellow]")
        return

    while True:
        try:
            mode_display = f"{current_mode}"
            user_input = console.input(f"[bold bright_cyan]saltice[/bold bright_cyan] [dim]({mode_display})[/dim] [bold green]>[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]Saltice session terminated. Happy coding![/bold cyan]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold cyan]Saltice session terminated. Happy coding![/bold cyan]")
            break

        if user_input in ["/stop", "/cancel"]:
            console.print("[bold yellow]No active background task currently running.[/bold yellow]")
            continue

        if user_input in ["/docs", "/doc", "/project"]:
            found = False
            for doc_file, doc_title in [("README.md", "Project README"), ("implementation_plan.md", "Implementation Plan"), ("walkthrough.md", "Project Walkthrough")]:
                if os.path.exists(doc_file):
                    found = True
                    try:
                        with open(doc_file, "r", encoding="utf-8", errors="replace") as df:
                            console.print(Panel(Markdown(df.read()), title=f"[bold bright_cyan]📖 {doc_title} ({doc_file})[/bold bright_cyan]", border_style="cyan"))
                    except Exception as de:
                        console.print(f"[red]Error reading {doc_file}: {de}[/red]")
            if not found:
                console.print("[yellow]No project documentation (README.md, implementation_plan.md, walkthrough.md) found in the current workspace.[/yellow]")
            continue

        # --- Slash Commands ---
        if user_input.startswith("/team"):
            parts = user_input.split()
            if len(parts) > 1:
                team = [p.lower() for p in parts[1:]]
                swarm_workflow.set_active_team(team)
            else:
                console.print(f"Current active team: [bold cyan]{', '.join(swarm_workflow.active_team).upper()}[/bold cyan]")
            continue

        if user_input.startswith("/mode"):
            parts = user_input.split()
            if len(parts) > 1:
                new_mode = parts[1].lower()
                if new_mode in ["builder", "auto", "saltice", "architect", "ecc", "antigravity"]:
                    current_mode = "builder"
                    console.print("[bold bright_cyan]Switched to Flagship Builder Mode (ECC + Antigravity Flow with 887 Skills & Async Subagents)[/bold bright_cyan]")
                elif new_mode in ["huggingface", "hf"]:
                    current_mode = "huggingface"
                    console.print("[bold cyan]Switched to Hugging Face Serverless Engine (Qwen 2.5 Coder & Llama 3.3 70B)[/bold cyan]")
                elif new_mode in ["cerebras"]:
                    current_mode = "cerebras"
                    console.print("[bold cyan]Switched to Cerebras Wafer-Scale Engine (1,000+ tok/s)[/bold cyan]")
                elif new_mode in ["local", "normal"]:
                    current_mode = "local"
                    console.print("[bold green]Switched to Normal Mode (Local Engine with Autonomous ReAct Loop)[/bold green]")
                elif new_mode in ["swarm", "committee"]:
                    current_mode = "swarm"
                    console.print("[bold yellow]Switched to Swarm Mode (Architect + Coder + Reviewer + Executor)[/bold yellow]")
                elif new_mode in ["council", "debate", "discussion"]:
                    current_mode = "council"
                    console.print("[bold magenta]Switched to Council Mode (Round-Table Debate & Synthesis)[/bold magenta]")
                elif new_mode in ["modular", "subsystems", "split"]:
                    current_mode = "builder"
                    console.print("[bold bright_cyan]Modular decomposition is now natively unified into Flagship Builder Mode (ECC Architecture + Subagents)[/bold bright_cyan]")
                elif new_mode in ["gemini", "mistral", "groq", "cloudflare", "openrouter"]:
                    current_mode = "mistral"
                    console.print("[bold cyan]Switched to Solo Mode using Mistral Codestral[/bold cyan]")
                elif new_mode in ["groq", "gemini", "nim", "cloudflare", "cohere", "openrouter", "sambanova"]:
                    current_mode = new_mode
                    console.print(f"[bold cyan]Switched to Solo Mode using {new_mode.upper()} engine[/bold cyan]")
                else:
                    console.print("[bold red]Unknown mode. Options: builder, huggingface, cerebras, swarm, council, local, mistral, groq, gemini, cloudflare, openrouter, nim, cohere[/bold red]")
            else:
                console.print(f"Current mode: [bold yellow]{current_mode}[/bold yellow]")
            continue

        if user_input in ["/ui", "/web", "/gui"]:
            console.print("[bold cyan]🚀 Starting Saltice Glassy Web UI Server in background...[/bold cyan]")
            import threading
            from ui_server import start_ui_server
            threading.Thread(target=start_ui_server, kwargs={"auto_open": True}, daemon=True).start()
            console.print("[bold green]✔ Saltice Web UI launched in default browser at http://localhost:54321[/bold green]")
            continue

        if user_input.startswith("/caveman"):
            parts = user_input.split()
            if len(parts) > 1:
                lvl = parts[1].lower()
                if lvl in ["lite", "full", "ultra", "off"]:
                    current_caveman = lvl
                    swarm_workflow.set_caveman_level(lvl)
                    console.print(f"[bold green]✔ Caveman compression set to:[/bold green] [bold yellow]{current_caveman}[/bold yellow]")
                else:
                    console.print(f"[bold red]Unknown Caveman level '{lvl}'. Options: lite (recommended), full, ultra, off[/bold red]")
            else:
                console.print(f"Current Caveman level: [bold yellow]{current_caveman}[/bold yellow] (Options: lite, full, ultra, off)")
            continue

        if user_input.startswith("/search "):
            q = user_input[8:].strip()
            console.print(f"[bold magenta]Searching web for: {q}...[/bold magenta]")
            s_res = search_web(q)
            console.print(Panel(Markdown(s_res), title=f"Search Results: {q}", border_style="magenta"))
            continue

        if user_input.startswith("/fetch "):
            u = user_input[7:].strip()
            console.print(f"[bold magenta]Fetching URL: {u}...[/bold magenta]")
            f_res = fetch_webpage(u)
            console.print(Panel(Markdown(f_res), title=f"Webpage Content: {u}", border_style="magenta"))
            continue

        if user_input.startswith("/compact"):
            from caveman import scrub_history_for_context
            parts = user_input.split(maxsplit=1)
            instructions = parts[1].strip() if len(parts) > 1 else ""
            if not session_history:
                console.print("[yellow]Session history is currently empty; nothing to compact.[/yellow]")
            else:
                before_chars = sum(len(str(t)) for t in session_history)
                for t in session_history:
                    if isinstance(t, dict) and "summary" in t and len(str(t["summary"])) > 300:
                        t["summary"] = t["summary"][:300] + "... [Compacted]"
                after_chars = sum(len(str(t)) for t in session_history)
                saved_pct = (1 - (after_chars / max(1, before_chars))) * 100
                console.print(f"[bold green]✔ Session context compacted![/bold green] (Freed {saved_pct:.1f}% context tokens)")
                if instructions:
                    console.print(f"  [dim]Active focus: {instructions}[/dim]")
            continue

        if user_input.startswith("/iterations") or user_input.startswith("/turns"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip().isdigit():
                current_iterations = int(parts[1].strip())
                console.print(f"[bold green]✔ Action iteration limit set to {current_iterations} turns.[/bold green]")
            else:
                console.print(f"Current iteration limit: [bold cyan]{current_iterations} turns[/bold cyan].")
                console.print("Usage: [bold yellow]/iterations <number>[/bold yellow] (e.g. '/iterations 60', '/iterations 100')")
            continue

        if user_input.startswith("/mcp"):
            from mcp_catalog import MCP_CATALOG, search_mcp_servers
            parts = user_input.split(maxsplit=1)
            q = parts[1].strip() if len(parts) > 1 else ""
            if not q:
                console.print(f"Curated MCP Registry: [bold cyan]{MCP_CATALOG.count():,} servers indexed[/bold cyan].")
                console.print("Usage: [bold yellow]/mcp <query>[/bold yellow] (e.g. '/mcp postgres', '/mcp browser', '/mcp github')")
            else:
                mcp_res = search_mcp_servers(q, limit=6)
                console.print(Panel(mcp_res, title=f"MCP Discovery: {q}", border_style="magenta"))
            continue

        if user_input.startswith("/browser") or user_input.startswith("/devtools"):
            parts = user_input.split(maxsplit=1)
            target = parts[1].strip() if len(parts) > 1 else ""
            if not target:
                console.print("[yellow]Usage: [bold]/browser <url_or_filepath>[/bold] (e.g. '/browser index.html' or '/browser https://example.com')[/yellow]")
            else:
                from tools import inspect_url_with_browser
                console.print(f"[bold cyan]🌐 Inspecting with Headless Chrome DevTools: {target}...[/bold cyan]")
                res = inspect_url_with_browser(target, take_screenshot=True)
                console.print(Panel(res, title=f"Chrome DevTools Report: {target}", border_style="cyan"))
            continue

        if user_input in ["/files", "/manifest"]:
            files_list = []
            if active_project.get("target_file"):
                files_list.append(active_project.get("target_file"))
            for h in session_history:
                tf = h.get("target_file")
                if tf and tf not in files_list:
                    files_list.append(tf)
            if not files_list:
                console.print("[yellow]No files recorded in session manifest yet.[/yellow]")
            else:
                manifest_lines = [f"- [bold green]{f}[/bold green] (Exists: {os.path.exists(f)})" for f in files_list]
                console.print(Panel("\n".join(manifest_lines), title="Session File Manifest", border_style="cyan"))
            continue

        if user_input.startswith("/skills"):
            parts = user_input.split(maxsplit=1)
            filter_arg = parts[1].strip() if len(parts) > 1 else None
            SKILL_MANAGER.display_skills_table(filter_query=filter_arg)
            continue

        if user_input in ["/subagents", "/subagent"]:
            from subagents import SUBAGENT_MANAGER
            SUBAGENT_MANAGER.list_all()
            continue

        if user_input in ["/rules", "/agents.md", "/conventions"]:
            from context_manager import CONTEXT_MANAGER
            rules = CONTEXT_MANAGER.get_rules_content()
            if rules:
                console.print(Panel(Markdown(rules), title="Project Rules & Conventions", border_style="cyan"))
            else:
                console.print("[yellow]No AGENTS.md or CLAUDE.md found in workspace tree.[/yellow]")
            continue

        if user_input in ["/memory", "/memories"]:
            from context_manager import CONTEXT_MANAGER
            mems = CONTEXT_MANAGER.get_memory_context()
            if mems:
                console.print(Panel(mems, title="Persistent Session Memory", border_style="green"))
            else:
                console.print("[yellow]No persistent memories recorded yet. (Use 'record_memory' tool to store)[/yellow]")
            continue

        if user_input.startswith("/artifacts"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                art_name = parts[1].strip()
                ARTIFACT_MANAGER.view_artifact(art_name)
            else:
                ARTIFACT_MANAGER.list_artifacts()
            continue

        if user_input.startswith("/iterations"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                try:
                    val = int(parts[1].strip())
                    current_iterations = val
                    if val <= 0:
                        console.print("[bold green]✔ Iteration limit disabled (Unlimited Runway).[/bold green]")
                    else:
                        console.print(f"[bold green]✔ Iteration limit set to {val} turns.[/bold green]")
                except ValueError:
                    console.print("[yellow]Usage: /iterations <N> (0 for unlimited)[/yellow]")
            else:
                lim_text = "Unlimited" if current_iterations <= 0 else f"{current_iterations} turns"
                console.print(f"Current iteration limit: [bold cyan]{lim_text}[/bold cyan]")
        if user_input in ["/history", "/chat", "/turns"]:
            if not session_history:
                console.print("[dim]No previous conversation turns in this session yet.[/dim]")
            else:
                h_table = Table(title="Conversational Chat History (Active Session)", border_style="cyan", box=box.ROUNDED)
                h_table.add_column("Turn", style="bold cyan", width=6)
                h_table.add_column("User Goal", style="bold white", width=35)
                h_table.add_column("Target / Touched Files", style="green", width=25)
                h_table.add_column("Result Summary", style="dim", width=40)
                for idx, t in enumerate(session_history, 1):
                    files_str = ", ".join(t.get("touched_files", [])) or t.get("target_file", "None")
                    h_table.add_row(
                        str(idx),
                        t.get("user_goal", "")[:70],
                        files_str[:40],
                        (t.get("summary", "") or "")[:80]
                    )
                console.print(h_table)
            continue

        if user_input in ["/sessions", "/session-list"]:
            s_list = SESSION_MANAGER.list_sessions()
            if not s_list:
                console.print("[dim]No saved sessions found in .saltice/sessions/.[/dim]")
            else:
                s_table = Table(title="Saved Conversational Sessions (.saltice/sessions/)", border_style="cyan", box=box.ROUNDED)
                s_table.add_column("Session ID", style="bold cyan")
                s_table.add_column("Created", style="dim")
                s_table.add_column("Turns", style="bold white", justify="center")
                s_table.add_column("First Goal", style="white")
                for s in s_list:
                    s_table.add_row(
                        s.get("session_id", ""),
                        s.get("created_at", "")[:19].replace("T", " "),
                        str(s.get("turns", 0)),
                        s.get("first_goal", "")[:50]
                    )
                console.print(s_table)
                console.print("[dim]Use [bold white]/resume <session_id>[/bold white] to restore any past session.[/dim]")
            continue

        if user_input.startswith("/resume"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                target_sid = parts[1].strip()
                try:
                    SESSION_MANAGER.load_session(target_sid)
                    session_history = SESSION_MANAGER.get_session_history_list()
                    console.print(f"[bold green]✔ Resumed session:[/bold green] [bold cyan]{target_sid}[/bold cyan] ({len(session_history)} turns restored)")
                except Exception as e:
                    console.print(f"[bold red]Failed to resume session '{target_sid}':[/bold red] {e}")
            else:
                console.print("[yellow]Usage: /resume <session_id> (run /sessions to list available IDs)[/yellow]")
            continue

        if user_input in ["/new", "/reset-session"]:
            new_id = SESSION_MANAGER.start_session()
            session_history = SESSION_MANAGER.get_session_history_list()
            console.print(f"[bold green]✔ Started fresh session:[/bold green] [bold cyan]{new_id}[/bold cyan]")
            continue

        if user_input in ["/state", "/session-state", "/memory-state"]:
            from session_state import SESSION_STATE
            state_data = SESSION_STATE.get_all(flatten=False)
            has_entries = any(len(v) > 0 for v in state_data.values())
            if not has_entries:
                console.print("[dim]No structured state variables stored yet.[/dim]")
            else:
                s_table = Table(title="Structured Session State Memory (4-Tier Architecture)", border_style="cyan", box=box.ROUNDED)
                s_table.add_column("Tier / Namespace", style="bold cyan", width=18)
                s_table.add_column("Key", style="bold white", width=25)
                s_table.add_column("Value", style="green", width=35)
                s_table.add_column("Lifetime / Scope", style="dim", width=25)

                for k, v in state_data.get("temp", {}).items():
                    s_table.add_row("Temporary (temp:)", k, json.dumps(v), "Current Turn Only")
                for k, v in state_data.get("session", {}).items():
                    s_table.add_row("Session ((none))", k, json.dumps(v), "Active Conversation")
                for k, v in state_data.get("user", {}).items():
                    s_table.add_row("User (user:)", k, json.dumps(v), "Across All Sessions")
                for k, v in state_data.get("app", {}).items():
                    s_table.add_row("App (app:)", k, json.dumps(v), "Global Project Workspace")

                console.print(s_table)
            continue

        if user_input.startswith("/set "):
            parts = user_input[5:].strip().split(maxsplit=1)
            if len(parts) == 2:
                k, v = parts[0], parts[1]
                from session_state import SESSION_STATE
                try:
                    val_parsed = json.loads(v)
                except Exception:
                    val_parsed = v
                SESSION_STATE.set(k, val_parsed)
                console.print(f"[bold green]✔ State updated:[/bold green] [bold cyan]{k}[/bold cyan] = {json.dumps(val_parsed)}")
            else:
                console.print("[yellow]Usage: /set <key> <value> (e.g. '/set user:theme aero-frost' or '/set target_object rocket')[/yellow]")
            continue

        if user_input.startswith("/get "):
            k = user_input[5:].strip()
            if k:
                from session_state import SESSION_STATE
                val = SESSION_STATE.get(k)
                if val is not None:
                    console.print(f"[bold cyan]{k}[/bold cyan] = [bold green]{json.dumps(val)}[/bold green]")
                else:
                    console.print(f"[yellow]Key '{k}' is not set in any active namespace.[/yellow]")
            else:
                console.print("[yellow]Usage: /get <key> (e.g. '/get target_object' or '/get user:theme')[/yellow]")
            continue

        if user_input.startswith("/clear-state"):
            parts = user_input.split(maxsplit=1)
            scope = parts[1].strip() if len(parts) > 1 else "all"
            from session_state import SESSION_STATE
            SESSION_STATE.clear_scope(scope)
            console.print(f"[bold green]✔ Cleared state scope:[/bold green] [bold cyan]{scope}[/bold cyan]")
            continue

        if user_input == "/help":
            print_help()
            continue

        if user_input in ["/tokens", "/limits", "/quota", "/balance"]:
            display_token_and_limit_dashboard()
            continue

        if user_input == "/models":
            show_models_status()
            continue

        if user_input == "/stats":
            show_stats()
            continue

        if user_input == "/benchmark":
            run_benchmark()
            continue

        if user_input == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            show_banner()
            continue

        if user_input == "/pwd":
            console.print(f"Current working directory: [bold green]{os.getcwd()}[/bold green]")
            continue

        if user_input.startswith("/cd"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                target_dir = os.path.expanduser(parts[1].strip())
                try:
                    os.chdir(target_dir)
                    console.print(f"[bold green]Working directory changed to:[/bold green] {os.getcwd()}")
                except Exception as e:
                    console.print(f"[bold red]Cannot change directory:[/bold red] {e}")
            else:
                console.print(f"Current working directory: [bold yellow]{os.getcwd()}[/bold yellow]")
            continue

        if user_input.startswith("/run "):
            cmd = user_input[5:].strip()
            console.print(f"[bold yellow]Executing:[/bold yellow] {cmd}")
            out = run_command(cmd)
            console.print(Panel(out, title=f"Output: {cmd}", border_style="white"))
            continue

        if user_input.startswith("/deploy"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                target_file = parts[1].strip()
                console.print(f"[bold cyan]Deploying {target_file} to Cloudflare Pages...[/bold cyan]")
                ok, msg, url = deploy_to_pages(target_file)
                if ok:
                    console.print(Panel(f"[bold green]✔ Deployed Successfully![/bold green]\n\n[bold white]Live Public URL:[/bold white] [bold underline bright_cyan]{url}[/bold underline bright_cyan]", title="Cloudflare Pages Deploy", border_style="green"))
                else:
                    console.print(f"[bold red]Deployment failed:[/bold red] {msg}")
            else:
                console.print("[yellow]Usage: /deploy <filepath>[/yellow]")
            continue

        if user_input.startswith("/scan"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                target_url = parts[1].strip()
                console.print(f"[bold cyan]Submitting URL to Cloudflare URL Scanner: {target_url}...[/bold cyan]")
                s_res = scan_url(target_url)
                if s_res.get("ok"):
                    console.print(Panel(f"[bold green]✔ Scan Initiated![/bold green]\n\n[dim]UUID:[/dim] {s_res.get('scan_uuid')}\n[dim]Target:[/dim] {s_res.get('url')}\n\nView security & DOM audit on Cloudflare Security Center.", title="Cloudflare URL Scanner", border_style="cyan"))
                else:
                    console.print(f"[bold red]Scan failed:[/bold red] {s_res.get('error')}")
            else:
                console.print("[yellow]Usage: /scan <url>[/yellow]")
            continue

        if user_input.startswith("/semantic "):
            q = user_input[10:].strip()
            console.print(f"[bold magenta]Searching workspace semantically using Cloudflare BGE embeddings: {q}...[/bold magenta]")
            sem_matches = semantic_code_search(q, search_dir=".")
            if sem_matches:
                sem_text = ""
                for m in sem_matches:
                    sem_text += f"### {m['file']} (Lines {m['start_line']}–{m['end_line']}) [Cosine Similarity: {m['score']:.3f}]\n```\n{m['content'][:300]}\n```\n\n"
                console.print(Panel(Markdown(sem_text), title=f"Semantic Code Matches: {q}", border_style="magenta"))
            else:
                console.print("[yellow]No semantic matches found.[/yellow]")
            continue

        if user_input in ["/telemetry", "/telemetry-stats"]:
            summary = TELEMETRY.get_summary()
            t_table = Table(title="Agent Swarm Telemetry & Win-Rates", border_style="green", box=box.ROUNDED)
            t_table.add_column("Metric", style="bold cyan")
            t_table.add_column("Value", style="bold white")
            t_table.add_row("Total Tasks Executed", str(summary.get("total_tasks", 0)))
            t_table.add_row("Average Duration", f"{summary.get('avg_duration_seconds', 0)}s")
            t_table.add_row("Syntax Pass Rate", str(summary.get("syntax_success_rate", "N/A")))
            t_table.add_row("Headless Runtime Pass Rate", str(summary.get("runtime_success_rate", "N/A")))
            for dom, cnt in summary.get("domain_breakdown", {}).items():
                t_table.add_row(f"Domain: {dom.upper()}", f"{cnt} tasks")
            console.print(t_table)
            continue

        # --- Task Execution Based on Mode ---
        try:
            from tools import infer_target_filename
            inferred = infer_target_filename(goal=user_input, default_ext=".html", cwd=".", active_file=active_project.get("target_file"))
            if inferred:
                active_project["target_file"] = inferred

            summary = "Task completed."
            if current_mode == "council":
                # Multi-Agent Debate and Consensus Synthesis
                res = swarm_workflow.run_discussion(user_input, auto_execute=True)
                summary = res if isinstance(res, str) else "Council discussion complete."
            elif current_mode == "swarm":
                # Standard Committee Flow (Architect -> Coder -> Reviewer -> Executor)
                res = swarm_workflow.run_task(user_input, auto_execute=True)
                summary = res if isinstance(res, str) else "Swarm committee task complete."
            else:
                # Flagship Saltice Antigravity Engine: Live Workspace Context + Dual-Mode Parser + Subagents
                engine = SalticeAntigravityEngine(mode=current_mode, caveman_level=current_caveman, max_iterations=current_iterations)
                summary = engine.run(user_input, session_context=session_history, target_override=active_project.get("target_file"))
                t_files = list(getattr(engine, "touched_files", []))
                SESSION_MANAGER.record_turn(
                    user_goal=user_input,
                    target_file=active_project.get("target_file"),
                    summary=summary or "Execution complete.",
                    touched_files=t_files
                )
                session_history = SESSION_MANAGER.get_session_history_list()

        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠️ Task cancelled by user (Ctrl+C). Restoring state...[/bold yellow]")
            tgt = active_project.get("target_file")
            if tgt:
                bak_file = f"{tgt}.bak"
                if os.path.exists(bak_file):
                    try:
                        import shutil
                        shutil.copy2(bak_file, tgt)
                        console.print(f"  [dim]✔ Restored {tgt} from safety backup ({bak_file}).[/dim]")
                    except Exception as be:
                        console.print(f"  [dim yellow]Backup restore notice: {be}[/dim yellow]")
            console.print("[dim]Returned to interactive prompt. Ready for next instruction.[/dim]\n")
            continue
        except Exception as e:
            console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    main()
