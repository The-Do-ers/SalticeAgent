# Google Stax Evaluation Guide for Saltice Agent

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
   - Select `d:\USEME FOLDER\ANTIGRAVITY\SalticeAgent\stax_battery_dataset.csv`.
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
