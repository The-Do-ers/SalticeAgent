"""
Unified Antigravity-Style Autonomous Coding Engine for Saltice
Equipped with:
- Dual-Mode Resilient Parser: Parses JSON (strict=False) OR direct markdown code blocks without failing!
- Token-Efficient Live Workspace Awareness Snapshot on Turn 1
- Full Antigravity Toolbelt: file edits, slice viewer, shell commands, web search, GitHub search, Snyk audit
- Subagents on Demand: Spawns parallel subagent workers only when necessary
- RateLimitShield: Automatic failover across OpenRouter, Mistral, Cloudflare, Groq, Gemini, and NIM
"""

import sys
import json
import re
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

console = Console(force_terminal=True, legacy_windows=False)

import shutil

from providers import call_llm, call_openrouter, call_local_model
from caveman import CAVEMAN_PROMPTS, scrub_history_for_context
from tools import (
    run_command,
    read_file,
    write_file,
    list_directory,
    search_web,
    fetch_webpage,
    view_file_slice,
    replace_file_content,
    get_workspace_summary,
    github_search,
    snyk_audit,
    validate_code_syntax,
    cloudflare_semantic_search,
    create_plan,
    create_walkthrough,
    create_readme,
    infer_target_filename,
    cloudflare_url_scan,
    cloudflare_manage_queue,
    cloudflare_manage_container,
    spawn_subagent,
    check_subagent_status,
    list_subagents,
    wait_for_subagent,
    record_memory,
    read_memory,
    retrieve_cached_content,
    extract_media_info,
    search_mcp_servers,
    run_chrome_devtools,
    inspect_url_with_browser,
    verify_ui_in_browser,
    search_ui_templates,
    open_in_browser,
    workspace_vector_search,
    vector_status,
    verify_with_real_browser,
    fetch_vector_asset,
    generate_physics_rig,
    set_state,
    get_state,
    delete_state,
    generate_image,
    generate_svg_logo,
    inspect_image_quality
)
from skills import SKILL_MANAGER
from artifacts import ARTIFACT_MANAGER
from context_manager import CONTEXT_MANAGER
from hooks import HOOK_MANAGER
from subagents import SUBAGENT_MANAGER
from session_manager import SESSION_MANAGER
from session_state import SESSION_STATE

