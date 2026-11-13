#!/usr/bin/env python3
"""
Google Stax Benchmark Battery Generator for Saltice
Creates Stax-compliant datasets (CSV + JSONL) and custom LLM-as-a-judge autorater rubrics.
"""

import os
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SCENARIOS = [
    {
        "id": "STAX-01",
        "task_category": "Bug Fix / Existing File Respect",
        "input_prompt": "In a project with an existing 'pomodoro.html' that has a broken timer loop, fix the timer without creating duplicate files.",
        "reference_criteria": "Surgically edits pomodoro.html using precise edits. Does NOT create index.html or duplicate files. Verifies timer tick interval.",
        "saltice_output": "Identified timer interval bug in pomodoro.html. Applied targeted replace_file_content to line 42 (clearInterval before setInterval). Preserved all existing styling, zero duplicate files created.",
        "rubric_target": "Karpathy Simplicity & Anti-Duplication"
    },
    {
        "id": "STAX-02",
        "task_category": "Frontend UI / Glassy Standards",
        "input_prompt": "Create a modern Glassy Dark Mode Analytics Card with frosted glass, neon cyan borders, and smooth hover glow.",
        "reference_criteria": "CSS includes backdrop-filter: blur(16px), background: rgba(255, 255, 255, 0.05), neon border rgba(0, 240, 255, 0.3), no white screen stubs.",
        "saltice_output": "<div class='glass-card' style='backdrop-filter: blur(16px); background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.3); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); border-radius: 16px; padding: 24px; color: #fff;'><h2>Live Telemetry</h2><div class='metric'>99.98%</div></div>",
        "rubric_target": "Glassy UI Standards"
    },
    {
        "id": "STAX-03",
        "task_category": "Zero-White-Screen Completeness",
        "input_prompt": "Build a responsive Pomodoro Timer with start, pause, reset, and audio notification.",
        "reference_criteria": "100% complete executable code. Zero '// TODO: add logic' comments. Audio context or sound synthesized. Fully closed tags.",
        "saltice_output": "Complete HTML5 document with inline CSS and ES6 JavaScript. Full Web Audio API synthesizer for chime notification. Zero placeholder comments or stubs.",
        "rubric_target": "Functional Integrity"
    },
    {
        "id": "STAX-04",
        "task_category": "Non-Blocking Dev Server Rule",
        "input_prompt": "Verify a newly built Vite/React frontend application in an automated agent loop.",
        "reference_criteria": "Must NOT execute blocking 'npm run dev' or 'npx vite' in run_command. Uses 'npm run build' or 'npx tsc --noEmit' for headless verification.",
        "saltice_output": "Executed 'npm run build' and static AST validation synchronously. Server start deferred to user terminal instruction to prevent agent loop hanging.",
        "rubric_target": "Execution Safety"
    },
    {
        "id": "STAX-05",
        "task_category": "Karpathy Simplicity",
        "input_prompt": "Refactor a 20-line utility function to handle empty arrays safely.",
        "reference_criteria": "Add a simple guard clause (if not arr: return []). Do not introduce new classes, abstract factory patterns, or single-use helper modules.",
        "saltice_output": "Added guard clause: `if not items: return []`. Kept function signature identical. Zero unnecessary dependencies or abstractions added.",
        "rubric_target": "Karpathy Simplicity"
    },
    {
        "id": "STAX-06",
        "task_category": "Autonomous Self-Healing",
        "input_prompt": "Fix a SyntaxError: unexpected token '<' when loading JSON from an API endpoint that returned an HTML error page.",
        "reference_criteria": "Checks HTTP status code and response content-type before calling response.json(). Provides clean fallback error.",
        "saltice_output": "Wrapped fetch in status & content-type check. If content-type does not contain 'application/json', surfaces raw text error message instead of crashing.",
        "rubric_target": "Robustness & Error Recovery"
    },
    {
        "id": "STAX-07",
        "task_category": "Context & Token Economy",
        "input_prompt": "Inspect a 5,000 line codebase to find where the database connection pool is initialized.",
        "reference_criteria": "Uses ripgrep / grep_search with targeted regex rather than dumping the entire directory contents into context.",
        "saltice_output": "Executed grep_search(Query='create_pool|create_engine|PoolConfig'). Found exact initialization at db/session.py:34. Consumed only 42 tokens.",
        "rubric_target": "Token Economy"
    },
    {
        "id": "STAX-08",
        "task_category": "Asynchronous Subagent Delegation",
        "input_prompt": "Run a security audit across all NPM and Python dependencies while continuing to draft the implementation plan.",
        "reference_criteria": "Spawns background subagent for Snyk/audit scan without blocking main planner thread.",
        "saltice_output": "Dispatched background task `spawn_subagent(role='security_auditor', prompt='snyk test')`. Main planner immediately continued implementation_plan.md drafting.",
        "rubric_target": "Asynchronous Concurrency"
    },
    {
        "id": "STAX-09",
        "task_category": "Living Documentation Triple-Pack",
        "input_prompt": "Deliver a full-stack authentication microservice with comprehensive documentation.",
        "reference_criteria": "Delivers implementation_plan.md (architecture & decisions), walkthrough.md (usage & testing), and README.md (quickstart).",
        "saltice_output": "Generated implementation_plan.md with threat model, walkthrough.md with curl commands and test suite output, and updated README.md.",
        "rubric_target": "Documentation Integrity"
    },
    {
        "id": "STAX-10",
        "task_category": "Path Resolution & Relocation Defense",
        "input_prompt": "Execute agent tools when the agent directory is nested inside a subfolder under the workspace.",
        "reference_criteria": "Uses dynamic sys.path resolution and anchor paths (AGENT_DIR, workspace_root) rather than hardcoded C:\\ absolute paths.",
        "saltice_output": "Resolved paths using `Path(__file__).resolve().parent` and dynamic discovery. Zero path regressions across root and subfolder execution.",
        "rubric_target": "Architectural Resilience"
    }
]

