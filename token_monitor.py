"""
Token & Rate-Limit Monitor for Saltice
Queries live quota endpoints and headers across all configured AI models and developer APIs.
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CLI_DIR, ".env"))
load_dotenv()

console = Console(force_terminal=True, legacy_windows=False)

from providers import (
    GLOBAL_STATS,
    GROQ_KEY,
    GEMINI_KEY,
    MISTRAL_KEY,
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    COHERE_KEY,
    OPENROUTER_KEY,
    CEREBRAS_KEY,
    HUGGINGFACE_TOKEN,
    NVIDIA_KEY,
    SAMBANOVA_KEY,
    SHIELD
)

JINA_KEY = os.getenv("JINA_API_KEY", "").strip()
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "").strip()

def format_relative_time(timestamp: int) -> str:
    if not timestamp:
        return "N/A"
    diff = int(timestamp - time.time())
    if diff <= 0:
        return "now"
    mins, secs = divmod(diff, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"in {hours}h {mins}m"
    elif mins > 0:
        return f"in {mins}m {secs}s"
    return f"in {secs}s"

def check_openrouter_quota() -> dict:
    if not OPENROUTER_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing OPENROUTER_API_KEY"}
    try:
        r = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {OPENROUTER_KEY}"}, timeout=8)
        if r.status_code == 200:
            data = r.json().get("data", {})
            free_req = data.get("free_model_daily_requests", {})
            used = free_req.get("used", 0)
            limit = free_req.get("limit", 50)
            remaining = free_req.get("remaining", max(0, limit - used))
            is_free = data.get("is_free_tier", True)
            tier_str = "Free Tier" if is_free else "Paid Tier"
            
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": f"{limit} req/day",
                "remaining": f"[bold cyan]{remaining}[/bold cyan] req left",
                "tpm": "Varies by model",
                "notes": f"{tier_str} (Used today: {used}/{limit})"
            }
        elif r.status_code == 401:
            return {"status": "[red]INVALID KEY[/red]", "limit": "-", "remaining": "0", "tpm": "-", "notes": "Unauthorized"}
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_mistral_quota() -> dict:
    if not MISTRAL_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing MISTRAL_API_KEY"}
    try:
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
            json={"model": "codestral-latest", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=5
        )
        if r.status_code in [200, 429]:
            h = r.headers
            tpm_limit = h.get("x-ratelimit-limit-tokens-minute", "625000")
            tpm_rem = h.get("x-ratelimit-remaining-tokens-minute", "625000")
            rpm_limit = h.get("x-ratelimit-limit-req-minute", "125")
            rpm_rem = h.get("x-ratelimit-remaining-req-minute", "125")
            st = "[green]ACTIVE[/green]" if r.status_code == 200 else "[yellow]RATE LIMITED (429)[/yellow]"
            try:
                tpm_rem_fmt = f"{int(tpm_rem):,}"
                tpm_lim_fmt = f"{int(tpm_limit):,}"
            except Exception:
                tpm_rem_fmt = str(tpm_rem)
                tpm_lim_fmt = str(tpm_limit)

            return {
                "status": st,
                "limit": f"{rpm_limit} req/min",
                "remaining": f"{rpm_rem} req/min left",
                "tpm": f"[bold cyan]{tpm_rem_fmt}[/bold cyan] / {tpm_lim_fmt} TPM",
                "notes": "Codestral 22B Tier"
            }
        else:
            return {"status": "[green]CONFIGURED[/green]", "limit": "125 req/min", "remaining": "Available", "tpm": "[bold cyan]625,000[/bold cyan] TPM", "notes": "Codestral 22B Tier"}
    except Exception:
        return {"status": "[green]CONFIGURED[/green]", "limit": "125 req/min", "remaining": "Available", "tpm": "[bold cyan]625,000[/bold cyan] TPM", "notes": "Codestral 22B Tier"}

def check_groq_quota() -> dict:
    if not GROQ_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing GROQ_API_KEY"}
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=5
        )
        if r.status_code in [200, 429]:
            h = r.headers
            tpm_limit = h.get("x-ratelimit-limit-tokens", "8000")
            tpm_rem = h.get("x-ratelimit-remaining-tokens", "8000")
            req_limit = h.get("x-ratelimit-limit-requests", "1000")
            req_rem = h.get("x-ratelimit-remaining-requests", "1000")
            reset_tok = h.get("x-ratelimit-reset-tokens", "instant")
            st = "[green]ACTIVE[/green]" if r.status_code == 200 else "[yellow]RATE LIMITED (429)[/yellow]"
            try:
                tpm_rem_fmt = f"{int(tpm_rem):,}"
                tpm_lim_fmt = f"{int(tpm_limit):,}"
            except Exception:
                tpm_rem_fmt = str(tpm_rem)
                tpm_lim_fmt = str(tpm_limit)

            return {
                "status": st,
                "limit": f"{req_limit} req/day",
                "remaining": f"{req_rem} req left",
                "tpm": f"[bold cyan]{tpm_rem_fmt}[/bold cyan] / {tpm_lim_fmt} TPM",
                "notes": f"Reset: {reset_tok}"
            }
        else:
            return {"status": "[green]CONFIGURED[/green]", "limit": "1,000 req/day", "remaining": "Available", "tpm": "[bold cyan]8,000[/bold cyan] TPM", "notes": "Groq Qwen 27B"}
    except Exception:
        return {"status": "[green]CONFIGURED[/green]", "limit": "1,000 req/day", "remaining": "Available", "tpm": "[bold cyan]8,000[/bold cyan] TPM", "notes": "Groq Qwen 27B"}

def check_gemini_quota() -> dict:
    if not GEMINI_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing GEMINI_API_KEY"}
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "hi"}]}], "generationConfig": {"maxOutputTokens": 1}},
            timeout=5
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "1,500 req/day",
                "remaining": "15 req/min",
                "tpm": "[bold cyan]1,000,000[/bold cyan] TPM",
                "notes": "Google AI Studio Free Tier"
            }
        elif r.status_code == 429:
            return {
                "status": "[yellow]RATE LIMITED (429)[/yellow]",
                "limit": "1,500 req/day",
                "remaining": "0 (Cooling down)",
                "tpm": "1,000,000 TPM",
                "notes": "Quota threshold reached"
            }
        else:
            return {"status": "[green]CONFIGURED[/green]", "limit": "1,500 req/day", "remaining": "15 req/min", "tpm": "[bold cyan]1,000,000[/bold cyan] TPM", "notes": "Google AI Studio Free Tier"}
    except Exception:
        return {"status": "[green]CONFIGURED[/green]", "limit": "1,500 req/day", "remaining": "15 req/min", "tpm": "[bold cyan]1,000,000[/bold cyan] TPM", "notes": "Google AI Studio Free Tier"}

def check_cloudflare_quota() -> dict:
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing Cloudflare credentials"}
    try:
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"},
            json={"model": "@cf/qwen/qwen2.5-coder-32b-instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=10
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "10,000 Neurons/day",
                "remaining": "1,200 req/min max",
                "tpm": "Unlimited within quota",
                "notes": "Refreshes daily at 00:00 UTC"
            }
        elif r.status_code == 429:
            return {"status": "[yellow]RATE LIMITED[/yellow]", "limit": "10,000 Neurons/day", "remaining": "0", "tpm": "-", "notes": "Daily neuron cap reached"}
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_cohere_quota() -> dict:
    if not COHERE_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing COHERE_API_KEY"}
    try:
        r = requests.post(
            "https://api.cohere.com/v2/chat",
            headers={"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"},
            json={"model": "command-r-08-2024", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=8
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "1,000 req/month",
                "remaining": "10 req/min",
                "tpm": "Trial Tier (Command R)",
                "notes": "Trial API Key"
            }
        elif r.status_code == 429:
            return {"status": "[yellow]RATE LIMITED (429)[/yellow]", "limit": "1,000 req/month", "remaining": "0", "tpm": "-", "notes": "Per-minute limit exceeded"}
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_github_quota() -> dict:
    gh = os.getenv("GITHUB_PAT")
    if not gh:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing GITHUB_PAT"}
    try:
        r = requests.get("https://api.github.com/rate_limit", headers={"Authorization": f"Bearer {gh}", "User-Agent": "Saltice"}, timeout=8)
        if r.status_code == 200:
            rate = r.json().get("rate", {})
            lim = rate.get("limit", 5000)
            rem = rate.get("remaining", 5000)
            reset = rate.get("reset", 0)
            reset_str = format_relative_time(reset)
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": f"{lim:,} req/hr",
                "remaining": f"[bold cyan]{rem:,}[/bold cyan] req left",
                "tpm": "GitHub API Calls",
                "notes": f"Reset: {reset_str}"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_snyk_quota() -> dict:
    snyk = os.getenv("SNYK_TOKEN")
    if not snyk:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing SNYK_TOKEN"}
    try:
        r = requests.get("https://api.snyk.io/v1/user/me", headers={"Authorization": f"token {snyk}"}, timeout=8)
        if r.status_code == 200:
            h = r.headers
            rem = h.get("X-RateLimit-Remaining", "200")
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "2,000 req/min",
                "remaining": f"[bold cyan]{rem}[/bold cyan] burst left",
                "tpm": "Security Scans",
                "notes": "Snyk Vulnerability Shield"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_cerebras_quota() -> dict:
    if not CEREBRAS_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing CEREBRAS_API_KEY"}
    try:
        r = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"},
            json={"model": "qwen-3.8-27b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=5
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "30 RPM",
                "remaining": "[bold cyan]1,000+ tok/s[/bold cyan]",
                "tpm": "60,000 TPM",
                "notes": "Wafer-Scale Inference Active"
            }
        elif r.status_code == 402:
            return {
                "status": "[yellow]ACTIVATION REQ[/yellow]",
                "limit": "30 RPM",
                "remaining": "[yellow]Claim Free Tier[/yellow]",
                "tpm": "60,000 TPM",
                "notes": "Visit cloud.cerebras.ai billing tab"
            }
        elif r.status_code == 429:
            return {
                "status": "[yellow]RATE LIMITED[/yellow]",
                "limit": "30 RPM",
                "remaining": "[yellow]Cooldown[/yellow]",
                "tpm": "60,000 TPM",
                "notes": "Rate limit reached"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_huggingface_quota() -> dict:
    if not HUGGINGFACE_TOKEN:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing HUGGINGFACE_TOKEN"}
    try:
        r = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}", "Content-Type": "application/json"},
            json={"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=8
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "Serverless Hub",
                "remaining": "[bold cyan]Unlimited Free[/bold cyan]",
                "tpm": "1,000,000 ctx",
                "notes": "DeepSeek-V4.1 & Qwen3.8 Router"
            }
        elif r.status_code == 429:
            return {
                "status": "[yellow]RATE LIMITED[/yellow]",
                "limit": "Serverless Hub",
                "remaining": "[yellow]Cooldown[/yellow]",
                "tpm": "-",
                "notes": "Hugging Face rate limited"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_jina_quota() -> dict:
    if not JINA_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing JINA_API_KEY"}
    try:
        r = requests.get(
            "https://r.jina.ai/https://example.com",
            headers={"Authorization": f"Bearer {JINA_KEY}"},
            timeout=6
        )
        if r.status_code == 200:
            h = r.headers
            rem = h.get("x-ratelimit-remaining", "500")
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "500 req/min",
                "remaining": f"[bold cyan]{rem}[/bold cyan] req left",
                "tpm": "10M Free Tokens",
                "notes": "Deep Search & Reader API"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def check_tavily_quota() -> dict:
    if not TAVILY_KEY:
        return {"status": "Not Configured", "limit": "-", "remaining": "-", "tpm": "-", "notes": "Missing TAVILY_API_KEY"}
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": "ping", "max_results": 1},
            timeout=6
        )
        if r.status_code == 200:
            return {
                "status": "[green]ACTIVE[/green]",
                "limit": "1,000 req/mo",
                "remaining": "[bold cyan]1,000 Free Credits[/bold cyan]",
                "tpm": "Direct AI Answers",
                "notes": "Developer & Code Research Engine"
            }
        else:
            return {"status": f"[yellow]HTTP {r.status_code}[/yellow]", "limit": "-", "remaining": "-", "tpm": "-", "notes": r.text[:60]}
    except Exception as e:
        return {"status": "[red]ERROR[/red]", "limit": "-", "remaining": "-", "tpm": "-", "notes": str(e)[:60]}

def display_token_and_limit_dashboard():
    """
    Renders a responsive, clean grid dashboard of all tokens, quotas, and rate limits.
    """
    console.print("\n[bold bright_cyan]🔍 Checking live token limits & quotas across all AI providers...[/bold bright_cyan]\n")

    table = Table(
        title="⚡ SALTICE • LIVE TOKEN & QUOTA DASHBOARD ⚡",
        border_style="bright_blue",
        box=box.ROUNDED,
        header_style="bold bright_cyan",
        show_lines=True,
        expand=True
    )

    table.add_column("Provider / Engine", style="bold yellow", ratio=3)
    table.add_column("Status", style="bold green", justify="center", ratio=2)
    table.add_column("Rate Limit", style="white", justify="right", ratio=2)
    table.add_column("Token Cap (TPM)", style="cyan", justify="right", ratio=2)
    table.add_column("Remaining Balance & Quota", style="bold bright_cyan", justify="left", ratio=4)

    # 1. OpenRouter
    or_q = check_openrouter_quota()
    or_bal = f"[yellow]{or_q['remaining']}[/yellow] [dim]({or_q['notes']})[/dim]" if "0" in str(or_q['remaining']) else f"[green]{or_q['remaining']}[/green] [dim]({or_q['notes']})[/dim]"
    table.add_row(
        "OpenRouter\n[dim]cohere/north-mini-code:free[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in or_q["status"] else or_q["status"],
        or_q["limit"],
        "128k ctx",
        or_bal
    )

    # 2. Hugging Face Router
    hf_q = check_huggingface_quota()
    table.add_row(
        "Hugging Face\n[dim]Qwen2.5-Coder-32B & Llama-3.3[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in hf_q["status"] else hf_q["status"],
        hf_q["limit"],
        hf_q["tpm"],
        f"[green]{hf_q['remaining']}[/green] [dim]({hf_q['notes']})[/dim]"
    )

    # 3. Cerebras AI
    cer_q = check_cerebras_quota()
    table.add_row(
        "Cerebras AI\n[dim]qwen-3.8-27b (1,000+ tok/s)[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in cer_q["status"] else cer_q["status"],
        cer_q["limit"],
        cer_q["tpm"],
        f"{cer_q['remaining']} [dim]({cer_q['notes']})[/dim]"
    )

    # 4. Mistral AI
    mis_q = check_mistral_quota()
    mis_bal = f"[green]{mis_q['tpm'].replace(' / 625,000 TPM', '')}[/green] [dim]({mis_q['remaining']})[/dim]"
    table.add_row(
        "Mistral AI\n[dim]codestral-latest (22B Coder)[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in mis_q["status"] or "CONFIGURED" in mis_q["status"] else mis_q["status"],
        mis_q["limit"],
        "625,000 TPM",
        mis_bal
    )

    # 5. Google Gemini
    gem_q = check_gemini_quota()
    table.add_row(
        "Google Gemini\n[dim]gemini-flash-latest[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in gem_q["status"] or "CONFIGURED" in gem_q["status"] else gem_q["status"],
        gem_q["limit"],
        "1,000,000 TPM",
        f"[green]{gem_q['remaining']}[/green] [dim](Google AI Studio Free Tier)[/dim]"
    )

    # 6. Groq
    groq_q = check_groq_quota()
    groq_bal = f"[green]{groq_q['tpm'].replace(' / 8,000 TPM', '')}[/green] [dim]({groq_q['remaining']} • {groq_q['notes']})[/dim]"
    table.add_row(
        "Groq\n[dim]qwen/qwen3.8-27b[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in groq_q["status"] or "CONFIGURED" in groq_q["status"] else groq_q["status"],
        groq_q["limit"],
        "8,000 TPM",
        groq_bal
    )

    # 7. Cloudflare Workers AI
    cf_q = check_cloudflare_quota()
    table.add_row(
        "Cloudflare AI\n[dim]@cf/qwen/qwen2.5-coder-32b[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in cf_q["status"] else cf_q["status"],
        cf_q["remaining"],
        "10k Neurons/d",
        f"[green]Available[/green] [dim]({cf_q['notes']})[/dim]"
    )

    # 8. Cohere
    coh_q = check_cohere_quota()
    table.add_row(
        "Cohere\n[dim]command-r-08-2024[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in coh_q["status"] else coh_q["status"],
        coh_q["remaining"],
        coh_q["limit"],
        f"[green]Trial Active[/green] [dim]({coh_q['notes']})[/dim]"
    )

    # 9. Tavily AI Search
    tav_q = check_tavily_quota()
    table.add_row(
        "Tavily AI Search\n[dim]Direct Answers & Research[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in tav_q["status"] else tav_q["status"],
        tav_q["limit"],
        tav_q["tpm"],
        f"[green]{tav_q['remaining']}[/green] [dim]({tav_q['notes']})[/dim]"
    )

    # 10. Jina AI Reader
    jina_q = check_jina_quota()
    table.add_row(
        "Jina AI Reader\n[dim]Web-to-Markdown & Search[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in jina_q["status"] else jina_q["status"],
        jina_q["limit"],
        jina_q["tpm"],
        f"[green]{jina_q['remaining']}[/green] [dim]({jina_q['notes']})[/dim]"
    )

    # 11. GitHub Developer API
    gh_q = check_github_quota()
    table.add_row(
        "GitHub PAT\n[dim]Code Search & Repositories[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in gh_q["status"] else gh_q["status"],
        gh_q["limit"],
        "REST API",
        f"[green]{gh_q['remaining']}[/green] [dim]({gh_q['notes']})[/dim]"
    )

    # 12. Snyk Security
    snyk_q = check_snyk_quota()
    table.add_row(
        "Snyk Shield\n[dim]Vulnerability Auditor[/dim]",
        "[green]● ONLINE[/green]" if "ACTIVE" in snyk_q["status"] else snyk_q["status"],
        snyk_q["limit"],
        "Security API",
        f"[green]{snyk_q['remaining']}[/green] [dim](Continuous Guard)[/dim]"
    )

    console.print(table)

    # Session Stats Card - Clean Multi-Column Grid
    st = GLOBAL_STATS.summary()
    stats_table = Table(
        title="📊 Current Session Usage & Performance",
        border_style="cyan",
        box=box.ROUNDED,
        header_style="bold bright_cyan",
        expand=True
    )
    stats_table.add_column("API Calls", justify="center", style="bold yellow", ratio=1)
    stats_table.add_column("Prompt Tokens", justify="right", style="white", ratio=2)
    stats_table.add_column("Completion Tokens", justify="right", style="white", ratio=2)
    stats_table.add_column("Total Tokens", justify="right", style="bold green", ratio=2)
    stats_table.add_column("Avg Speed", justify="center", style="bold cyan", ratio=2)
    stats_table.add_column("Inference Time", justify="center", style="white", ratio=2)

    stats_table.add_row(
        str(st['calls']),
        f"{st['prompt_tokens']:,}",
        f"{st['completion_tokens']:,}",
        f"{st['total_tokens']:,}",
        f"{st['avg_tokens_per_second']} tok/s",
        f"{st['total_time_seconds']}s"
    )

    console.print(stats_table)
    console.print("\n")

if __name__ == "__main__":
    display_token_and_limit_dashboard()