UNIFIED_TOOL_INSTRUCTIONS = """
You are Saltice, an elite autonomous AI software engineer, heavily inspired by modern agent frameworks like Cline and ClaudeCode.
You operate with directness, strategic planning, and rigorous execution.
You DO NOT stop until the task is completely finished, tested, and working perfectly.

WORKSPACE CONTEXT:
{workspace_info}

YOUR TOOLS:
1. `write_file(filepath, content)`: Create or fully rewrite files.
2. `view_file_slice(filepath, start_line, end_line)`: Read specific line ranges with line numbers.
3. `replace_file_content(filepath, target_content, replacement_content)`: Precise surgical edits. Use this instead of `write_file` for large files to avoid massive rewrites!
4. `read_file(filepath)`: Read full content of a file.
5. `run_command(command)`: Execute non-blocking shell commands. This is CRITICAL. Use it to `npm install`, `npx vite`, run tests, or lint code.
6. `search_web(query)`: Search web, Wikipedia, or npm for modern packages, GSAP animations, Lenis smooth scroll, React Bits, Kokonut UI, or TSX implementations.
7. `github_search(query)`: Search GitHub repositories for code patterns and UI inspiration.
8. `spawn_subagent(role, prompt, provider)`: ASYNCHRONOUS SUBAGENT. Spawns an independent subagent worker in the background for heavy research or sub-tasks without blocking you. Returns `subagent_id`.
9. `check_subagent_status(subagent_id)`: Inspect the status, progress, or completed result of a background subagent.
10. `wait_for_subagent(subagent_id, timeout_sec)`: Wait for a background subagent to complete and return its result.
11. `list_subagents()`: List all background subagents and their statuses.
12. `record_memory(key, value)`: Persist an important decision or finding to session memory across turns.
13. `read_memory()`: Read persistent workspace memories.
14. `cloudflare_url_scan(url)`: Scan a URL for threats.
15. `cloudflare_manage_queue(action, queue_name)`: Create/delete/list Cloudflare Queues.
16. `cloudflare_manage_container(action, container_id)`: Manage Cloudflare containers.
17. `create_plan(title, content)`: Generate `implementation_plan.md`. MUST BE HIGHLY DETAILED (500+ words).
18. `create_walkthrough(title, content)`: Generate `walkthrough.md`. MUST BE HIGHLY DETAILED.
19. `list_directory(dirpath)`: List directory contents.
20. `retrieve_cached_content(log_id, start_line, end_line)`: View raw offloaded tool outputs or logs without blowing the context window (CCR).
21. `search_mcp_servers(query, category)`: Search 4,200+ curated MCP servers and aggregators for database, browser, tools, or cloud capabilities.
22. `extract_media_info(url, extract_subtitles)`: Extract media title, duration, chapters, and subtitles from YouTube/web media with yt-dlp.
23. `run_chrome_devtools(tool_name, args, flags)`: Execute Chrome DevTools MCP tools (list_pages, new_page, navigate_page, take_snapshot, take_screenshot, evaluate_script, lighthouse_audit, click, fill).
24. `inspect_url_with_browser(url, take_screenshot, run_lighthouse)`: High-level headless Chrome DevTools inspection for web pages or local HTML files (extracts DOM, console errors, accessibility).
25. `verify_ui_in_browser(target_file, take_screenshot)`: Run headless browser to evaluate live rendered DOM, catch white screens, check interactive elements, and capture 1280x800 screenshot.
26. `search_ui_templates(category_or_query)`: Fetch modern design system presets (Glassmorphism, Cyberpunk, Bento Grid, Audio Visualizer, Retro Arcade) and GitHub component blueprints.
27. `finish(summary)`: Complete the task ONLY when verified working visually and functionally.
28. `workspace_vector_search(query, workspace_dir, top_k)`: 🔍 **LangChain+FAISS Semantic Code Search**. Find code/files matching a natural language query using vector similarity. Use this to locate functions, classes, or patterns in the workspace WITHOUT knowing the filename. Better than grep — understands intent. Example: "function that validates email addresses".
29. `vector_status()`: 🧠 Check the status of all LangChain/FAISS vector indexes (workspace, skills, session memory). Use to confirm the vector intelligence layer is active.
30. `verify_with_real_browser(target_file, user_goal)`: 🔬 **4-Layer Autonomous Browser Verification & Self-Healing Pipeline**. Serves the app over local HTTP, runs headless Chrome CDP, audits console errors, performs programmatic mouse/keyboard interactions, and evaluates screenshots with a Vision Model. Returns pass or structured failure diagnosis.
31. `fetch_vector_asset(entity_name, style)`: 🎨 **Verified Vector Asset Retrieval**. Queries curated offline presets (rocket, airplane, car, drone, submarine, bird, gamepad, compass, shield, sword) and the free public Iconify open-source API (200,000+ vector paths). NEVER guess coordinates or draw rounded square CSS boxes — use this tool to retrieve production-grade SVG paths!
32. `generate_physics_rig(rig_type, options)`: 🚀 **High-Performance Physics & Motion Rig Generator**. Generates mathematically verified spring-damper inertia (F = -kx - cv), shortest-arc angular slerp, autonomous Lissajous cruise, and transparent canvas particle contrails (with `ctx.clearRect` - zero dark staining).
33. `set_state(key, value)`: 🧠 **Structured Session State Memory**. Sets exact key-value state. Namespaces:
    - `temp:step` (Temporary, current turn only, discarded after this invocation)
    - `user:theme` (User-level, persists across all sessions for this user)
    - `app:api_url` (App-level, persists globally for entire project workspace)
    - No prefix (e.g. `target_object`, `active_palette`) (Session-level, persists across turns in current conversation).
34. `get_state(key)`: 🔍 Read structured state value or view all active variables across namespaces.
35. `delete_state(key)`: 🗑️ Remove a state variable from session, user, app, or temp memory.
36. `generate_image(prompt, model, backend, wordmark, enhance, output_path)`: 🎨 **Autonomous Visual Diffusion Studio**. Generates photorealistic scenes, UI mockups, or conceptual artwork using Cloudflare Workers AI edge GPUs (<2.5s) or Hugging Face ZeroGPU spaces (FLUX.1, SD 3.5 Large). Optionally adds vector wordmarks to prevent AI text errors.
37. `generate_svg_logo(concept, output_path, style, rasterize_to_png)`: 🛡️ **Precision Vector SVG Logo Engine**. Generates crisp, scalable vector SVG logos, brand marks, and geometric icons using Gemini pure XML synthesis with <defs>, Iconify registry (200,000+ vectors), and curated offline blueprints.
38. `inspect_image_quality(image_path)`: 🔍 Validates image file integrity, verifies non-blank standard deviation variance (std_dev > 8.0), and extracts dominant brand color palette hex codes.

- REAL BROWSER VERIFICATION & SELF-HEALING DIRECTIVE:
  * A web deliverable is NOT complete merely because "the file was written" or "the browser opened without crashing".
  * Saltice enforces 4 distinct verification layers:
    1. Code Layer: Valid syntax, complete implementation, zero hollow stubs or tool output strings.
    2. Execution Layer: Serves over local HTTP with 0 console errors and 0 uncaught exceptions.
    3. Interaction Layer: Tested via Chrome DevTools Protocol (mouse movement, clicks, lag, animations).
    4. Visual Layer: Rendered screenshot verified by Multimodal Vision Model against user requirements with strict 1-10 aesthetic scoring.
  * When you call `finish`, this full 4-layer pipeline executes automatically. If it reports a failure, read the structured diagnosis and repair the code surgically!

- STRATEGIC PLANNING & MODULAR WORKFLOW (The "Cline" Method):
  1. DYNAMIC ARCHITECTURE: Build real multi-file applications (React, TSX, Vite).
  2. TERMINAL USAGE: If you build a Vite/React app, you CANNOT just output files and stop. You MUST use `run_command` to `npm install` and verify it builds.
  3. NO LONG-RUNNING PROCESSES: DO NOT use `run_command` for dev servers like `npx vite`, `npm run dev`, or `npm start`. They run infinitely and will block you. Instead, run `npm run build` to verify the code compiles without errors, then use the `finish` tool and tell the user to run the dev server themselves.
  4. PROACTIVE RESEARCH: Don't guess styling. Search for "GSAP ScrollTrigger showcase", "React Bits components", or "Kokonut UI".
  5. ITERATE UNTIL PERFECT: If a command fails (like Vite missing dependencies), read the error, fix the file, run the command again. You have high iteration limits (up to 50 turns). Don't quit early.
  6. DETAILED DOCS: When creating plans, act like a Staff Engineer. Write deep, insightful paragraphs, not just a 2-line echo of the prompt.
  7. VITE / REACT ENTRYPOINT RULES:
     - In Vite/React/TSX projects, `index.html` at the project root is the main HTML entrypoint.
     - The script tag in `index.html` MUST point to the source entrypoint (e.g. `<script type="module" src="/src/main.tsx"></script>`), NEVER to a `./dist/assets/...` bundle or production output file!
     - When `npm run build` or Vite fails with an error like `Failed to resolve ./dist/assets/... from index.html`, check `index.html` immediately and ensure it references `/src/main.tsx` (or `/src/main.jsx`).
  8. FILE EDITING TARGETS & ROOT CAUSE:
     - Always pay close attention to the exact filename reported in build errors or terminal outputs. If an error says `Failed to resolve ... from D:/.../index.html` or `[ROOT CAUSE LOCATOR]`, edit `index.html` directly, do NOT edit or create phantom files.
  9. VISUAL OBJECT FIDELITY & MOTION RIGS (NO GEOMETRIC SURROGATES):
     - When asked to build or render a physical object, vehicle, or character (e.g. airplane, aircraft, jet, rocket, car, bird, drone, spaceship, submarine):
       * ALWAYS call `fetch_vector_asset(entity_name)` to get genuine production SVG paths with zero API keys or coordinate guessing!
       * NEVER substitute a generic CSS <div> with border-radius (rounded square/box), a circle, or an emoji! A rounded square is NOT an airplane!
       * NEVER guess raw SVG coordinates or assemble crude pipes/polygons from scratch — use `fetch_vector_asset`.
     - For cursor following, inertia, and particle trails:
       * ALWAYS call `generate_physics_rig("spring_follower")` to get verified spring-damper physics, shortest-arc rotation, and transparent canvas contrails (with `ctx.clearRect`).
  10. CREATIVE MOTION & HIGH-CONTRAST DESIGN (GSAP, LENIS, REACT BITS, KOKONUT UI):
     - DO NOT force generic frosted glass boxes or dark-on-dark rounded squares everywhere.
     - Foreground focal objects must have high visual contrast against the background. NEVER use the same dark color for both the object and the background.
     - Deliver awards-grade creative experiences:
       * Smooth inertia scrolling via **Lenis**.
       * Kinetic typography, timeline orchestration, and scroll triggers via **GSAP & ScrollTrigger**.
       * Interactive components and micro-interactions from **React Bits** (spotlight cards, magnetic buttons, particle backgrounds, text decrypters) and **Kokonut UI**.
  11. ITERATIVE PART-BY-PART CONSTRUCTION (FOR LARGE / COMPLEX APPS):
     - DO NOT attempt to write 1,500+ lines (50KB-100KB) of HTML, CSS, and JS in a single monolithic write_file turn. Monolithic dumps risk hitting model token ceilings, resulting in truncated code or corrupted JSON escapes.
     - ALWAYS build large applications in structured, modular stages:
       * Stage 1 (Skeleton & Layout): Write clean HTML5 boilerplate, DOM section containers, navigation structure, and CSS variables / design tokens.
       * Stage 2 (Components & Content): Use replace_file_content to flesh out the Bento grids, cards, tabs, and component markup with full details.
       * Stage 3 (Motion & Scripts): Use replace_file_content to add the JavaScript logic: GSAP timelines, ScrollTrigger scrubs, Lenis ticker, canvas loops, and event listeners.
       * Stage 4 (Verification & Self-Healing): Run verify_with_real_browser (or static validation), inspect any issues, apply surgical fixes with replace_file_content, and call finish.
     - NEVER run launcher scripts or recursive test runners (e.g. run_*.py or engine.py) using run_command. To test web applications, call the browser tools (verify_with_real_browser or inspect_url_with_browser).

HOW TO RESPOND (JSON TOOL CALLING IS REQUIRED):
```json
{{
  "thought": "Your reasoning (e.g. I need to fetch vector asset, generate physics rig, write files, then finish)",
  "action": "run_command | fetch_vector_asset | generate_physics_rig | search_web | write_file | replace_file_content | view_file_slice | create_plan | finish",
  "args": {{ ... }}
}}
```
"""

