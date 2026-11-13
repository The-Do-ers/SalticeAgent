# Saltice Autonomous Coding Agent — Master System Architecture & Capabilities Report

**Version**: 3.4.0 (Antigravity Engine Core)  
**Status**: Production Ready • Zero-Hang Architecture  
**Active Assets**: 889 Specialized Skills • 4,234 Curated MCP Servers • 10 ECC Subagent Roles • 25 Production Tools  

---

## 1. Executive Summary & Identity

**Saltice** is a next-generation autonomous software engineering agent built to operate directly in complex multi-file codebases. Powered by the `SalticeAntigravityEngine`, Saltice combines:
1. **Resilient Dual-Mode Parsing**: Native JSON structured tool execution backed by automated regex/markdown block recovery when models omit strict JSON wrapping.
2. **Progressive Skill Disclosure**: Over 880 domain-specific runbooks loaded into memory on-demand without exhausting prompt token limits.
3. **Microsoft Context Engineering & Loop Breakers**: Multi-turn history scrubbing that cuts redundant prompt tokens by **89.7%** and circuit breakers that terminate infinite error loops.
4. **Asynchronous Multi-Agent Swarm**: Background subagent delegation for research, planning, testing, and audits without freezing the main conversation.
5. **Universal Tooling & MCP Integration**: Direct terminal execution, surgical file edits, Cloudflare Pages deployments, 4,234 on-demand MCP servers, and live browser automation via Chrome DevTools MCP.

---

## 2. Engineering Operating System & Guiding Pillars

Saltice enforces the canonical **Everything Claude Code (ECC)** engineering lifecycle:
$$\text{plan} \longrightarrow \text{test} \longrightarrow \text{implement} \longrightarrow \text{review} \longrightarrow \text{verify} \longrightarrow \text{remember} \longrightarrow \text{improve}$$

### Andrej Karpathy's 4 Golden Pillars
1. **Think Before Coding**:
   - Surface constraints, assumptions, and tradeoffs explicitly.
   - For non-trivial tasks, generate `implementation_plan.md` before executing file edits.
2. **Simplicity First**:
   - Deliver the minimal code that solves the problem.
   - Avoid speculative generalizations, complex wrapper layers, and premature configurability.
3. **Surgical Changes**:
   - Touch only the lines required to achieve the goal.
   - Always prefer `replace_file_content` over rewriting entire 500+ line files.
   - Never leave orphan files or broken intermediate states.
4. **Goal-Driven Execution**:
   - Define objective, non-blocking verification criteria.
   - Run compilation checks (`npm run build`, `npx tsc --noEmit`) or automated test suites before declaring completion.

### Strict Safety & Anti-Regression Guardrails
* **No Blocking Dev Servers**: Hard pre-tool hook blocks commands like `npx vite`, `npm run dev`, or `npm start` that run indefinitely and freeze autonomous agent loops.
* **Zero White-Screen Policy**: Every generated file must be 100% complete. Stub comments like `/* TODO: add logic */` are strictly forbidden.
* **Living Documentation Triple-Pack**: All major multi-file workflows maintain:
  * `implementation_plan.md`: Technical breakdown, architecture, and verification strategy.
  * `walkthrough.md`: Changes made, test results, and execution guide.
  * `README.md`: Quickstart and project summary.

---

## 3. Multi-Provider LLM Tier & Resiliency

Saltice is provider-agnostic, supporting a wide array of state-of-the-art models with automatic failover, rate limiting, and exponential backoff:

| Provider | Supported Models | Primary Use Case |
| :--- | :--- | :--- |
| **OpenRouter** | Claude 3.7 Sonnet, Claude 3.5 Sonnet, GPT-4o, DeepSeek R1/V3, Qwen 2.5 Coder | Flagship planning, complex refactors, multi-file code generation |
| **Gemini** | Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro | Ultra-fast reasoning, large context analysis, multimodal verification |
| **Mistral** | Mistral Large 2, Codestral 2501 | High-speed coding tasks and Python automation |
| **Groq** | Llama 3.3 70B Versatile, DeepSeek R1 Distill | Sub-second latency for auxiliary and subagent tasks |
| **Cloudflare** | Llama 3.3 70B Instruct, BGE Embeddings | Edge deployment, security scans, semantic vector search |
| **Local** | Ollama, LM Studio, vLLM | Complete privacy, offline execution, air-gapped development |

### Rate Limiting & Token Monitor
* `RateLimitedQueue`: Maintains sliding-window tracking for TPM (Tokens Per Minute), RPM (Requests Per Minute), and RPD (Requests Per Day).
* Automatically catches HTTP `429` (Rate Limit) and `503` (Overloaded) errors, applying exponential backoff with random jitter.
* Interactive `/tokens` command displays live token quotas, model latency, and remaining credit balances.

---

## 4. Context Engineering & Loop Engineering

