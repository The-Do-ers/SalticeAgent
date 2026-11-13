---
title: System Architecture Overview
type: architecture_blueprint
created_at: 2026-09-16 16:54:38
---

# System Architecture Overview

## System Architecture: Antigravity Autonomous Terminal

`
+-------------------------------------------------------------------------------+
|                      ANTIGRAVITY TERMINAL CODING ASSISTANT                   |
+-------------------------------------------------------------------------------+
        |                                                   |
        v                                                   v
+-----------------------+                         +---------------------+
|      Normal Mode      |                         |  Council Debate /   |
| (Local Solo ReAct)    |                         |  Swarm Committee    |
+-----------------------+                         +---------------------+
        |                                                   |
        +-------------------------+-------------------------+
                                  |
                                  v
+-------------------------------------------------------------------------------+
|                    RATE-LIMIT SHIELD & MULTI-PROVIDER POOL                   |
|  Cloudflare -> Mistral -> OpenRouter -> Groq -> NIM -> Gemini -> Cohere       |
+-------------------------------------------------------------------------------+
        |                         |                         |
        v                         v                         v
+---------------+         +---------------+         +---------------+
|  ReAct Engine |         | Skills System |         |  Artifacts    |
| (Tools/Debug) |         | (Progressive) |         |  (Persisted)  |
+---------------+         +---------------+         +---------------+
`

### Key Subsystems
1. **Dynamic Rate-Limit Shield:** 45-second cooldown on HTTP 429 with zero-interruption failover.
2. **Specialized Skills:** Progressive disclosure runbooks for Git, Testing, Security, Refactoring, and APIs.
3. **Artifact Generator:** Persistent markdown plans, architecture blueprints, and walkthroughs.
4. **Autonomous Web Search:** Multi-source facts, Wikipedia REST, and PyPI lookup.