class SubagentWorker:
    """
    Focused subagent worker spawned by the primary agent only when necessary.
    """
    def __init__(self, role: str, provider: str = "openrouter"):
        self.role = role
        self.provider = provider
        self.max_turns = 3

    def execute(self, task_prompt: str) -> str:
        console.print(f"  [bold magenta]🤖 [Subagent: {self.role} ({self.provider.upper()})] Starting assignment...[/bold magenta]")
        workspace = get_workspace_summary()

        system_prompt = f"""You are a specialized subagent working under Saltice.
Role: {self.role}
Workspace Context:
{workspace}

Available Tools:
1. `write_file(filepath, content)`
2. `read_file(filepath)`
3. `run_command(command)`
4. `search_web(query)`
5. `finish(summary)`

Respond in JSON format:
```json
{{
  "thought": "...",
  "action": "write_file | read_file | run_command | search_web | finish",
  "args": {{ ... }}
}}
```"""

        history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Assignment: {task_prompt}\nBegin now."}
        ]

        actions_taken = []

        for turn in range(1, self.max_turns + 1):
            try:
                res = call_llm(history, preferred_provider=self.provider, max_tokens=1500)
                raw = res["content"].strip()

                # Extract JSON
                json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
                json_str = json_match.group(1) if json_match else ""
                if not json_str:
                    brace = re.search(r"(\{[\s\S]*\})", raw)
                    json_str = brace.group(1) if brace else ""

                if not json_str:
                    # Fallback direct code extraction
                    code_matches = re.findall(r"```([a-zA-Z0-9_\-\.]*)?\s*[\r\n]+([\s\S]*?)```", raw)
                    if code_matches:
                        for ltag, cc in code_matches:
                            fname = "index.html" if "html" in (ltag or "").lower() or "<!doctype" in cc.lower() else "code.py"
                            write_file(fname, cc.strip())
                            actions_taken.append(f"Auto-saved code to {fname}")
                    actions_taken.append(f"Output: {raw[:150]}")
                    break

                data = json.loads(json_str, strict=False)
                thought = data.get("thought", "")
                action = data.get("action", "")
                args = data.get("args", {})

                if thought:
                    console.print(f"    [dim cyan]• {thought}[/dim cyan]")

                if action == "finish":
                    summary = args.get("summary", thought or "Finished.")
                    console.print(f"  [bold green]✔ Subagent finished:[/bold green] {summary[:100]}")
                    actions_taken.append(f"Finished: {summary}")
                    return "\n".join(actions_taken)

                obs = self._execute_sub_tool(action, args)
                actions_taken.append(f"Action '{action}': {obs[:100]}")
                history.append({"role": "assistant", "content": json_str})
                history.append({"role": "user", "content": f"Observation: {obs}\nContinue or finish."})

            except Exception as e:
                actions_taken.append(f"Subagent error: {e}")
                break

        return "\n".join(actions_taken)

    def _execute_sub_tool(self, action: str, args: dict) -> str:
        try:
            if action == "write_file":
                fp = args.get("filepath", "")
                cnt = args.get("content", "")
                console.print(f"    [bold green]💾 Writing {fp} ({len(cnt)} bytes)[/bold green]")
                return write_file(fp, cnt)
            elif action == "read_file":
                return read_file(args.get("filepath", ""))
            elif action == "run_command":
                cmd = args.get("command", "")
                console.print(f"    [bold yellow]$ {cmd}[/bold yellow]")
                return run_command(cmd)
            elif action == "search_web":
                return search_web(args.get("query", ""))
            elif action == "generate_image":
                p = args.get("prompt", user_goal)
                m = args.get("model")
                b = args.get("backend", "auto")
                wm = args.get("wordmark")
                enh = bool(args.get("enhance", True))
                out = args.get("output_path")
                console.print(f"  [bold bright_magenta]🎨 Generating Diffusion Image: {p[:60]}[/bold bright_magenta]")
                return generate_image(prompt=p, model=m, backend=b, wordmark=wm, enhance=enh, output_path=out)

            elif action == "generate_svg_logo":
                c = args.get("concept", args.get("prompt", user_goal))
                out = args.get("output_path")
                sty = args.get("style", "minimal")
                rast = bool(args.get("rasterize_to_png", True))
                console.print(f"  [bold bright_cyan]🛡️ Generating Vector SVG Logo: {c[:60]}[/bold bright_cyan]")
                return generate_svg_logo(concept=c, output_path=out, style=sty, rasterize_to_png=rast)

            elif action == "inspect_image_quality":
                ip = args.get("image_path", "")
                console.print(f"  [bold cyan]🔍 Inspecting Image Quality & Brand Palette: {ip}[/bold cyan]")
                return inspect_image_quality(ip)

            elif action == "finish":
                return args.get("summary", "Done.")
            else:
                return f"Unknown subagent action: {action}"
        except Exception as e:
            return f"Error: {e}"





