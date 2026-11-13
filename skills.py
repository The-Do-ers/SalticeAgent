"""
Comprehensive Skills System for Saltice & Antigravity
Multi-Tier Discovery:
- Builtin & Global Plugins:
  - C:\\Users\\HP\\.gemini\\config\\plugins\\
  - C:\\Users\\HP\\.gemini\\antigravity\\builtin\\skills\\
- Workspace & User Repos:
  - .agents/skills/, .grok/skills/, .claude/skills/, multi_agent_cli/skills/
  - ~/.agents/skills/, ~/.grok/skills/, ~/.claude/skills/

Features:
- Fast recursive discovery (discovers 130+ specialized skills in milliseconds)
- Full YAML frontmatter parsing (name, description, when-to-use, argument-hint, allowed-tools)
- Progressive Disclosure: Compact catalog in prompt to protect token budget; full instructions injected dynamically on intent/keyword match or slash command
- Slash Commands: /<skill-name> triggers skill instantly (e.g. /glassy-ui, /chrome-devtools, /firebase-firestore)
"""

import os
import re
from typing import Dict, List, Optional
from rich.table import Table
from rich.console import Console
from rich import box

try:
    from vector_intelligence import find_skills_by_vector, build_skills_index
    _VEC_SKILLS_OK = True
except ImportError:
    _VEC_SKILLS_OK = False

console = Console(force_terminal=True, legacy_windows=False)

STOP_WORDS = {
    "build", "make", "create", "write", "help", "app", "tool", "code",
    "guide", "basics", "setup", "skill", "workflow", "view", "read",
    "check", "start", "clean", "project", "overview", "system"
}

class Skill:
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        path: str,
        category: str = "General",
        when_to_use: List[str] = None,
        paths: List[str] = None,
        user_invocable: bool = True,
        argument_hint: str = "",
        allowed_tools: List[str] = None
    ):
        self.name = name
        self.description = description
        self.content = content
        self.path = path
        self.category = category
        self.when_to_use = when_to_use or []
        self.paths = paths or []
        self.user_invocable = user_invocable
        self.argument_hint = argument_hint
        self.allowed_tools = allowed_tools or []

    def matches_query(self, query: str) -> bool:
        q = query.lower()
        # 1. Direct name match
        normalized_name = self.name.lower().replace("-", " ")
        if self.name.lower() in q or normalized_name in q:
            return True

        # 2. Matches against when_to_use trigger phrases and individual significant trigger words
        for phrase in self.when_to_use:
            p_clean = phrase.lower().strip()
            if len(p_clean) >= 2 and p_clean in q:
                return True
            for word in p_clean.split():
                if len(word) >= 4 and word in q:
                    return True

        # 3. Matches on stem/root tokens from skill name (e.g. 'test' matches 'tests', 'testing')
        tokens = [t for t in re.split(r"[-_\s]+", self.name.lower()) if len(t) >= 3 and t not in ["code", "tool", "guide", "setup", "skill", "basics", "workflow"]]
        for t in tokens:
            if re.search(rf"\b{re.escape(t)}", q):
                return True

        return False