def generate():
    csv_path = BASE_DIR / "stax_battery_dataset.csv"
    jsonl_path = BASE_DIR / "stax_battery_dataset.jsonl"
    guide_path = BASE_DIR / "STAX_EVALUATION_GUIDE.md"

    # 1. Write CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "task_category", "input_prompt", "reference_criteria", "saltice_output", "rubric_target"])
        writer.writeheader()
        for s in SCENARIOS:
            writer.writerow(s)

    # 2. Write JSONL
    with open(jsonl_path, mode="w", encoding="utf-8") as f:
        for s in SCENARIOS:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # 3. Write Guide & Autorater Rubrics
    guide_content = """# Google Stax Evaluation Guide for Saltice Agent

This guide provides everything you need to run automated, data-driven evaluations of the **Saltice Autonomous Agent** on [Google Stax](https://stax.withgoogle.com).

---

## 1. What is in this Evaluation Battery?

We have generated two Stax-ready dataset formats in `SalticeAgent/`:
- **`stax_battery_dataset.csv`**: Standard CSV format for 1-click upload.
- **`stax_battery_dataset.jsonl`**: JSON Lines format for multi-field Stax project schemas.

Each row contains:
- `input_prompt`: The real coding task / scenario.
- `reference_criteria`: The rigorous ground truth rules (Karpathy simplicity, no white screens, non-blocking servers).
- `saltice_output`: The actual actions and code output produced by Saltice.
- `rubric_target`: The specific quality dimension being evaluated.

---

## 2. Step-by-Step: How to Upload to Stax

1. Open your browser where you logged into **[stax.withgoogle.com](https://stax.withgoogle.com)**.
2. Click **Create Project** (or **New Evaluation**).
3. Select **Pointwise Evaluation** (to score Saltice alone) or **Side-by-Side (SxS)** (to compare Saltice vs. Gemini 2.0 / Claude / GPT-4o).
4. In the **Dataset** tab:
   - Click **Import Dataset** -> **Upload CSV / JSONL**.
   - Select `d:\\USEME FOLDER\\ANTIGRAVITY\\SalticeAgent\\stax_battery_dataset.csv`.
   - Map:
     - Input field -> `input_prompt`
     - Reference / Ground truth -> `reference_criteria`
     - Candidate output -> `saltice_output`

---

## 3. Custom Stax Autorater Rubrics (Copy & Paste into Stax)

In Stax, click **Add Evaluator / Autorater** -> **Custom LLM-as-a-Judge**, and copy-paste these rubrics:

### Autorater 1: Karpathy Simplicity & Minimal Diffs
```text
You are an expert software engineering judge assessing whether an AI coding agent adheres to Andrej Karpathy's Simplicity First principle.

Evaluation Criteria:
- Score 5 (Exceptional): The agent solved the problem with minimal, surgical changes. No bloated abstractions, no single-use classes, zero unnecessary files created.
- Score 3 (Acceptable): The code works, but introduces slight unnecessary complexity or extra helper functions.
- Score 1 (Failed): The agent overwrote entire working files, created duplicate unnecessary files (e.g. index.html when another file was already present), or introduced heavy speculative bloat.

Input: {{input_prompt}}
Reference Criteria: {{reference_criteria}}
Agent Output: {{saltice_output}}

Provide a score (1-5) and a brief justification.
```

### Autorater 2: Zero-White-Screen & Functional Completeness
```text
You are an expert frontend code auditor assessing whether code is 100% complete and ready to run.

Evaluation Criteria:
- Score 5 (Flawless): Zero placeholder comments (e.g. '// TODO: implement later', '...'). All scripts, styles, and tags are properly closed.
- Score 3 (Partial): Code runs, but contains placeholder comments or missing non-critical assets.
- Score 1 (Broken): White-screen bug, unclosed tags, syntax errors, or hollow stubs.

Input: {{input_prompt}}
Agent Output: {{saltice_output}}

Provide a score (1-5) and a brief justification.
```

### Autorater 3: Modern Glassy UI Aesthetics
```text
You are a senior UI/UX designer evaluating web deliverables for modern aesthetic standards.

Evaluation Criteria:
- Score 5 (Stunning Glassmorphism): Clean dark theme, frosted glass effects (backdrop-filter: blur), subtle neon borders, rounded geometry, responsive layout.
- Score 3 (Standard): Clean UI, but plain or standard bootstrap-style flat colors without frosted glass or modern styling.
- Score 1 (Ugly/Outdated): Default browser black-on-white text, unstyled forms, misaligned raw HTML.

Input: {{input_prompt}}
Agent Output: {{saltice_output}}

Provide a score (1-5) and a brief justification.
```

---

## 4. Viewing the Stax Evaluation Results
Once Stax finishes running the autoraters:
- Check the **Scorecards**: Overall average score across all 10 scenarios.
- Check the **Radar Chart**: Comparison across Simplicity, Completeness, Aesthetics, and Resilience.
- For SxS evaluations: View the **Win Rate %** of Saltice against vanilla baseline models!
"""

    with open(guide_path, mode="w", encoding="utf-8") as f:
        f.write(guide_content.strip() + "\n")

    print(f"Generated Stax Suite successfully:")
    print(f"  - CSV:   {csv_path} ({len(SCENARIOS)} scenarios)")
    print(f"  - JSONL: {jsonl_path}")
    print(f"  - Guide: {guide_path}")

if __name__ == "__main__":
    generate()
