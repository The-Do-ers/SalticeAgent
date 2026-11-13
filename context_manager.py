"""
Context and Rules Discovery Manager for Saltice
Inspired by Grok Build's AGENTS.md / rules discovery and Claude Code's CLAUDE.md conventions.

Features:
- Walks directory tree up from cwd to root to discover:
  - AGENTS.md, Agents.md, AGENT.md
  - CLAUDE.md, Claude.md, CLAUDE.local.md
  - .grok/rules/*.md, .claude/rules/*.md
- Persistent Memory Store:
  - Stores decisions and key facts in .grok/memory.json or .agents/memory.json
- Formats rules and active memories to inject directly into the system prompt.
"""

import os
import json
from typing import List, Dict, Optional, Any

class ContextManager:
    def __init__(self, start_dir: Optional[str] = None):
        self.start_dir = os.path.abspath(start_dir or os.getcwd())
        self.rules_files: List[str] = []
        self.memories: Dict[str, str] = {}
        self.anti_patterns: List[Dict[str, Any]] = []
        self.load_all()

    def load_all(self):
        self.rules_files = self.discover_rules_files()
        self.memories = self.load_memory()
        self.anti_patterns = self.load_anti_patterns()

    def discover_rules_files(self) -> List[str]:
        """Ascend from start_dir up to root finding all convention files."""
        found = []
        candidate_names = [
            "AGENTS.md", "Agents.md", "AGENT.md",
            "CLAUDE.md", "Claude.md", "CLAUDE.local.md"
        ]

        current = self.start_dir
        visited = set()

        while current and current not in visited:
            visited.add(current)

            # Check direct candidate files
            for name in candidate_names:
                p = os.path.join(current, name)
                if os.path.isfile(p) and p not in found:
                    found.append(p)

            # Check rule directories (.grok/rules, .claude/rules, .agents/rules)
            for rdir in [".grok/rules", ".claude/rules", ".agents/rules"]:
                rules_path = os.path.join(current, rdir)
                if os.path.isdir(rules_path):
                    try:
                        for rf in os.listdir(rules_path):
                            if rf.endswith(".md"):
                                full_rf = os.path.join(rules_path, rf)
                                if full_rf not in found:
                                    found.append(full_rf)
                    except Exception:
                        pass

            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        return found

    def get_rules_content(self, max_chars_per_file: int = 4000) -> str:
        """Combine all discovered rules into a consolidated context string."""
        if not self.rules_files:
            return ""

        sections = ["[PROJECT CONVENTIONS & RULES (Discovered from AGENTS.md / CLAUDE.md)]"]
        for rf in self.rules_files:
            try:
                with open(rf, "r", encoding="utf-8", errors="replace") as f:
                    cnt = f.read(max_chars_per_file).strip()
                rel_p = os.path.relpath(rf, self.start_dir)
                sections.append(f"--- Rule Source: {rel_p} ---\n{cnt}")
            except Exception:
                pass

        return "\n\n".join(sections)

    def _get_memory_filepath(self) -> str:
        # Check .grok dir or .agents dir in start_dir
        for d in [".grok", ".agents"]:
            dp = os.path.join(self.start_dir, d)
            if os.path.isdir(dp):
                return os.path.join(dp, "memory.json")
        return os.path.join(self.start_dir, ".agents", "memory.json")

    def load_memory(self) -> Dict[str, str]:
        mp = self._get_memory_filepath()
        if os.path.isfile(mp):
            try:
                with open(mp, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def record_memory(self, key: str, value: str) -> str:
        mp = self._get_memory_filepath()
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        self.memories[key] = value
        try:
            with open(mp, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2)
            return f"Memory stored: '{key}' -> '{value}'"
        except Exception as e:
            return f"Failed to store memory: {e}"

    def get_memory_context(self) -> str:
        if not self.memories:
            return ""
        lines = ["[PERSISTENT MEMORY & SESSION DECISIONS]:"]
        for k, v in self.memories.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)

    def _get_anti_patterns_filepath(self) -> str:
        for d in [".saltice", ".agents", ".grok"]:
            dp = os.path.join(self.start_dir, d)
            if os.path.isdir(dp):
                return os.path.join(dp, "anti_patterns.json")
        return os.path.join(self.start_dir, ".saltice", "anti_patterns.json")

    def load_anti_patterns(self) -> List[Dict[str, Any]]:
        ap_file = self._get_anti_patterns_filepath()
        if os.path.isfile(ap_file):
            try:
                with open(ap_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass

        # Default foundational guardrails inspired by frontier model alignment
        defaults = [
            {
                "id": "ap_glassy_ui",
                "tag": "Bland / Non-Glassy UI",
                "constraint": "Never generate flat unstyled white backgrounds or generic cards. Always deliver modern Glassmorphism (backdrop-filter: blur(20px), translucent obsidian rgba(18, 18, 22, 0.75), subtle neon glow, 1px specular borders).",
                "active": True,
                "source": "system_guardrail"
            },
            {
                "id": "ap_no_placeholders",
                "tag": "Placeholder / Truncated Code",
                "constraint": "Never write placeholder comments (e.g. '/* TODO: add full logic here */') or truncate code with '...'. Always provide 100% complete, runnable code.",
                "active": True,
                "source": "system_guardrail"
            },
            {
                "id": "ap_anti_regression",
                "tag": "Duplicate / Phantom Files",
                "constraint": "Never create duplicate files or wipe working functionality. Modify existing files surgically using replace_file_content.",
                "active": True,
                "source": "system_guardrail"
            }
        ]
        return defaults

    def record_anti_pattern(self, tag: str, constraint: str, source: str = "user_feedback") -> Dict[str, Any]:
        """Record a negative feedback constraint to prevent the agent from repeating bad generations."""
        import time
        ap_file = self._get_anti_patterns_filepath()
        os.makedirs(os.path.dirname(ap_file), exist_ok=True)

        new_entry = {
            "id": f"ap_{int(time.time()*1000)}",
            "tag": tag.strip(),
            "constraint": constraint.strip(),
            "active": True,
            "source": source,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Check if identical tag already exists; update it if so
        updated = False
        for item in self.anti_patterns:
            if item.get("tag", "").lower() == tag.strip().lower():
                item["constraint"] = constraint.strip()
                item["active"] = True
                item["source"] = source
                new_entry = item
                updated = True
                break

        if not updated:
            self.anti_patterns.append(new_entry)

        try:
            with open(ap_file, "w", encoding="utf-8") as f:
                json.dump(self.anti_patterns, f, indent=2)
        except Exception:
            pass

        return new_entry

    def toggle_anti_pattern(self, pattern_id: str, active: bool) -> bool:
        for item in self.anti_patterns:
            if item.get("id") == pattern_id:
                item["active"] = active
                try:
                    with open(self._get_anti_patterns_filepath(), "w", encoding="utf-8") as f:
                        json.dump(self.anti_patterns, f, indent=2)
                    return True
                except Exception:
                    return False
        return False

    def delete_anti_pattern(self, pattern_id: str) -> bool:
        initial_len = len(self.anti_patterns)
        self.anti_patterns = [p for p in self.anti_patterns if p.get("id") != pattern_id]
        if len(self.anti_patterns) != initial_len:
            try:
                with open(self._get_anti_patterns_filepath(), "w", encoding="utf-8") as f:
                    json.dump(self.anti_patterns, f, indent=2)
                return True
            except Exception:
                return False
        return False

    def get_negative_constraints_context(self) -> str:
        """Format active anti-patterns into high-priority prompt constraints."""
        active = [p for p in self.anti_patterns if p.get("active", True)]
        if not active:
            return ""

        lines = [
            "[CRITICAL NEGATIVE CONSTRAINTS - LEARNED FROM USER REINFORCEMENT FEEDBACK]:",
            "The following behaviors have been explicitly flagged as undesirable. You MUST NOT repeat these mistakes:"
        ]
        for p in active:
            lines.append(f"- [AVOID - {p.get('tag', 'Negative Pattern')}]: {p.get('constraint', '')}")

        return "\n".join(lines)

CONTEXT_MANAGER = ContextManager()
