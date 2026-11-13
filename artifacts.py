"""
Artifacts System for Antigravity Terminal Assistant
Inspired by Antigravity and Claude Code Artifacts:
- Generates structured markdown documents (Implementation Plans, Walkthroughs, Blueprints, Audits).
- Stores artifacts persistently in multi_agent_cli/artifacts/.
- Renders rich formatted artifacts directly in the terminal.
"""

import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console(force_terminal=True, legacy_windows=False)

class ArtifactManager:
    def __init__(self, storage_dir=None):
        self._custom_storage = storage_dir

    @property
    def storage_dir(self):
        if self._custom_storage:
            os.makedirs(self._custom_storage, exist_ok=True)
            return self._custom_storage
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(agent_dir, "artifacts")
        os.makedirs(target, exist_ok=True)
        return target

    def save_artifact(self, name: str, title: str, artifact_type: str, content: str) -> str:
        """Save an artifact markdown file with frontmatter metadata."""
        if not name.endswith(".md"):
            name = f"{name}.md"
        filepath = os.path.join(self.storage_dir, name)
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        header = f"""---
title: {title}
type: {artifact_type}
created_at: {timestamp}
---

# {title}

"""
        full_content = header + content.strip() + "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        console.print(Panel(f"[green]Saved artifact:[/green] [bold white]{name}[/bold white]\n[dim]Path: {filepath}[/dim]", title="[bold cyan]Artifact Created[/bold cyan]", border_style="cyan"))
        return filepath

    def list_artifacts(self):
        files = [f for f in os.listdir(self.storage_dir) if f.endswith(".md")]
        if not files:
            console.print("[yellow]No artifacts found in storage.[/yellow]")
            return
        
        table = Table(title="Generated Project Artifacts", border_style="cyan")
        table.add_column("Artifact Filename", style="bold yellow")
        table.add_column("Size", style="cyan")
        table.add_column("Modified", style="dim")
        
        for f in files:
            fp = os.path.join(self.storage_dir, f)
            sz = os.path.getsize(fp)
            mod = time.ctime(os.path.getmtime(fp))
            table.add_row(f, f"{sz} bytes", mod)
        
        console.print(table)

    def view_artifact(self, name: str):
        if not name.endswith(".md"):
            name = f"{name}.md"
        filepath = os.path.join(self.storage_dir, name)
        if not os.path.exists(filepath):
            console.print(f"[bold red]Artifact '{name}' not found.[/bold red]")
            return
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(Panel(Markdown(content), title=f"[bold green]{name}[/bold green]", border_style="green"))

ARTIFACT_MANAGER = ArtifactManager()
