"""
Asynchronous Subagent Manager for Saltice
Inspired by Grok Build, Claude Code, and Antigravity parallel execution architectures.

Features:
- Spawns subagents in isolated background threads
- Tracks status (PENDING, RUNNING, COMPLETED, FAILED)
- Full result capture, logging, and metrics
- Tools for main agent:
  - spawn_subagent(role, prompt, provider) -> returns subagent_id
  - check_subagent_status(subagent_id) -> returns status, progress or output
  - list_subagents() -> returns table of active/completed subagents
  - wait_for_subagent(subagent_id, timeout_sec) -> blocks until finished or timeout
  - invoke_subagent(role, prompt, provider) -> synchronous execution wrapper
"""

import sys
import time
import uuid
import threading
import json
import re
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

class SubagentTask:
    def __init__(self, task_id: str, role: str, prompt: str, provider: str = "openrouter"):
        self.task_id = task_id
        self.role = role
        self.prompt = prompt
        self.provider = provider
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.actions_taken: list = []
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None

    def to_dict(self) -> Dict[str, Any]:
        duration = None
        if self.started_at:
            end_t = self.finished_at or time.time()
            duration = round(end_t - self.started_at, 2)
        return {
            "subagent_id": self.task_id,
            "role": self.role,
            "provider": self.provider,
            "status": self.status,
            "created_at": self.created_at,
            "duration_sec": duration,
            "actions_count": len(self.actions_taken),
            "result_preview": (self.result[:200] + "...") if self.result else None,
            "error": self.error
        }


# Pre-configured specialized subagent personas inspired by ECC (Everything Claude Code)
ECC_SPECIALIZED_ROLES = {
    "planner": "Implementation planning specialist: decomposes complex goals into granular, testable steps with verification gates.",
    "architect": "System design and scalability architect: designs high-cohesion, low-coupling components and clean module boundaries.",
    "tdd-guide": "Test-Driven Development guide: defines tests first (unit, integration) and verifies implementations with strict coverage.",
    "code-reviewer": "Code quality & anti-regression reviewer: audits logic, edge cases, readability, and performance before completion.",
    "security-reviewer": "Security specialist: audits OWASP vulnerabilities, prevents secret leaks, and checks input validation/sanitization.",
    "build-error-resolver": "Build & syntax repair specialist: quickly diagnoses and resolves compilation, type, and lint failures.",
    "doc-updater": "Documentation specialist: synchronizes implementation plans, walkthroughs, and READMEs.",
    "academic-researcher": "Academic research specialist: literature synthesis, citation verification, and rigorous methodology review.",
    "karpathy-auditor": "Karpathy guidelines auditor: enforces simplicity, prevents speculative over-engineering, and ensures surgical edits.",
    "browser-agent": "Chrome DevTools browser automation & debugging agent: navigates pages, inspects DOM/accessibility, captures screenshots, evaluates client-side JavaScript, and runs Lighthouse audits via Chrome DevTools MCP.",
    "image-agent": "Autonomous visual diffusion and vector graphic studio: generates hyper-realistic mockups, visual assets, 3D textured graphics, and vector logos using Cloudflare AI, HuggingFace ZeroGPU, and Gemini SVG synthesis.",
    "vector-designer": "Vector logo and SVG design specialist: synthesizes mathematical SVG brand marks, icons, and geometric vectors with gradient defs, filters, and lossless PNG rasterization."
}

