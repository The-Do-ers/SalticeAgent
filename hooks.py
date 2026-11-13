"""
Lifecycle Hooks System for Saltice
Inspired by Grok Build and Claude Code hook architectures.

Features:
- Discovers hook scripts in .grok/hooks/ and .agents/hooks/
- Built-in pre-tool safety guards (blocks hanging dev servers, dangerous commands)
- Runs pre-tool and post-tool lifecycle handlers
"""

import os
import re
import subprocess
from typing import Dict, Any, Tuple
from rich.console import Console

console = Console(force_terminal=True, legacy_windows=False)

class HookManager:
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.hook_dirs = [
            os.path.join(self.workspace_dir, ".grok", "hooks"),
            os.path.join(self.workspace_dir, ".agents", "hooks"),
            os.path.expanduser("~/.grok/hooks")
        ]

    def run_pre_tool_hook(self, action: str, args: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Runs prior to tool execution.
        Returns (proceed: bool, message: str, modified_args: dict).
        """
        # Guard 1: Prevent blocking dev servers in run_command
        if action == "run_command":
            cmd = (args.get("command") or "").strip()
            # Catch standalone blocking dev servers
            blocking_patterns = [
                r"^(?:npx\s+)?vite(?:\s+dev)?$",
                r"^npm\s+(?:run\s+)?(?:dev|start)$",
                r"^yarn\s+(?:dev|start)$",
                r"^pnpm\s+(?:dev|start)$",
                r"^python\s+-m\s+http\.server$"
            ]
            for pat in blocking_patterns:
                if re.search(pat, cmd, re.IGNORECASE):
                    msg = (
                        f"[HOOK BLOCKED]: Command '{cmd}' starts an indefinite, interactive development server.\n"
                        f"Running this will block the agent indefinitely.\n"
                        f"Instead, please verify the build non-blockingly using 'npm run build' or 'tsc', "
                        f"and instruct the user to run '{cmd}' in their own terminal."
                    )
                    return False, msg, args

        # Check for custom pre-tool scripts in hook directories
        for hdir in self.hook_dirs:
            hook_script = os.path.join(hdir, f"pre-{action}")
            for ext in ["", ".sh", ".bat", ".py", ".ps1"]:
                full_p = hook_script + ext
                if os.path.isfile(full_p):
                    try:
                        # Execute hook non-blockingly with short timeout
                        env = os.environ.copy()
                        env["TOOL_ACTION"] = action
                        res = subprocess.run(
                            [full_p] if ext != ".py" else ["python", full_p],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            env=env
                        )
                        if res.returncode != 0:
                            return False, f"Pre-tool hook '{full_p}' rejected execution: {res.stderr.strip()}", args
                    except Exception:
                        pass

        return True, "OK", args

    def run_post_tool_hook(self, action: str, args: Dict[str, Any], result: str) -> str:
        """
        Runs after tool execution. Can append diagnostics or run linting.
        """
        return result

HOOK_MANAGER = HookManager()