### A. 89.7% Multi-Turn Context Pruning (Microsoft Lesson 12 Architecture)
In prolonged multi-turn sessions, prior tool outputs (such as writing large files) rapidly fill the context window, causing massive token burn (e.g. 64k token spikes).
* **The Solution**: `scrub_history_for_context()` in `caveman.py`.
* Recent turn memory ($t = N-1$) is kept verbatim for working memory.
* Older turns ($t < N-1$) have heavy code writes replaced with lightweight receipts: `[Content written to disk: App.tsx (4,200 chars), syntax verified]`.
* **Benchmark Result**: Context size for multi-turn sessions drops from **6,476 characters (~1,619 tokens) to 668 characters (~167 tokens)** — an **89.7% reduction** per turn!

### B. Loop Stall Detection & Circuit Breaker (Cobus Greyling Loop Engineering)
* Tracks normalized observation signatures to detect recurring failures.
* **Turn 2 of identical error**: Injects a high-priority reflection notice instructing the agent to step back, re-read the error, and switch strategies.
* **Turn 3/4 of identical error**: Circuit breaker trips, halting execution and returning a root-cause diagnosis rather than exhausting user API credits.
* Bounded iterations: Replaced infinite loops with configurable `max_iterations = 10`.

### C. Caveman Lite Compression
* Strips conversational meta-chatter, pleasantries, and filler words while preserving 100% of code syntax, file paths, and terminal commands.
* Standardized as the default compression mode across all engine workflows.

### D. Tool Output Distillation & Headroom Reversible CCR
* Terminal and build outputs exceeding 3,000 characters are automatically saved to `.saltice/tool_logs/tool_<timestamp>_<hash>.log`.
* Returns an intelligent 1,200-character distillation (head + tail + fatal error lines) with a unique retrieval receipt ID.
* Tool `retrieve_cached_content(log_id, start_line, end_line)` allows inspecting exact line ranges on demand.
* Headroom `SmartCrusher` structurally compacts large JSON responses by >95% while preserving data schema and sample items.

---

## 5. The 889 Specialized Skills Ecosystem

Saltice indexes **889 specialized skills** across 8 discovery tiers using progressive disclosure (only skill names and triggers reside in the prompt; full instructions load on-demand):

1. **Chrome DevTools MCP (7 skills)**: `chrome-devtools`, `chrome-devtools-cli`, `cookie-debugging`, `a11y-debugging`, `debug-optimize-lcp`, `memory-leak-debugging`, `troubleshooting`.
2. **Karpathy Guidelines (5 skills)**: `karpathy-guidelines`, `simplicity-first`, `surgical-edits`, `think-before-coding`, `goal-driven-execution`.
3. **ECC Engineering (20+ skills)**: `tdd-workflow`, `anti-regression`, `modular-decomposition`, `architectural-review`, `continuous-learning`.
4. **Claude Code Skills (100+ skills)**: `fullstack-dev`, `git-workflow`, `code-refactor`, `api-scaffolding`, `security-auditor`.
5. **Academic Research Skills (30+ skills)**: `academic-paper`, `literature-review`, `citation-auditor`, `statistical-methodology`.
6. **Core Saltice Skills**: `glassy-ui`, `liquid-glass-design`, `autonomous-tester`, `cloudflare-platform`.
7. **System & Plugin Skills (700+ skills)**: BigQuery, Firestore, Cloud Storage, Flutter, Dart, PyMOL, NCBI, etc.
8. **Workspace Skills**: Project-local skills loaded from `.agents/skills/`.

> **Usage**: Type `/<skill-name>` (e.g. `/glassy-ui`, `/chrome-devtools`, `/karpathy-guidelines`) in the terminal to activate any skill instantly.

---

## 6. Asynchronous Multi-Agent Swarm (10 Personas)

Managed by `subagents.py`, subagents execute in background daemon threads with isolated execution contexts:

| Subagent Role | Primary Responsibility |
| :--- | :--- |
| **`planner`** | Decomposes complex user goals into granular, testable steps with verification gates. |
| **`architect`** | System design and scalability; ensures high cohesion and low coupling across modules. |
| **`tdd-guide`** | Writes unit and integration tests first; verifies implementations against strict coverage criteria. |
| **`code-reviewer`** | Audits code quality, edge cases, readability, and performance before completion. |
| **`security-reviewer`** | Audits OWASP Top 10 vulnerabilities, detects secret leaks, checks input sanitization. |
| **`build-error-resolver`** | Rapidly diagnoses and resolves compilation, type, and lint failures. |
| **`doc-updater`** | Synchronizes implementation plans, walkthroughs, and READMEs. |
| **`academic-researcher`** | Literature synthesis, citation verification, and rigorous methodology review. |
| **`karpathy-auditor`** | Enforces simplicity, prevents speculative over-engineering, and mandates surgical edits. |
| **`browser-agent`** | Headless Chrome DevTools DOM inspection, console error capture, and Lighthouse audits. |

---

## 7. Curated MCP Registry & Chrome DevTools MCP

