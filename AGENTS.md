# AGENTS.md - Saltice Autonomous Project Conventions & Directives

Welcome to the Saltice project repository. All autonomous agents (Saltice, Antigravity, Cline, Grok, Claude Code, ECC) operating in this workspace must strictly follow these instructions.

## 1. Project Architecture & Standards
- **Global CLI Command**: Type `saltice` in any terminal or directory on Windows to launch immediately.
- **Core Engine**: Located in `SalticeAgent/` (with backward-compatible proxy in `multi_agent_cli/`). Powered by `SalticeAntigravityEngine` with dual-mode parsing (JSON + resilient Markdown block recovery).
- **Asynchronous Subagents**: Managed via `subagents.py`. Use `spawn_subagent` for parallel research or sub-tasks, and inspect with `check_subagent_status`.
- **Modular Skills**: 600+ specialized skills indexed from `SalticeAgent/.agents/skills/`, `.repo_cache/` (ECC, Claude-Skills, Karpathy-Skills, Academic-Research-Skills), and system plugins.
- **Rules & Conventions**: Automatically discovered from this `AGENTS.md` and any `.grok/rules/` or `.claude/rules/`.

## 2. Engineering Operating System (ECC Flow)
Follow the canonical engineering lifecycle:
```text
plan -> test -> implement -> review -> verify -> remember -> improve
```
- **Plan Before Execution**: For non-trivial tasks, generate `implementation_plan.md` first.
- **Test-Driven Verification**: Write verification tests or non-blocking build checks before calling finish.
- **Self-Review**: Inspect changes before declaring completion.
- **Memory & Continuous Learning**: Persist key decisions via `record_memory`.

## 3. Andrej Karpathy's 4 Pillars
1. **Think Before Coding**: Don't assume. Surface tradeoffs. State assumptions explicitly. If uncertain or ambiguous, clarify before executing.
2. **Simplicity First**: Minimum code that solves the problem. Nothing speculative. No single-use abstractions or unneeded configurability.
3. **Surgical Changes**: Touch only what you must. Match existing style. Clean up your own orphans. Every changed line must trace directly to the goal.
4. **Goal-Driven Execution**: Define verifiable success criteria. Loop until verified.

## 4. Critical Execution Rules
1. **NO BLOCKING DEV SERVERS**:
   - DO NOT run `npx vite`, `npm run dev`, `npm start`, or any blocking HTTP server using `run_command`. These processes run forever and will hang the agent loop.
   - ALWAYS verify web apps using non-blocking compilation checks:
     ```powershell
     npm run build
     # or
     npx tsc --noEmit
     ```
   - Then complete the turn and instruct the user to run `npm run dev` in their external terminal.

2. **PREVENT WHITE SCREENS & HOLLOW STUBS**:
   - Every single generated file must be 100% complete.
   - Never use placeholder comments like `/* TODO: add full logic here */` or `...`.
   - Ensure all script tags, module imports, and stylesheets are properly referenced and closed.

3. **CREATIVE AWARDS-GRADE UI & MOTION (GSAP, LENIS, REACT BITS, KOKONUT UI)**:
   - DO NOT force generic frosted glass boxes or dark-on-dark rounded squares everywhere.
   - Deliver modern, high-end, responsive web designs inspired by creative agency & Awwwards-grade experiences:
     - Ultra-smooth inertial scrolling with **Lenis**.
     - Kinetic typography, timeline animations, and scroll-driven scrubbing with **GSAP & ScrollTrigger**.
     - Rich micro-interactions and interactive components from **React Bits** (magnetic buttons, spotlight cards, particle backgrounds, text decrypters) and **Kokonut UI**.
     - Sharp visual hierarchy, authentic contrast, and purposeful typography.

4. **LIVING DOCUMENTATION TRIPLE-PACK**:
   - On major projects or multi-file applications, ensure the triple-pack is generated:
     - `implementation_plan.md`: Comprehensive breakdown of architecture, design choices, and verification.
     - `walkthrough.md`: Detailed usage guide, testing checklist, and run instructions.
     - `README.md`: Quickstart and project summary.

5. **ANTI-REGRESSION DIRECTIVE**:
   - When modifying an existing file, NEVER wipe working functionality.
   - Use `replace_file_content` for surgical line edits instead of rewriting entire multi-hundred line files.

6. **STRICT TEST WORKSPACE CONFINEMENT**:
   - ALL test runs, scratch prototypes, verification captures, and experiment websites MUST be created strictly within `SalticeAgent/tests/<test_name>/`.
   - NEVER vomit test files, loose verification PNGs, or experimental HTML files into the root workspace or SalticeAgent root directory. Keep root directories pristine.

7. **ITERATIVE PART-BY-PART CONSTRUCTION (ZERO MONOLITHIC DUMPS)**:
   - For applications with rich motion, canvas, or 10+ components, NEVER attempt to write 1,500+ lines in a single turn. Monolithic dumps exceed output token caps and lead to parser bleed or truncated code.
   - Stage 1: Skeleton, layouts, CSS variables, typography tokens.
   - Stage 2: Components, cards, bento grids, navigation markup.
   - Stage 3: GSAP timelines, Lenis smooth scroll, Web Audio API, canvas event listeners.
   - Stage 4: Real browser verification (`verify_with_real_browser`) and surgical self-healing.