class SkillManager:
    def __init__(self, custom_dirs: Optional[List[str]] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(base_dir, ".."))

        # Discovery roots (global plugins, builtins, ECC, Claude-Skills, Karpathy, Academic, workspace, user home)
        self.search_roots = custom_dirs or [
            r"C:\Users\HP\.gemini\config\plugins",
            r"C:\Users\HP\.gemini\antigravity\builtin\skills",
            os.path.join(base_dir, ".agents", "skills"),
            os.path.join(workspace_root, ".agents", "skills"),
            os.path.join(base_dir, ".grok", "skills"),
            os.path.join(workspace_root, ".grok", "skills"),
            os.path.join(base_dir, ".claude", "skills"),
            os.path.join(workspace_root, ".claude", "skills"),
            os.path.join(base_dir, "skills"),
            os.path.join(workspace_root, "skills"),
            os.path.join(base_dir, ".repo_cache", "ECC", "skills"),
            os.path.join(workspace_root, ".repo_cache", "ECC", "skills"),
            os.path.join(base_dir, ".repo_cache", "ECC", ".agents", "skills"),
            os.path.join(workspace_root, ".repo_cache", "ECC", ".agents", "skills"),
            os.path.join(base_dir, ".repo_cache", "ECC", ".claude", "skills"),
            os.path.join(workspace_root, ".repo_cache", "ECC", ".claude", "skills"),
            os.path.join(base_dir, ".repo_cache", "claude-skills"),
            os.path.join(workspace_root, ".repo_cache", "claude-skills"),
            os.path.join(base_dir, ".repo_cache", "academic-research-skills"),
            os.path.join(workspace_root, ".repo_cache", "academic-research-skills"),
            os.path.join(base_dir, ".repo_cache", "andrej-karpathy-skills", "skills"),
            os.path.join(workspace_root, ".repo_cache", "andrej-karpathy-skills", "skills"),
            os.path.join(base_dir, ".repo_cache", "chrome-devtools-mcp", "skills"),
            os.path.join(workspace_root, ".repo_cache", "chrome-devtools-mcp", "skills"),
            os.path.expanduser("~/.agents/skills"),
            os.path.expanduser("~/.grok/skills"),
            os.path.expanduser("~/.claude/skills")
        ]
        self.skills: Dict[str, Skill] = {}
        self.load_skills()

    def load_skills(self):
        self.skills = {}
        visited_dirs = set()

        for root_dir in self.search_roots:
            if not os.path.exists(root_dir):
                continue
            norm_root = os.path.abspath(root_dir)
            if norm_root in visited_dirs:
                continue
            visited_dirs.add(norm_root)

            try:
                for dirpath, _, filenames in os.walk(norm_root):
                    if "SKILL.md" in filenames:
                        skill_file = os.path.join(dirpath, "SKILL.md")
                        default_name = os.path.basename(dirpath)
                        # Derive category from path
                        category = "Workspace"
                        dl = dirpath.lower().replace("\\", "/")
                        if "repo_cache/ecc" in dl or "/ecc/" in dl:
                            category = "ECC Engineering"
                        elif "claude-skills" in dl:
                            category = "Claude Code Skills"
                        elif "academic-research" in dl:
                            category = "Academic Research"
                        elif "andrej-karpathy" in dl:
                            category = "Karpathy Guidelines"
                        elif "chrome-devtools" in dl:
                            category = "Chrome DevTools MCP"
                        elif "plugins" in dl:
                            parts = dl.split("/")
                            try:
                                p_idx = [p.lower() for p in parts].index("plugins")
                                category = parts[p_idx + 1].replace("-plugin", "").title()
                            except Exception:
                                category = "System Plugin"
                        elif "builtin" in dl:
                            category = "Antigravity Builtin"
                        elif ".agents" in dl or "multi_agent_cli" in dl:
                            category = "Core Saltice"

                        self._parse_skill_file(skill_file, default_name, category)
            except Exception:
                pass

    def _parse_skill_file(self, file_path: str, default_name: str, category: str):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()

            fm_match = re.search(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)", raw)
            if not fm_match:
                self.skills[default_name] = Skill(
                    name=default_name,
                    description=f"Specialized skill for {default_name}",
                    content=raw.strip(),
                    path=file_path,
                    category=category
                )
                return

            frontmatter = fm_match.group(1)
            body = fm_match.group(2).strip()

            def get_field(field_name: str, default: str = "") -> str:
                m = re.search(rf"^{field_name}:\s*(.+)$", frontmatter, re.MULTILINE | re.IGNORECASE)
                return m.group(1).strip().strip('"\'') if m else default

            name = get_field("name", default_name)
            desc = get_field("description", "No description provided.")
            arg_hint = get_field("argument-hint", "")
            user_invocable_val = get_field("user-invocable", "true").lower()
            user_invocable = user_invocable_val not in ["false", "no", "0"]

            # Parse trigger phrases
            when_to_use = []
            when_m = re.search(r"^(?:when-to-use|when_to_use):\s*(.*(?:\n\s*-\s*.*)*)", frontmatter, re.MULTILINE | re.IGNORECASE)
            if when_m:
                lines = when_m.group(1).split("\n")
                for l in lines:
                    cleaned = re.sub(r"^[\s\-]+", "", l).strip().strip('"\'')
                    if cleaned:
                        when_to_use.append(cleaned)

            if not when_to_use:
                # Add default triggers based on name
                when_to_use = [name.replace("-", " "), name]

            self.skills[name] = Skill(
                name=name,
                description=desc,
                content=body,
                path=file_path,
                category=category,
                when_to_use=when_to_use,
                user_invocable=user_invocable,
                argument_hint=arg_hint
            )
        except Exception:
            pass

    def get_skills_catalog(self) -> str:
        """
        Progressive Disclosure:
        Generates a token-efficient catalog notice with key skills and command format.
        """
        count = len(self.skills)
        if count == 0:
            return ""

        # Highlight key popular skills
        spotlight = [
            "karpathy-guidelines", "glassy-ui", "autonomous-tester", "api-scaffolding",
            "code-refactor", "git-workflow", "security-auditor", "test-driven-development",
            "academic-paper", "deep-research", "everything-claude-code",
            "chrome-devtools", "a11y-debugging", "modern-web-guidance",
            "firebase-firestore", "gemini-api-dev"
        ]

        lines = [
            f"[SPECIALIZED SKILLS SYSTEM: {count} Total Skills Installed]",
            "Skills can be invoked via slash command `/<skill-name>` or activate automatically when relevant to user query.",
            "Common Spotlight Skills:"
        ]
        for sname in spotlight:
            if sname in self.skills:
                lines.append(f"- `/{sname}`: {self.skills[sname].description[:90]}...")

        lines.append(f"(Plus {count - len(spotlight)} more specialized skills across Flutter, Firebase, Chrome DevTools, BigQuery, and Science APIs)")
        return "\n".join(lines)

    def _score_skill_relevance(self, skill: Skill, query: str) -> int:
        q = query.lower()
        score = 0
        norm_name = skill.name.lower().replace("-", " ")

        # 1. Exact name match (highest priority)
        if skill.name.lower() in q:
            score += 150
        elif norm_name in q:
            score += 100

        # 2. Trigger phrases in when_to_use
        for phrase in skill.when_to_use:
            p_clean = phrase.lower().strip()
            if len(p_clean) >= 3:
                if p_clean in q:
                    score += 80
                else:
                    words = [w for w in p_clean.split() if w not in STOP_WORDS and len(w) >= 4]
                    for w in words:
                        if w in q:
                            score += 30

        # 3. Specific key concepts in description
        desc_clean = skill.description.lower()
        key_phrases = [
            "surgical changes", "avoid overcomplication", "simplicity first",
            "fastapi", "jwt", "security audit", "sql injection", "vulnerability",
            "unit test", "frosted glass", "neon", "playwright", "e2e"
        ]
        for kp in key_phrases:
            if kp in desc_clean and any(w in q for w in kp.split() if len(w) >= 4):
                score += 45

        # 4. Token match from skill name (e.g. 'security', 'api', 'flutter', 'firebase')
        tokens = [t for t in re.split(r"[-_\s]+", skill.name.lower()) if len(t) >= 4 and t not in STOP_WORDS]
        for t in tokens:
            if re.search(rf"\b{re.escape(t)}", q):
                score += 30

        return score

    def find_relevant_skills(self, query: str, limit: int = 3) -> List["Skill"]:
        """Rank and return top relevant skills using weighted relevance scoring.
        
        Merges two signals:
        - Keyword/token scoring (fast, no API needed)
        - Vector cosine similarity via FAISS+Gemini embeddings (when available)
        """
        keyword_scores: Dict[str, int] = {}
        for skill in self.skills.values():
            sc = self._score_skill_relevance(skill, query)
            if sc > 0:
                keyword_scores[skill.name] = sc

        # Augment with vector similarity scores (adds ~200-500ms only when index built)
        vector_bonus: Dict[str, float] = {}
        if _VEC_SKILLS_OK:
            try:
                vec_results = find_skills_by_vector(query, top_k=5)
                for skill_name, sim in vec_results:
                    # Convert 0-1 similarity to a score bonus comparable to keyword scores
                    vector_bonus[skill_name] = sim * 120  # Max bonus: 120 pts at sim=1.0
            except Exception:
                pass

        # Merge: keyword score + vector bonus
        combined: Dict[str, float] = {}
        all_skill_names = set(list(keyword_scores.keys()) + list(vector_bonus.keys()))
        for sname in all_skill_names:
            combined[sname] = keyword_scores.get(sname, 0) + vector_bonus.get(sname, 0)

        scored = [(score, self.skills[name]) for name, score in combined.items() if name in self.skills]
        scored.sort(key=lambda x: -x[0])
        return [skill for _, skill in scored[:limit]]

    def get_skill_by_command(self, command: str) -> Optional[Skill]:
        """Resolve slash command like '/glassy-ui' or '/chrome-devtools'."""
        clean_cmd = command.strip().lstrip("/").lower()
        for name, skill in self.skills.items():
            if name.lower() == clean_cmd:
                return skill
        return None

    def display_skills_table(self, filter_query: Optional[str] = None):
        """Rich interactive CLI display of all installed skills."""
        table = Table(
            title=f"All Installed Skills ({len(self.skills)} Total) [Progressive Disclosure]",
            border_style="cyan",
            box=box.ROUNDED
        )
        table.add_column("Slash Command", style="bold yellow", width=32)
        table.add_column("Category", style="magenta", width=18)
        table.add_column("Description", style="white")

        matches = 0
        for s in sorted(self.skills.values(), key=lambda x: (x.category, x.name)):
            if filter_query:
                fq = filter_query.lower()
                if fq not in s.name.lower() and fq not in s.category.lower() and fq not in s.description.lower():
                    continue

            slash = f"/{s.name}" if s.user_invocable else s.name
            desc = s.description[:85] + ("..." if len(s.description) > 85 else "")
            table.add_row(slash, s.category, desc)
            matches += 1

        console.print(table)
        if filter_query:
            console.print(f"[dim]Showing {matches} skills matching '{filter_query}'. Type '/skills' to view all.[/dim]")
        else:
            console.print(f"[dim]Total: {matches} skills ready. To filter, type '/skills <filter>' (e.g. '/skills flutter' or '/skills web')[/dim]")

SKILL_MANAGER = SkillManager()