class SubagentManager:
    def __init__(self):
        self._tasks: Dict[str, SubagentTask] = {}
        self._lock = threading.Lock()

    def spawn(self, role: str, prompt: str, provider: str = "openrouter") -> str:
        """Spawn a subagent asynchronously in a background thread."""
        task_id = f"subagent-{uuid.uuid4().hex[:8]}"
        task = SubagentTask(task_id=task_id, role=role, prompt=prompt, provider=provider)

        with self._lock:
            self._tasks[task_id] = task

        thread = threading.Thread(target=self._run_subagent_worker, args=(task,), daemon=True)
        task._thread = thread
        thread.start()

        console.print(f"[bold magenta]🚀 [Subagent Manager] Spawned '{role}' ({task_id}) in background...[/bold magenta]")
        return json.dumps({
            "status": "spawned",
            "subagent_id": task_id,
            "role": role,
            "provider": provider,
            "message": f"Subagent {task_id} is running asynchronously. Use 'check_subagent_status(\"{task_id}\")' to inspect or 'wait_for_subagent(\"{task_id}\")' to retrieve result."
        }, indent=2)

    def check_status(self, subagent_id: str) -> str:
        """Check status and recent actions of a subagent."""
        if isinstance(subagent_id, str) and subagent_id.strip().startswith("{"):
            try:
                data = json.loads(subagent_id)
                if "subagent_id" in data:
                    subagent_id = data["subagent_id"]
            except Exception:
                pass

        with self._lock:
            task = self._tasks.get(subagent_id)

        if not task:
            return json.dumps({"error": f"Subagent ID '{subagent_id}' not found."}, indent=2)

        info = task.to_dict()
        if task.status == "COMPLETED":
            info["full_result"] = task.result
        elif task.status == "FAILED":
            info["error_details"] = task.error
        elif task.status == "RUNNING":
            info["recent_actions"] = task.actions_taken[-5:]

        return json.dumps(info, indent=2)

    def wait_for(self, subagent_id: str, timeout_sec: int = 60) -> str:
        """Wait synchronously up to timeout_sec for a subagent to finish."""
        if isinstance(subagent_id, str) and subagent_id.strip().startswith("{"):
            try:
                data = json.loads(subagent_id)
                if "subagent_id" in data:
                    subagent_id = data["subagent_id"]
            except Exception:
                pass

        with self._lock:
            task = self._tasks.get(subagent_id)

        if not task:
            return json.dumps({"error": f"Subagent ID '{subagent_id}' not found."}, indent=2)

        if task._thread and task._thread.is_alive():
            task._thread.join(timeout=timeout_sec)

        return self.check_status(subagent_id)

    def list_all(self) -> str:
        """Return a formatted status overview of all subagents."""
        with self._lock:
            tasks = list(self._tasks.values())

        if not tasks:
            return "No subagents have been spawned in this session."

        table = Table(title="Autonomous Subagents Status", border_style="magenta")
        table.add_column("Subagent ID", style="bold cyan")
        table.add_column("Role", style="yellow")
        table.add_column("Provider", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="white")
        table.add_column("Actions", style="green")

        for t in tasks:
            color = "green" if t.status == "COMPLETED" else "yellow" if t.status == "RUNNING" else "red"
            dur = f"{t.to_dict()['duration_sec']}s" if t.to_dict()['duration_sec'] else "-"
            table.add_row(t.task_id, t.role, t.provider, f"[{color}]{t.status}[/{color}]", dur, str(len(t.actions_taken)))

        console.print(table)
        return json.dumps([t.to_dict() for t in tasks], indent=2)

    def _run_subagent_worker(self, task: SubagentTask):
        """Internal worker routine executed in background thread."""
        task.started_at = time.time()
        task.status = "RUNNING"

        try:
            from tools import (
                run_command, read_file, write_file, search_web,
                get_workspace_summary, view_file_slice, replace_file_content,
                generate_image, generate_svg_logo
            )
            from providers import call_llm

            workspace = get_workspace_summary()

            role_desc = ECC_SPECIALIZED_ROLES.get(task.role.lower(), f"Specialized domain engineer for {task.role}")
            system_prompt = f"""You are an elite, specialized subagent working asynchronously for the primary Saltice agent.
Role: {task.role} ({role_desc})
Assigned Goal: {task.prompt}

CORE ENGINEERING PRINCIPLES (ECC & Karpathy Directives):
1. Think before coding: surface assumptions, tradeoffs, and edge cases.
2. Simplicity first: minimum clean code that solves the goal; no speculative abstractions.
3. Surgical changes: touch only what you must, match existing patterns.
4. Goal-driven execution: verify each step with non-blocking checks before calling finish.

WORKSPACE CONTEXT:
{workspace}

Available Tools:
1. `write_file(filepath, content)`: Create or overwrite a file.
2. `read_file(filepath)`: Read a file completely.
3. `view_file_slice(filepath, start_line, end_line)`: Read slice of file.
4. `replace_file_content(filepath, target_content, replacement_content)`: Patch file.
5. `run_command(command)`: Run non-blocking shell command (e.g. tests, lint). NEVER run blocking dev servers.
6. `search_web(query)`: Search online resources.
7. `generate_image(prompt, model, backend, wordmark, enhance, output_path)`: Generate diffusion image.
8. `generate_svg_logo(concept, output_path, style, rasterize_to_png)`: Generate vector SVG brand logo.
9. `finish(summary)`: Call when your assignment is complete.

RESPONSE FORMAT (JSON ONLY):
```json
{{
  "thought": "Your reasoning",
  "action": "write_file | read_file | run_command | search_web | finish",
  "args": {{ ... }}
}}
```"""

            history = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Begin assignment: {task.prompt}"}
            ]

            max_turns = 10
            for turn in range(1, max_turns + 1):
                res = call_llm(history, preferred_provider=task.provider, max_tokens=2500)
                raw = res.get("content", "").strip()

                json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
                json_str = json_match.group(1) if json_match else ""
                if not json_str:
                    brace = re.search(r"(\{[\s\S]*\})", raw)
                    json_str = brace.group(1) if brace else ""

                if not json_str:
                    # Fallback markdown block detection
                    code_matches = re.findall(r"```([a-zA-Z0-9_\-\.]*)?\s*[\r\n]+([\s\S]*?)```", raw)
                    if code_matches:
                        for ltag, cc in code_matches:
                            fname = "subagent_output.txt"
                            write_file(fname, cc.strip())
                            task.actions_taken.append(f"Wrote extracted code to {fname}")
                    task.actions_taken.append(f"Unstructured thought: {raw[:120]}")
                    task.result = raw
                    break

                try:
                    data = json.loads(json_str, strict=False)
                except Exception:
                    data = {}

                thought = data.get("thought", "")
                action = data.get("action", "")
                args = data.get("args", {})
                if isinstance(args, str):
                    args = {"content": args, "command": args, "query": args, "filepath": args, "summary": args}

                if action == "finish":
                    summary = args.get("summary", thought or "Assignment completed.")
                    task.actions_taken.append(f"Finished: {summary}")
                    task.result = summary
                    break

                obs = "Done"
                try:
                    if action == "write_file":
                        obs = write_file(args.get("filepath", ""), args.get("content", ""))
                    elif action == "read_file":
                        obs = read_file(args.get("filepath", ""))
                    elif action == "view_file_slice":
                        obs = view_file_slice(args.get("filepath", ""), int(args.get("start_line", 1)), int(args.get("end_line", 100)))
                    elif action == "replace_file_content":
                        obs = replace_file_content(args.get("filepath", ""), args.get("target_content", ""), args.get("replacement_content", ""))
                    elif action == "run_command":
                        obs = run_command(args.get("command", ""))
                    elif action == "search_web":
                        obs = search_web(args.get("query", ""))
                    elif action == "generate_image":
                        obs = generate_image(
                            args.get("prompt", ""),
                            model=args.get("model", "flux-schnell"),
                            backend=args.get("backend", "auto"),
                            wordmark=args.get("wordmark", ""),
                            enhance=args.get("enhance", True),
                            output_path=args.get("output_path", "")
                        )
                    elif action == "generate_svg_logo":
                        obs = generate_svg_logo(
                            args.get("concept", ""),
                            output_path=args.get("output_path", "artifacts/logo.svg"),
                            style=args.get("style", "modern-tech"),
                            rasterize_to_png=args.get("rasterize_to_png", True)
                        )
                    else:
                        obs = f"Unknown action '{action}'"
                except Exception as ex:
                    obs = f"Action error: {ex}"

                task.actions_taken.append(f"Action '{action}': {obs[:120]}")
                history.append({"role": "assistant", "content": json_str})
                history.append({"role": "user", "content": f"Observation: {obs}\nContinue or finish."})

            if not task.result:
                task.result = f"Completed {len(task.actions_taken)} actions for role '{task.role}'."

            task.status = "COMPLETED"

        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
            console.print(f"[bold red]❌ [Subagent {task.task_id}] Failed: {e}[/bold red]")
        finally:
            task.finished_at = time.time()
            console.print(f"[bold green]✔ [Subagent {task.task_id}] Finished ({round(task.finished_at - task.started_at, 2)}s)[/bold green]")

# Global singleton instance
SUBAGENT_MANAGER = SubagentManager()