### A. 4,234 Curated MCP Servers (`mcp_catalog.py`)
* Indexed across 24 categories (Database, Cloud, AI, Browser, DevTools, GitHub, Docker, etc.) from `awesome-mcp-servers`.
* Zero prompt token cost: Queried on-demand via `search_mcp_servers(query, category)` or `/mcp <query>`.

### B. Chrome DevTools MCP Integration
* Global Antigravity config: `C:\Users\HP\.gemini\config\mcp_config.json`
* Plugin config: `C:\Users\HP\.gemini\config\plugins\chrome-devtools-plugin\mcp_config.json`
* Runs headless Chrome via `npx -y chrome-devtools-mcp@latest --headless --no-usage-statistics`.
* Automated inspection tool: `inspect_url_with_browser(url, take_screenshot, run_lighthouse)`.
* Low-level tool calling: `run_chrome_devtools(tool_name, args, flags)`.
* Interactive terminal command: `/browser <url>`.

---

## 8. Complete Production Toolbelt Reference (25 Tools)

1. `run_command(cmd, timeout)`: Structured shell command execution with exit code capture and non-blocking server guardrails.
2. `write_file(filepath, content)`: Creates or overwrites files with automatic parent directory creation.
3. `replace_file_content(filepath, target, replacement)`: Surgical contiguous text replacement.
4. `view_file_slice(filepath, start_line, end_line)`: Inspects specific file segments without blowing context.
5. `search_web(query, max_results)`: Multi-source free web search (DuckDuckGo + Wikipedia + PyPI).
6. `fetch_webpage(url)`: Extracts clean markdown text from any web URL.
7. `spawn_subagent(role, prompt, provider)`: Asynchronous background worker spawning.
8. `check_subagent_status(subagent_id)`: Checks status and progress of background subagent.
9. `wait_for_subagent(subagent_id, timeout_sec)`: Blocks until background subagent completes.
10. `list_subagents()`: Lists all active and finished background tasks.
11. `record_memory(key, value)`: Stores persistent architectural decisions across turns.
12. `read_memory()`: Reads persistent session memories for active workspace.
13. `retrieve_cached_content(log_id, start_line, end_line)`: Content-Centric Representation log reader.
14. `search_mcp_servers(query, category)`: Instant search across 4,234 MCP servers.
15. `extract_media_info(url, extract_subtitles)`: Metadata, chapters, and subtitles via yt-dlp.
16. `run_chrome_devtools(tool_name, args, flags)`: Headless Chrome DevTools CDP command runner.
17. `inspect_url_with_browser(url, take_screenshot, run_lighthouse)`: One-step DOM and console health check.
18. `cloudflare_url_scan(url)`: Scans live web pages for security threats and network structure.
19. `cloudflare_manage_queue(action, queue_name)`: Creates, deletes, or lists Cloudflare Queues.
20. `cloudflare_manage_container(action, container_id)`: Manages Cloudflare container workloads.
21. `create_plan(title, content)`: Generates structured `implementation_plan.md`.
22. `create_walkthrough(title, content)`: Generates detailed `walkthrough.md`.
23. `list_directory(dirpath)`: Recursive directory inspection with file sizes.
24. `deploy_to_pages(project_name, directory)`: Direct deployment to live Cloudflare Pages.
25. `finish(summary)`: Concludes the task once verified working and tested.

---

## 9. Interactive CLI Commands & Workflow

To launch the Saltice agent terminal:
```powershell
cd "d:\USEME FOLDER\ANTIGRAVITY\multi_agent_cli"
python main.py
```

### Essential Slash Commands
* `/mode builder`: Set operating mode to flagship Antigravity autonomous flow.
* `/browser <url>`: Inspect any live web URL or local HTML file in headless Chrome DevTools.
* `/mcp <query>`: Search the 4,234 curated MCP servers by topic or tool name.
* `/compact [instructions]`: Compress multi-turn conversation into executive working memory.
* `/files`: Display the active session file manifest of all created or modified files.
* `/skills [filter]`: Display the interactive skills table with trigger details.
* `/tokens`: Open the live TPM, RPM, and credit balance dashboard.
* `/deploy <file>`: Deploy any generated web app directly to Cloudflare Pages.
* `/help`: Display the complete terminal command reference.

---

## 10. Verification & Quality Assurance Report

All capabilities have been validated across automated test suites:
* `test_chrome_devtools_integration.py`: **PASSED** (MCP config, 7 skills, `browser-agent` subagent, tool execution)
* `test_new_capabilities.py`: **PASSED** (Distillation, SmartCrusher, 4,234 MCP registry, Pi manifest)
* `test_loop_and_context_engineering.py`: **PASSED** (89.7% context compression, loop stall circuit breaker, Caveman Lite)
* `verify_engine_reflection.py`: **PASSED** (Skill query reflection, ECC subagent roles, dev server guardrails)

---
*Report Generated: 2026-09-22 • Saltice Engineering Core*
