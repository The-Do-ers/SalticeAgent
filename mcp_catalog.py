"""
MCP Server Catalog & Discovery Engine for Saltice
Indexes 4,200+ curated Model Context Protocol (MCP) servers from awesome-mcp-servers.
Provides zero-token progressive discovery: tools and users search on demand
without polluting the LLM prompt context window.
"""

import os
import re
from typing import List, Dict, Optional

class MCPCatalog:
    def __init__(self, readme_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.readme_path = readme_path or os.path.abspath(
            os.path.join(base_dir, "..", ".repo_cache", "awesome-mcp-servers", "README.md")
        )
        self._servers: List[Dict[str, str]] = []
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        if not os.path.exists(self.readme_path):
            return

        try:
            with open(self.readme_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

            current_category = "General"
            # Parse markdown lines
            for line in text.splitlines():
                cat_match = re.match(r"^###\s+.*?\s*<a name=\"([^\"]+)\"></a>(.*)", line)
                if cat_match:
                    current_category = cat_match.group(2).strip().strip("* ").strip()
                    continue

                m = re.match(r"^-\s+\[([^\]]+)\]\((https://github\.com/[^\)]+)\)\s*(.*)", line)
                if m:
                    name = m.group(1).strip()
                    url = m.group(2).strip()
                    raw_desc = m.group(3).strip()
                    # Strip badges, urls, emojis and markdown image links
                    clean_desc = re.sub(r'\[!\[.*?\]\(.*?\)\]\(.*?\)', '', raw_desc)
                    clean_desc = re.sub(r'https?://\S+', '', clean_desc)
                    clean_desc = re.sub(r'[^\x00-\x7F]+', ' ', clean_desc)
                    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip(' -')

                    # Extract install/run hint if present
                    install_hint = ""
                    npx_m = re.search(r'(npx\s+(?:-y\s+)?[@a-zA-Z0-9_\-\/]+)', raw_desc)
                    pip_m = re.search(r'(pip\s+install\s+[a-zA-Z0-9_\-\/]+)', raw_desc)
                    if npx_m:
                        install_hint = npx_m.group(1)
                    elif pip_m:
                        install_hint = pip_m.group(1)

                    self._servers.append({
                        "name": name,
                        "url": url,
                        "category": current_category,
                        "description": clean_desc,
                        "install": install_hint
                    })
        except Exception:
            pass

    def search(self, query: str, category: Optional[str] = None, limit: int = 8) -> List[Dict[str, str]]:
        self._ensure_loaded()
        if not self._servers:
            return []

        q_terms = [t.lower() for t in query.lower().split() if len(t) >= 2]
        cat_lower = category.lower() if category else None

        scored = []
        for s in self._servers:
            if cat_lower and cat_lower not in s["category"].lower():
                continue

            name_lower = s["name"].lower()
            desc_lower = s["description"].lower()
            cat_text = s["category"].lower()

            score = 0
            for term in q_terms:
                if term in name_lower:
                    score += 50
                if term in desc_lower:
                    score += 20
                if term in cat_text:
                    score += 15
                if s["install"] and term in s["install"].lower():
                    score += 25

            if score > 0:
                scored.append((score, s))

        scored.sort(key=lambda x: -x[0])
        return [item for _, item in scored[:limit]]

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._servers)


MCP_CATALOG = MCPCatalog()


def search_mcp_servers(query: str, category: Optional[str] = None, limit: int = 6) -> str:
    """
    Search 4,200+ curated MCP servers by keyword or category.
    Returns matched servers with repo URL, description, and install commands.
    """
    results = MCP_CATALOG.search(query, category=category, limit=limit)
    if not results:
        return f"No MCP servers found matching '{query}'. Total catalog size: {MCP_CATALOG.count():,} servers."

    lines = [f"[MCP REGISTRY SEARCH: '{query}' ({len(results)} matches from {MCP_CATALOG.count():,} servers)]:"]
    for r in results:
        lines.append(f"\n- {r['name']} ({r['category']})")
        lines.append(f"  URL: {r['url']}")
        if r['description']:
            lines.append(f"  Info: {r['description'][:140]}...")
        if r['install']:
            lines.append(f"  Run Command: `{r['install']}`")

    return "\n".join(lines)