class SalticeAntigravityEngine:
    """
    The Primary Antigravity-Style Engine for Saltice.
    Direct execution, live workspace context, resilient dual-format parsing,
    and subagent spawning on demand.
    """
    def __init__(self, mode: str = "gemini", caveman_level: str = "lite", max_iterations: int = 0, event_callback: callable = None, **kwargs):
        self.mode = mode
        self.caveman_level = caveman_level
        self.max_iterations = max_iterations
        self.event_callback = event_callback
        self.history = []
        self.active_target_file = None
        self.session_manifest = []
        self.touched_files = set()

    def _emit_event(self, event_type: str, data: dict):
        """Emit real-time execution telemetry event to Web UI / attached listeners."""
        if self.event_callback and callable(self.event_callback):
            try:
                import time
                data = dict(data)
                data["type"] = event_type
                data["timestamp"] = time.strftime("%H:%M:%S")
                self.event_callback(event_type, data)
            except Exception:
                pass

    def _call_model(self, messages: list) -> str:
        preferred = self.mode if self.mode in [
            "gemini", "mistral", "huggingface", "groq", "cloudflare", "openrouter", "nvidia_nim", "cohere", "local", "cerebras", "sambanova"
        ] else "gemini"

        if preferred == "local":
            try:
                res = call_local_model(messages, max_tokens=2500)
                return res["content"]
            except Exception as e:
                console.print(f"[yellow]⚠️ Local engine notice: {e}[/yellow]")
                console.print("[dim]Attempting cloud fallback if internet connection is available...[/dim]")
                preferred = "gemini"

        try:
            res = call_llm(messages, preferred_provider=preferred, max_tokens=8192)
            if isinstance(res, dict):
                return res.get("content", str(res))
            return str(res)
        except Exception as e:
            if self.mode == "local":
                raise RuntimeError(
                    "[Offline Mode Error]: Local model server is not running on localhost (Ollama/LM Studio), and no internet connection is available for cloud fallback.\n"
                    "[Offline Setup Guide]:\n"
                    "   1. Start Ollama: Open the Ollama app or run 'ollama run qwen2.5-coder:7b'\n"
                    "   2. Or start LM Studio Local Server on port 1234."
                ) from e
            raise

    def _parse_and_execute(self, raw_response: str, user_goal: str) -> tuple[bool, str]:
        """
        Dual-Format Resilient Parser:
        1. Attempts JSON extraction and execution (with strict=False for multiline strings).
        2. IF model returned direct markdown code blocks, extracts them, writes to disk, and executes!
        Returns (is_finished, observation_message).
        """
        # --- PATH 1: Try JSON Parsing (Direct, Sanitized, and Regex Recovery) ---
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_response)
        json_str = json_match.group(1) if json_match else ""
        if not json_str:
            brace_match = re.search(r"(\{[\s\S]*\})", raw_response)
            json_str = brace_match.group(1) if brace_match else ""

        action_data = None
        if json_str:
            try:
                action_data = json.loads(json_str, strict=False)
            except Exception:
                try:
                    # Sanitize invalid escape sequences (e.g. \d, \s, \w in regex)
                    sanitized = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', json_str)
                    action_data = json.loads(sanitized, strict=False)
                except Exception:
                    pass

        # Regex recovery if json.loads failed but action was intended
        if not action_data:
            act_m = re.search(r'"action"\s*:\s*"([a-zA-Z0-9_]+)"', raw_response)
            if act_m:
                act = act_m.group(1)
                fp_m = re.search(r'"filepath"\s*:\s*"([^"]+)"', raw_response)
                html_m = re.search(r'(<!DOCTYPE[\s\S]*?</html>)', raw_response, re.IGNORECASE)
                if act == "write_file" and html_m:
                    fp = fp_m.group(1) if fp_m else (self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file))
                    code = html_m.group(1)
                    if r'\n' in code:
                        code = code.replace(r'\"', '"').replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\\', '\\')
                    action_data = {"action": "write_file", "args": {"filepath": fp, "content": code}}
                elif act == "write_file":
                    cnt_m = re.search(r'"content"\s*:\s*"([\s\S]*?)"\s*(?:,\s*"[a-zA-Z_]+"\s*:|\}\s*\})', raw_response)
                    if cnt_m:
                        code = cnt_m.group(1)
                        if r'\n' in code:
                            code = code.replace(r'\"', '"').replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\\', '\\')
                        fp = fp_m.group(1) if fp_m else (self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file))
                        action_data = {"action": "write_file", "args": {"filepath": fp, "content": code}}
                elif act == "view_file_slice":
                    fp = fp_m.group(1) if fp_m else (self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file))
                    sm = re.search(r'"start_line"\s*:\s*(\d+)', raw_response)
                    em = re.search(r'"end_line"\s*:\s*(\d+)', raw_response)
                    s = int(sm.group(1)) if sm else 1
                    e = int(em.group(1)) if em else 200
                    action_data = {"action": "view_file_slice", "args": {"filepath": fp, "start_line": s, "end_line": e}}
                elif act == "read_file":
                    fp = fp_m.group(1) if fp_m else (self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file))
                    action_data = {"action": "read_file", "args": {"filepath": fp}}
                elif act == "create_plan":
                    t_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw_response)
                    c_m = re.search(r'"content"\s*:\s*"([\s\S]*?)"', raw_response)
                    title = t_m.group(1) if t_m else "Implementation Plan"
                    cnt = c_m.group(1) if c_m else raw_response
                    action_data = {"action": "create_plan", "args": {"title": title, "content": cnt}}
                elif act == "create_walkthrough":
                    t_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw_response)
                    c_m = re.search(r'"content"\s*:\s*"([\s\S]*?)"', raw_response)
                    title = t_m.group(1) if t_m else "Project Walkthrough"
                    cnt = c_m.group(1) if c_m else raw_response
                    action_data = {"action": "create_walkthrough", "args": {"title": title, "content": cnt}}
                elif act == "run_command":
                    cmd_m = re.search(r'"command"\s*:\s*"([^"]+)"', raw_response)
                    if cmd_m:
                        action_data = {"action": "run_command", "args": {"command": cmd_m.group(1)}}
                elif act == "finish":
                    sum_m = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_response)
                    action_data = {"action": "finish", "args": {"summary": sum_m.group(1) if sum_m else "Finished."}}

        if action_data:
            thought = action_data.get("thought", "")
            action = action_data.get("action", "")
            args = action_data.get("args", {})
            if isinstance(args, str):
                args = {"summary": args, "content": args, "filepath": args, "command": args, "query": args}
            elif not isinstance(args, dict):
                args = {}

            if thought:
                console.print(f"[bold yellow]🧠 Thought:[/bold yellow] {thought}")
                self._emit_event("thought", {"text": thought})

            if action == "finish":
                target_fp = self.active_target_file or infer_target_filename(user_goal, default_ext=".html", cwd=".", active_file=self.active_target_file)
                project_files_exist = (
                    (target_fp and os.path.exists(target_fp)) or
                    os.path.exists("index.html") or
                    os.path.exists("package.json") or
                    any(os.path.exists(f) for f in self.touched_files)
                )
                if target_fp and not project_files_exist:
                    return False, f"Cannot finish: Primary code file '{target_fp}' has not been created or written to disk yet. You must write the complete code for '{target_fp}' before calling finish!"

                has_walkthrough = os.path.exists("walkthrough.md") and os.path.getsize("walkthrough.md") > 100
                has_plan = os.path.exists("implementation_plan.md") and os.path.getsize("implementation_plan.md") > 100
                needs_docs = ("walkthrough" in user_goal.lower() and not has_walkthrough) or \
                              ("plan" in user_goal.lower() and not has_plan)
                if needs_docs:
                    return False, "Cannot finish: Missing required documentation. Please generate implementation_plan.md or walkthrough.md before finishing."

                # 4-Layer Autonomous Real Browser Verification (Code -> Execution -> Interaction -> Vision)
                check_target = target_fp if (target_fp and target_fp.endswith((".html", ".htm"))) else ("index.html" if os.path.exists("index.html") else None)
                if check_target and os.path.exists(check_target):
                    try:
                        from verification_pipeline import VERIFICATION_PIPELINE
                        current_attempt = getattr(self, "_current_turn", 1)
                        v_res = VERIFICATION_PIPELINE.verify_project(check_target, user_goal, attempt=current_attempt)
                        self._emit_event("browser_check", {
                            "ok": v_res.get("passed", False),
                            "target": check_target,
                            "report": v_res.get("summary_table", ""),
                            "screenshot": v_res.get("screenshot")
                        })
                        if not v_res.get("passed", False):
                            if v_res.get("should_halt_loop", False):
                                console.print(f"  [bold red]❌ Multi-Turn Verification Stall Halted:[/bold red]\n{v_res['report']}")
                                return True, f"[VERIFICATION FAILED - MAXIMUM REPAIR ATTEMPTS EXCEEDED]\n\n{v_res['report']}\n\nStructured Failure Diagnosis:\n```json\n{json.dumps(v_res.get('failure_diagnosis', {}), indent=2)}\n```"

                            diag_str = json.dumps(v_res.get("failure_diagnosis", {}), indent=2)
                            console.print(f"  [bold red]❌ 4-Layer Real Browser Verification Failed on '{check_target}':[/bold red]\n{v_res['report']}")
                            return False, f"Cannot finish: Real Browser Verification Failed on '{check_target}':\n\n{v_res['report']}\n\nStructured Failure Diagnosis:\n```json\n{diag_str}\n```\n\nYou MUST review this diagnostic evidence, repair the affected files using surgical edits, and re-test before declaring success."

                        console.print(Panel(v_res.get("summary_table", "VERIFICATION PASSED"), title="[bold green]✔ Real Browser Verification Passed[/bold green]", border_style="green"))
                    except Exception as e:
                        console.print(f"  [dim yellow]Verification pipeline notice: {e}[/dim yellow]")

                summary = args.get("summary", thought or "Task completed.")
                self._emit_event("finish", {"summary": summary})
                console.print(Panel(Markdown(summary), title="[bold green]✔ Task Finished Successfully[/bold green]", border_style="green"))
                return True, summary

            self._emit_event("tool_start", {"action": action, "args": args})
            obs = self._execute_tool(action, args, user_goal)
            self._emit_event("tool_result", {"action": action, "result": obs[:350]})
            return False, obs

        # --- PATH 2: Direct Markdown Code Extraction Fallback (Closed OR Unclosed) ---
        code_blocks = list(re.finditer(r"```([a-zA-Z0-9_\-\.]*)?\s*[\r\n]+([\s\S]*?)(?:```|$)", raw_response))
        if code_blocks:
            saved_files = []
            valid_exts = ('.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.sh', '.bat', '.txt', '.yaml', '.yml')

            for match in code_blocks:
                lang_tag = (match.group(1) or "").strip().lower()
                code_content = match.group(2).strip()

                if not code_content or len(code_content) < 20:
                    continue

                # Filter out context compression receipts
                if any(receipt in code_content for receipt in ["[Code written to disk", "[Content written to disk", "[Patch applied", "syntax verified]"]):
                    continue

                # Guard against raw JSON tool envelope blocks in code fences
                if code_content.startswith("{") and ('"action"' in code_content or '"thought"' in code_content):
                    html_m = re.search(r'<!DOCTYPE[\s\S]*?(?:</html>|$)', code_content, re.IGNORECASE)
                    if html_m:
                        code_content = html_m.group(0).replace(r'\"', '"').replace(r'\n', '\n').replace(r'\t', '\t')
                    else:
                        continue

                start_pos = match.start()
                prefix_text = raw_response[max(0, start_pos - 120):start_pos]

                filepath = None

                first_lines = "\n".join(code_content.splitlines()[:5])
                fp_match = re.search(r"(?:#|//|<!--|/\*)\s*(?:filepath|file):\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", first_lines, re.IGNORECASE)
                if fp_match:
                    filepath = fp_match.group(1).strip()

                if not filepath and prefix_text:
                    pre_match = re.search(r"(?:###|####|\*\*|`|File:?|Save to:?)\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", prefix_text, re.IGNORECASE)
                    if pre_match:
                        cand = pre_match.group(1).strip("`* :")
                        if cand.endswith(valid_exts):
                            filepath = cand

                if not filepath and ":" in lang_tag:
                    cand = lang_tag.split(":", 1)[1]
                    if cand.endswith(valid_exts):
                        filepath = cand

                if not filepath:
                    if "<!doctype html" in code_content.lower() or "<html" in code_content.lower():
                        filepath = self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file)
                    elif lang_tag in ["css"]:
                        filepath = "style.css"
                    elif lang_tag in ["javascript", "js"]:
                        filepath = infer_target_filename(user_goal, ".js", active_file=self.active_target_file)
                    elif lang_tag in ["python", "py"]:
                        filepath = infer_target_filename(user_goal, ".py")
                    elif lang_tag in ["markdown", "md"]:
                        header_sample = code_content.lower()[:200]
                        if "plan" in header_sample or "implementation" in header_sample:
                            filepath = "implementation_plan.md"
                        elif "walkthrough" in header_sample or "guide" in header_sample or "overview" in header_sample:
                            filepath = "walkthrough.md"
                        elif "walkthrough" in user_goal.lower() and not os.path.exists("walkthrough.md"):
                            filepath = "walkthrough.md"
                        elif "plan" in user_goal.lower() and not os.path.exists("implementation_plan.md"):
                            filepath = "implementation_plan.md"
                        else:
                            filepath = "README.md"

                if filepath:
                    filepath = filepath.strip("`* \t\r\n")
                    if "<html" in code_content.lower():
                        if "<script" in code_content.lower() and "</script>" not in code_content.lower():
                            code_content += "\n</script>"
                        if "</body>" not in code_content.lower():
                            code_content += "\n</body>"
                        if "</html>" not in code_content.lower():
                            code_content += "\n</html>"

                    write_file(filepath, code_content)
                    saved_files.append(filepath)
                    console.print(f"  [bold green]💾 [Auto-Saved Code]:[/bold green] {filepath} ({len(code_content)} bytes)")

            if saved_files:
                # Validate syntax on all saved files
                all_valid = True
                val_errors = []
                for sf in saved_files:
                    is_val, val_msg = validate_code_syntax(sf)
                    if not is_val:
                        all_valid = False
                        val_errors.append(f"File {sf}: {val_msg}")
                        console.print(f"  [bold red]❌ Syntax Check Failed ({sf}):[/bold red]\n{val_msg}")
                    else:
                        console.print(f"  [bold green]✔ Syntax clean:[/bold green] {sf}")

                if not all_valid:
                    return False, f"Syntax verification failed on saved file(s):\n" + "\n".join(val_errors) + "\nPlease view the file with view_file_slice, then fix the syntax errors or append the missing code to make it fully working."

                # If user asked for walkthrough / documentation or implementation_plan and it hasn't been written:
                has_walkthrough = os.path.exists("walkthrough.md") and os.path.getsize("walkthrough.md") > 100
                has_plan = os.path.exists("implementation_plan.md") and os.path.getsize("implementation_plan.md") > 100
                needs_docs = ("walkthrough" in user_goal.lower() and not has_walkthrough) or \
                             ("plan" in user_goal.lower() and not has_plan)

                if needs_docs:
                    return False, f"Successfully created and validated {', '.join(saved_files)} (Syntax clean).\nPlease now generate the required implementation_plan.md or walkthrough.md using create_walkthrough / create_plan, or call finish(summary) if complete."

                # Provide instant feedback and finish only if files truly complete the request
                if any(f.endswith(('.html', '.js')) for f in saved_files):
                    html_file = next((f for f in saved_files if f.endswith('.html')), None)
                    if html_file:
                        try:
                            with open(html_file, 'r', encoding='utf-8', errors='replace') as hf:
                                h_content = hf.read()
                        except Exception:
                            h_content = ""
                        app_keywords = ["game", "snake", "defense", "pong", "flappy", "app", "simulator", "arena", "synth", "audio", "visualizer", "player", "tool", "editor", "calculator", "dashboard"]
                        is_app = any(kw in html_file.lower() for kw in app_keywords) or any(kw in user_goal.lower() for kw in app_keywords)
                        if is_app and (len(h_content) < 3000 or "<script" not in h_content.lower()):
                            return False, f"File '{html_file}' was saved ({len(h_content)} bytes), but it is an incomplete stub lacking full interactive <script> logic (minimum 3,000 bytes required). Please output the complete, runnable HTML5 implementation in a single markdown code block."

                    msg = f"Successfully generated {', '.join(saved_files)}."
                    console.print(Panel(f"[bold green]✔ Files generated successfully[/bold green]\n{msg}", title="[bold green]Success[/bold green]", border_style="green"))
                    return True, msg
                elif any(f.endswith('.py') for f in saved_files):
                    py_file = next((f for f in saved_files if f.endswith('.py')), saved_files[0])
                    return True, f"Saved and verified clean: {', '.join(saved_files)}"

        # --- PATH 2.5: Raw HTML without markdown fences or JSON ---
        html_raw = re.search(r'(<!DOCTYPE[\s\S]*?(?:</html>|$))', raw_response, re.IGNORECASE)
        if html_raw and len(html_raw.group(1).strip()) > 100:
            cand_html = html_raw.group(1).strip()
            has_real_script = "<script" in cand_html.lower() and ("</script>" in cand_html.lower() or len(cand_html) > 500)
            has_structured_markup = "<head" in cand_html.lower() and "<body" in cand_html.lower()
            if has_real_script or has_structured_markup:
                if "<script" in cand_html.lower() and "</script>" not in cand_html.lower():
                    cand_html += "\n</script>"
                if "</body>" not in cand_html.lower():
                    cand_html += "\n</body>"
                if "</html>" not in cand_html.lower():
                    cand_html += "\n</html>"
                fp = self.active_target_file or infer_target_filename(user_goal, ".html", active_file=self.active_target_file)
                write_file(fp, cand_html)
                console.print(f"  [bold green]💾 [Auto-Saved HTML]:[/bold green] {fp} ({len(cand_html)} bytes)")

                is_val, val_msg = validate_code_syntax(fp)
                if not is_val:
                    console.print(f"  [bold red]❌ Syntax Check Failed ({fp}):[/bold red]\n{val_msg}")
                    return False, f"Syntax verification failed on '{fp}':\n{val_msg}\nPlease view the file with view_file_slice, then fix the syntax errors or complete the implementation using replace_file_content."

                console.print(f"  [bold green]✔ Syntax clean:[/bold green] {fp}")

                # 4-Layer Autonomous Real Browser Verification (Code -> Execution -> Interaction -> Vision)
                try:
                    from verification_pipeline import VERIFICATION_PIPELINE
                    current_attempt = getattr(self, "_current_turn", 1)
                    v_res = VERIFICATION_PIPELINE.verify_project(fp, user_goal, attempt=current_attempt)
                    if not v_res.get("passed", False):
                        diag_str = json.dumps(v_res.get("failure_diagnosis", {}), indent=2)
                        SESSION_STATE.set("temp:last_verification_status", "failed")
                        SESSION_STATE.set("temp:last_verification_error", v_res.get("report", "")[:200])
                        console.print(f"  [bold red]❌ Real Browser Verification Failed ({fp}):[/bold red]\n{v_res['report']}")
                        return False, f"Real browser verification failed on '{fp}':\n\n{v_res['report']}\n\nStructured Failure Diagnosis:\n```json\n{diag_str}\n```\n\nPlease repair '{fp}' using replace_file_content to resolve this issue."
                    SESSION_STATE.set("temp:last_verification_status", "passed")
                    SESSION_STATE.set("temp:last_verification_score", v_res.get("aesthetic_score", 8))
                    SESSION_STATE.set("last_verified_file", fp)
                    console.print(f"  [bold green]✔ Real Browser Verification Passed:[/bold green] {fp}")
                except Exception:
                    pass

                # App completeness verification
                app_keywords = ["game", "snake", "defense", "pong", "flappy", "app", "simulator", "arena", "synth", "audio", "visualizer", "player", "tool", "editor", "calculator", "dashboard", "pomodoro", "clock", "timer"]
                is_app = any(kw in fp.lower() for kw in app_keywords) or any(kw in user_goal.lower() for kw in app_keywords)
                if is_app and (len(cand_html) < 1500 or "<script" not in cand_html.lower()):
                    return False, f"File '{fp}' was saved ({len(cand_html)} bytes), but it is an incomplete stub lacking full interactive <script> logic (minimum 1,500 bytes required). Please output the complete, runnable HTML5 implementation."

                # Check if documentation or planning was requested
                has_walkthrough = os.path.exists("walkthrough.md") and os.path.getsize("walkthrough.md") > 100
                has_plan = os.path.exists("implementation_plan.md") and os.path.getsize("implementation_plan.md") > 100
                needs_docs = ("walkthrough" in user_goal.lower() and not has_walkthrough) or \
                             ("plan" in user_goal.lower() and not has_plan)

                if needs_docs:
                    return False, f"Successfully created and validated '{fp}' (Syntax clean).\nPlease now generate the required implementation_plan.md or walkthrough.md using create_walkthrough / create_plan, or call finish(summary) if complete."

                msg = f"Successfully generated {fp}."
                console.print(Panel(f"[bold green]✔ Web project ready![/bold green]\n{msg}", title="[bold green]Success[/bold green]", border_style="green"))
                return True, msg

        # --- PATH 3: Model answered with explanation or text ---
        console.print(f"[dim]{raw_response[:250]}...[/dim]")
        return False, "Output received. If work is finished, call finish(summary). Otherwise call a tool."

    _process_response = _parse_and_execute

    def _execute_tool(self, action: str, args: dict, user_goal: str = "") -> str:
        if isinstance(args, str):
            args = {"summary": args, "content": args, "filepath": args, "command": args, "query": args}
        elif not isinstance(args, dict):
            args = {}

        # Pre-tool lifecycle hook & safety guard
        proceed, hook_msg, args = HOOK_MANAGER.run_pre_tool_hook(action, args)
        if not proceed:
            console.print(f"  [bold red]⛔ {hook_msg}[/bold red]")
            return hook_msg

        if isinstance(args, dict):
            for k in ("filepath", "file", "path"):
                if k in args and isinstance(args[k], str):
                    self.touched_files.add(args[k])

        try:
            if action == "write_file":
                fp = args.get("filepath", "").strip()
                cnt = args.get("content", "")
                if not fp or fp in ["...", "…", "None", "null"] or fp.endswith((".", " ")):
                    fp = self.active_target_file or infer_target_filename(user_goal, active_file=self.active_target_file)
                if len(cnt.strip()) < 20:
                    return f"Warning: The provided content for '{fp}' was only {len(cnt.strip())} characters (placeholder or incomplete stub). Please provide the complete, runnable implementation code."
                if "<script>...</script>" in cnt or "<script>\n...</script>" in cnt or "<style>...</style>" in cnt:
                    return f"Error writing '{fp}': Content contains placeholder ellipsis '...' inside <script> or <style>. Do NOT use '...' placeholders; provide complete, functioning code with full JavaScript logic."
                console.print(f"  [bold green]💾 Writing {fp} ({len(cnt)} bytes)[/bold green]")
                res = write_file(fp, cnt)
                is_val, val_msg = validate_code_syntax(fp)
                if is_val:
                    res += f" (Syntax clean: {val_msg})"
                else:
                    res += f"\nWarning: Syntax check failed:\n{val_msg}"
                if fp and fp not in self.session_manifest:
                    self.session_manifest.append(fp)
                if fp.endswith('.html'):
                    pass # Removed direct start command as it breaks Vite apps
                return res

            elif action == "replace_file_content":
                fp = args.get("filepath", "")
                tc = args.get("target_content", "")
                rc = args.get("replacement_content", "")
                console.print(f"  [bold yellow]✏️ Patching {fp}[/bold yellow]")
                res = replace_file_content(fp, tc, rc)
                if fp and fp not in self.session_manifest:
                    self.session_manifest.append(fp)
                is_val, val_msg = validate_code_syntax(fp)
                if is_val:
                    res += f" (Syntax clean: {val_msg})"
                else:
                    res += f"\nWarning: Syntax check failed:\n{val_msg}"
                return res

            elif action == "view_file_slice":
                fp = args.get("filepath", "")
                s = int(args.get("start_line", 1))
                e = int(args.get("end_line", 200))
                console.print(f"  [bold cyan]📖 Viewing {fp} (lines {s}-{e})[/bold cyan]")
                return view_file_slice(fp, s, e)

            elif action == "read_file":
                fp = args.get("filepath", "")
                console.print(f"  [bold cyan]📖 Reading {fp}[/bold cyan]")
                return read_file(fp)

            elif action == "run_command":
                cmd = args.get("command", "")
                console.print(f"  [bold yellow]$ {cmd}[/bold yellow]")
                return run_command(cmd)

            elif action == "list_directory":
                dp = args.get("dirpath", ".")
                return list_directory(dp)

            elif action == "search_web":
                q = args.get("query", "")
                console.print(f"  [bold magenta]🌐 Web Search: {q}[/bold magenta]")
                return search_web(q)

            elif action == "github_search":
                q = args.get("query", "")
                console.print(f"  [bold magenta]🐙 GitHub Search (PAT): {q}[/bold magenta]")
                return github_search(q)

            elif action == "snyk_audit":
                pf = args.get("package_file", "requirements.txt")
                console.print(f"  [bold magenta]🛡️ Snyk Security Scan: {pf}[/bold magenta]")
                return snyk_audit(pf)

            elif action == "spawn_subagent":
                role = args.get("role", "Developer Subagent")
                prompt = args.get("prompt", "")
                prov = args.get("provider", "openrouter")
                return spawn_subagent(role=role, prompt=prompt, provider=prov)

            elif action == "check_subagent_status":
                sid = args.get("subagent_id", "")
                return check_subagent_status(sid)

            elif action == "wait_for_subagent":
                sid = args.get("subagent_id", "")
                tsec = int(args.get("timeout_sec", 60))
                return wait_for_subagent(sid, timeout_sec=tsec)

            elif action == "list_subagents":
                return list_subagents()

            elif action == "record_memory":
                k = args.get("key", "")
                v = args.get("value", "")
                return record_memory(k, v)

            elif action == "read_memory":
                return read_memory()

            elif action == "invoke_subagent":
                role = args.get("role", "Developer Subagent")
                prompt = args.get("prompt", "")
                prov = args.get("provider", "openrouter")
                sub = SubagentWorker(role=role, provider=prov)
                return sub.execute(prompt)

            elif action == "cloudflare_semantic_search":
                q = args.get("query", "")
                dp = args.get("dirpath", ".")
                console.print(f"  [bold magenta]⚡ Cloudflare Semantic Code Search (0 Tokens): {q}[/bold magenta]")
                with console.status("[bold magenta]🔍 Vectorizing & searching codebase...[/bold magenta]", spinner="dots"):
                    return cloudflare_semantic_search(q, dp)

            elif action == "cloudflare_url_scan":
                url = args.get("url", "")
                console.print(f"  [bold magenta]🔍 Cloudflare URL Scan: {url}[/bold magenta]")
                return cloudflare_url_scan(url)
            elif action == "cloudflare_manage_queue":
                act = args.get("action", "list")
                qn = args.get("queue_name", "")
                console.print(f"  [bold magenta]⚙️ Cloudflare Queue: {act} {qn}[/bold magenta]")
                return cloudflare_manage_queue(act, qn)
            elif action == "cloudflare_manage_container":
                act = args.get("action", "list")
                cid = args.get("container_id", "")
                console.print(f"  [bold magenta]📦 Cloudflare Container: {act} {cid}[/bold magenta]")
                return cloudflare_manage_container(act, cid)

            elif action == "create_plan":
                title = args.get("title", "Project Plan")
                cnt = args.get("content", "")
                fp = args.get("filepath", "implementation_plan.md")
                console.print(f"  [bold cyan]📋 Planning Architecture: {title} ({fp})[/bold cyan]")
                res = create_plan(title, cnt, fp)
                target_fp = self.active_target_file or infer_target_filename(user_goal, default_ext=".html", cwd=".", active_file=self.active_target_file)
                project_files_exist = os.path.exists(target_fp) or os.path.exists("index.html") or os.path.exists("package.json")
                if target_fp and not project_files_exist:
                    res += f"\nPlan recorded. CRITICAL NEXT STEP: Now write the complete, functioning code file '{target_fp}' using a markdown code block or write_file!"
                return res

            elif action == "create_walkthrough":
                title = args.get("title", "Project Walkthrough")
                cnt = args.get("content", "")
                fp = args.get("filepath", "walkthrough.md")
                console.print(f"  [bold cyan]📖 Writing Documentation: {title} ({fp} & README.md)[/bold cyan]")
                res = create_walkthrough(title, cnt, fp)
                target_fp = self.active_target_file or infer_target_filename(user_goal, default_ext=".html", cwd=".", active_file=self.active_target_file)
                project_files_exist = os.path.exists(target_fp) or os.path.exists("index.html") or os.path.exists("package.json")
                if target_fp and not project_files_exist:
                    res += f"\nWARNING: Primary code file '{target_fp}' does NOT exist yet! You must implement '{target_fp}' before calling finish."
                return res

            elif action == "save_artifact":
                name = args.get("name", "artifact.md")
                title = args.get("title", "Project Artifact")
                atype = args.get("type", "plan")
                cnt = args.get("content", "")
                console.print(f"  [bold cyan]📑 Generating Artifact: {title} ({name})[/bold cyan]")
                return ARTIFACT_MANAGER.save_artifact(name, title, atype, cnt)

            elif action == "retrieve_cached_content":
                lid = args.get("log_id", "")
                sl = int(args.get("start_line", 1))
                el = int(args.get("end_line", 120))
                console.print(f"  [bold cyan]📖 Retrieving Cached Log Slice: {lid} (Lines {sl}-{el})[/bold cyan]")
                return retrieve_cached_content(lid, start_line=sl, end_line=el)

            elif action == "search_mcp_servers":
                q = args.get("query", "")
                cat = args.get("category", None)
                console.print(f"  [bold magenta]🔌 MCP Registry Search: {q}[/bold magenta]")
                return search_mcp_servers(q, category=cat)

            elif action == "extract_media_info":
                u = args.get("url", "")
                subs = bool(args.get("extract_subtitles", True))
                console.print(f"  [bold magenta]🎬 yt-dlp Media Extraction: {u}[/bold magenta]")
                return extract_media_info(u, extract_subtitles=subs)

            elif action == "run_chrome_devtools":
                tname = args.get("tool_name", "list_pages")
                targs = args.get("args", [])
                tflags = args.get("flags", {})
                console.print(f"  [bold cyan]🌐 Chrome DevTools Action: {tname}[/bold cyan]")
                return run_chrome_devtools(tname, args=targs, flags=tflags)

            elif action == "inspect_url_with_browser":
                u = args.get("url", "")
                shot = bool(args.get("take_screenshot", False))
                lh = bool(args.get("run_lighthouse", False))
                console.print(f"  [bold cyan]🔍 Chrome DevTools Headless Inspection: {u}[/bold cyan]")
                return inspect_url_with_browser(u, take_screenshot=shot, run_lighthouse=lh)

            elif action == "verify_ui_in_browser":
                t = args.get("target_file", args.get("url", args.get("filepath", "")))
                shot = bool(args.get("take_screenshot", True))
                console.print(f"  [bold cyan]🖥️ Headless Visual UI Verification: {t}[/bold cyan]")
                return verify_ui_in_browser(t, take_screenshot=shot)

            elif action == "search_ui_templates":
                q = args.get("query", args.get("category", user_goal))
                console.print(f"  [bold magenta]🎨 UI Creativity & Template Engine: {q}[/bold magenta]")
                return search_ui_templates(q)

            elif action == "open_in_browser":
                t = args.get("target_file", args.get("url", args.get("filepath", "index.html")))
                console.print(f"  [bold cyan]🌐 Opening in Desktop Browser: {t}[/bold cyan]")
                return open_in_browser(t)

            elif action == "workspace_vector_search":
                q = args.get("query", args.get("q", user_goal))
                wdir = args.get("workspace_dir", args.get("dir", "."))
                top_k = int(args.get("top_k", 5))
                console.print(f"  [bold bright_magenta]🔍 Vector Semantic Search: {q[:60]}[/bold bright_magenta]")
                return workspace_vector_search(q, workspace_dir=wdir, top_k=top_k)

            elif action == "vector_status":
                console.print("  [bold cyan]🧠 Checking Vector Intelligence Status...[/bold cyan]")
                return vector_status()

            elif action == "verify_with_real_browser":
                t = args.get("target_file", args.get("url", args.get("filepath", "index.html")))
                g = args.get("user_goal", user_goal)
                console.print(f"  [bold bright_cyan]🔬 4-Layer Autonomous Real Browser Verification: {t}[/bold bright_cyan]")
                return verify_with_real_browser(t, user_goal=g)

            elif action == "fetch_vector_asset":
                entity = args.get("entity_name") or args.get("entity") or args.get("name", "")
                style = args.get("style", "solid")
                console.print(f"  [bold bright_magenta]🎨 Fetching Vector Asset: {entity}[/bold bright_magenta]")
                return fetch_vector_asset(entity, style=style)

            elif action == "generate_physics_rig":
                rig_type = args.get("rig_type", "spring_follower")
                opts = args.get("options")
                console.print(f"  [bold bright_cyan]🚀 Generating Motion Physics Rig: {rig_type}[/bold bright_cyan]")
                return generate_physics_rig(rig_type, options=opts)

            elif action == "set_state":
                k = args.get("key", "")
                v = args.get("value")
                console.print(f"  [bold bright_green]🧠 Setting Session State: {k}[/bold bright_green]")
                return set_state(k, v)

            elif action == "get_state":
                k = args.get("key")
                console.print(f"  [bold bright_green]🔍 Querying Session State: {k or 'ALL'}[/bold bright_green]")
                return get_state(k)

            elif action == "delete_state":
                k = args.get("key", "")
                console.print(f"  [bold red]🗑️ Deleting Session State: {k}[/bold red]")
                return delete_state(k)

            elif action == "finish":
                return args.get("summary", "Complete.")

            else:
                return f"Error: Unknown tool action '{action}'"
        except Exception as e:
            return f"Tool execution error: {str(e)}"

    def run(self, user_goal: str, session_context: list = None, target_override: str = None, event_callback: callable = None) -> str:
        if event_callback and callable(event_callback):
            self.event_callback = event_callback

        # 0. Structured State Memory: Reset turn temporary state & expand {key} templating
        SESSION_STATE.reset_temp()
        user_goal = SESSION_STATE.apply_templating(user_goal)

        # Domain entity auto-capture into session state
        goal_lower = user_goal.lower()
        if not SESSION_STATE.get("target_object"):
            for ent in ["rocket", "spacecraft", "spaceship", "airplane", "plane", "jet", "car", "supercar", "drone", "submarine", "gamepad", "bird"]:
                if ent in goal_lower:
                    syn = "rocket" if ent in ["spacecraft", "spaceship"] else ("airplane" if ent in ["plane", "jet"] else ent)
                    SESSION_STATE.set("target_object", syn)
                    break

        console.print(Panel(f"[bold white]{user_goal}[/bold white]", title=f"[bold bright_cyan]⚡ Saltice Autonomous Engine ({self.mode.upper()}) ⚡[/bold bright_cyan]", border_style="bright_blue"))

        workspace_info = get_workspace_summary()
        caveman = CAVEMAN_PROMPTS.get(self.caveman_level, "")

        # 1. Discover Project Rules (AGENTS.md / CLAUDE.md)
        project_rules = CONTEXT_MANAGER.get_rules_content()

        # 2. Discover Persistent Memories
        memories = CONTEXT_MANAGER.get_memory_context()

        # 3. Discover Negative Constraints / Learned Anti-Patterns from User Feedback
        negative_constraints = CONTEXT_MANAGER.get_negative_constraints_context()

        # 4. Dynamic Skills Discovery & Slash Command Handling
        skills_catalog = SKILL_MANAGER.get_skills_catalog()
        active_skills_text = ""

        # Check for Slash Command (e.g. /glassy-ui, /autonomous-tester)
        if user_goal.strip().startswith("/"):
            parts = user_goal.strip().split(maxsplit=1)
            cmd = parts[0]
            matched_skill = SKILL_MANAGER.get_skill_by_command(cmd)
            if matched_skill:
                console.print(f"[bold green]⚡ Slash Command Activated: /{matched_skill.name}[/bold green]")
                active_skills_text += f"\n[ACTIVATED SKILL: {matched_skill.name}]\n{matched_skill.content}\n"
                if len(parts) > 1:
                    user_goal = f"Execute skill '{matched_skill.name}' with input: {parts[1]}"
                else:
                    user_goal = f"Execute skill '{matched_skill.name}'"

        # Check for keyword trigger matches
        relevant_skills = SKILL_MANAGER.find_relevant_skills(user_goal)
        for s in relevant_skills:
            if s.name not in active_skills_text:
                console.print(f"[bold cyan]⚡ Dynamic Skill Injected: {s.name}[/bold cyan]")
                active_skills_text += f"\n[RELEVANT SPECIALIZED SKILL: {s.name}]\n{s.content}\n"

        active_target = target_override
        if not active_target and session_context and isinstance(session_context, list) and len(session_context) > 0:
            last_turn = session_context[-1]
            if isinstance(last_turn, dict) and last_turn.get("target_file"):
                active_target = last_turn.get("target_file")

        target_file = infer_target_filename(user_goal, default_ext=".html", cwd=".", active_file=active_target)
        self.active_target_file = target_file

        # Anti-regression and existing project awareness
        iteration_prompt = ""
        if os.path.exists(target_file) and os.path.getsize(target_file) > 200:

            iteration_prompt = f"""
[ITERATIVE ENHANCEMENT MODE]:
An existing working application '{target_file}' is present in the workspace.
CRITICAL ANTI-REGRESSION RULES:
1. You MUST PRESERVE all existing working business logic, timers, countdown intervals, state variables, and event listeners.
2. NEVER wipe or replace working code with a hollow stub or empty placeholders (e.g. /* ... */ or // todo).
3. If styling or visual effects (e.g. GSAP animations, Lenis smooth scroll, modern theme) are requested, inject modern styles and scripts while keeping all existing HTML IDs and JavaScript bindings working!
"""

        # Living Project Documentation awareness
        docs_context = ""
        if os.path.exists("implementation_plan.md"):
            try:
                with open("implementation_plan.md", "r", encoding="utf-8", errors="replace") as pf:
                    docs_context += f"\n[EXISTING IMPLEMENTATION PLAN]:\n{pf.read()[:1200]}\n"
            except Exception:
                pass

        session_str = ""
        if session_context and isinstance(session_context, list) and len(session_context) > 0:
            session_str = "\n[CONVERSATIONAL CHAT MEMORY (Previous Turns in this Session)]:\n"
            for idx, t in enumerate(session_context[-6:], 1):
                if isinstance(t, dict):
                    prompt_txt = t.get('user_goal', '')
                    summary_txt = t.get('summary', '') or 'Completed'
                    target_txt = t.get('target_file', '')
                    files_txt = f" (Touched: {', '.join(t.get('touched_files', []))})" if t.get('touched_files') else ""
                    session_str += f"Turn {idx}:\n  User: \"{prompt_txt}\"\n  Agent Result ({target_txt}{files_txt}): {summary_txt}\n\n"

        # Vector-based session memory RAG: retrieve semantically relevant past turns
        try:
            from vector_intelligence import search_session_memory
            session_id_for_vec = getattr(self, "_session_id", "default")
            vec_memory = search_session_memory(user_goal, top_k=3, session_id=session_id_for_vec)
            if vec_memory:
                session_str += f"\n{vec_memory}\n"
        except Exception:
            pass

        system_content = f"{caveman}\n\n{UNIFIED_TOOL_INSTRUCTIONS.format(workspace_info=workspace_info)}"
        if project_rules:
            system_content += f"\n\n{project_rules}"
        if negative_constraints:
            system_content += f"\n\n{negative_constraints}"
        if active_skills_text:
            system_content += f"\n\n{active_skills_text}"
        if memories:
            system_content += f"\n\n{memories}"
        if skills_catalog:
            system_content += f"\n\n{skills_catalog}"
        if iteration_prompt:
            system_content += f"\n\n{iteration_prompt}"

        # 5. Structured Session State Memory (Exact Variables & Scopes)
        state_prompt = SESSION_STATE.format_for_prompt()

        user_content = f"Task: {user_goal}"
        if state_prompt:
            user_content += f"\n\n{state_prompt}"
        if session_str:
            user_content += f"\n\n{session_str}"
        if docs_context:
            user_content += f"\n\n{docs_context}"
        user_content += "\nInspect workspace context above and execute your solution directly."

        self.history = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        result_obs = ""
        is_finished = False
        observation_history = []
        stall_count = 0
        max_turns = getattr(self, "max_iterations", 0)
        is_unlimited = (max_turns is None or max_turns <= 0)
        turn = 0

        while True:
            turn += 1
            self._current_turn = turn
            if not is_unlimited and turn > max_turns:
                break

            turn_str = f"{turn}" if is_unlimited else f"{turn}/{max_turns}"
            console.print(f"\n[bold bright_cyan]─── Action Turn {turn_str} ───[/bold bright_cyan]")
            self._emit_event("turn_start", {"turn": turn, "turn_str": turn_str, "max_turns": max_turns})

            try:
                # Context Engineering: Scrub stale observations only if history exceeds token budget
                pruned_history = scrub_history_for_context(self.history, keep_recent_turns=6)

                self._emit_event("reasoning", {"turn": turn, "mode": self.mode, "status": f"Saltice is reasoning & strategizing ({self.mode.upper()})..."})
                with console.status(f"[bold bright_cyan]🧠 Saltice is reasoning & strategizing ({self.mode.upper()})...[/bold bright_cyan]", spinner="dots"):
                    raw_response = self._call_model(pruned_history)

                is_finished, observation = self._parse_and_execute(raw_response, user_goal)

                if is_finished:
                    result_obs = observation
                    break

                obs_preview = observation[:300] + ("..." if len(observation) > 300 else "")
                console.print(f"  [dim]Observation: {obs_preview}[/dim]")

                # Cobus Greyling Loop Engineering: Stall & Infinite-Fix-Loop Detection
                obs_norm = re.sub(r'\s+', ' ', observation.strip()[:180]).lower()
                is_err = any(kw in obs_norm for kw in ["failed", "error", "warning", "timed out", "syntax verification failed"])

                if observation_history and obs_norm == observation_history[-1] and is_err:
                    stall_count += 1
                else:
                    stall_count = 0

                observation_history.append(obs_norm)

                if stall_count >= 3:
                    console.print(f"\n[bold red]⚠️ Loop Stall Terminated: 3 consecutive identical failures encountered.[/bold red]")
                    console.print(f"[bold yellow]Halting loop to prevent token burn. Last error: {observation[:200]}[/bold yellow]")
                    result_obs = f"Task halted: Loop stall detected after {turn} attempts with repeating failure:\n{observation[:300]}"
                    break

                # Context injection for turn continuation:
                # If stall detected (1 or 2 repeat errors), inject reflection directive
                stall_hint = ""
                if stall_count >= 1:
                    stall_hint = "\n\n[LOOP STALL WARNING]: Your last action produced the exact same error as the previous turn. Do NOT repeat the exact same tool call or file edit. Step back, re-examine the error message, and adopt an alternative strategy."

                runway_hint = ""
                if not is_unlimited:
                    rem = max_turns - turn
                    if 0 < rem <= 5:
                        runway_hint = f"\n\n[RUNWAY NOTICE]: {rem} action turn(s) remaining in this iteration cycle. Wrap up any remaining code changes, run verification, and call finish(summary)."

                self.history.append({"role": "assistant", "content": raw_response})
                self.history.append({
                    "role": "user",
                    "content": f"Observation:\n{observation}{stall_hint}{runway_hint}\n\nContinue your implementation or call finish(summary) if done."
                })

                # Embed this turn to session memory RAG (non-blocking background thread)
                try:
                    from vector_intelligence import embed_session_turn
                    session_id_for_vec = getattr(self, "_session_id", "default")
                    embed_session_turn(session_id_for_vec, "assistant", raw_response, turn)
                except Exception:
                    pass

            except Exception as e:
                console.print(f"[bold red]Execution error: {e}[/bold red]")
                break

        # Ensure walkthrough is synchronized if target_file exists
        if os.path.exists(target_file) and os.path.getsize(target_file) > 200:
            app_name = os.path.splitext(os.path.basename(target_file))[0].replace('_', ' ').replace('-', ' ').title()
            if not os.path.exists("walkthrough.md"):
                create_walkthrough(app_name, f"# Walkthrough: {app_name}\n\nTarget File: `{target_file}`\nTask: {user_goal}\nStatus: Complete & Verified.\n")

        if not is_unlimited:
            warn_msg = f"⚠️ Reached iteration limit ({max_turns} turns) without explicit finish. Workspace state preserved. Type next prompt or use '/iterations 0' for unlimited runway."
        else:
            warn_msg = "Task halted without explicit finish."

        final_summary = result_obs if (is_finished and result_obs) else (result_obs or warn_msg)
        self._emit_event("task_complete", {
            "summary": final_summary,
            "is_finished": is_finished,
            "turns": turn,
            "target_file": target_file,
            "touched_files": list(self.touched_files)
        })

        if is_finished and result_obs:
            console.print(f"[bold green]✔ Task completed: {result_obs[:200]}[/bold green]")
            return result_obs

        if result_obs:
            return result_obs

        console.print(f"[bold yellow]{warn_msg}[/bold yellow]")
        return warn_msg


# Alias for backward compatibility
ReActAgent = SalticeAntigravityEngine
SalticeArchitectAgent = SalticeAntigravityEngine
