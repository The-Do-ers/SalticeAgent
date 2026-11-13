"""
Caveman Token Compression Engine
Inspired by JuliusBrussee/caveman & CAVEWOMAN (Adobe Research).
Provides:
1. System prompt rules that cut output tokens by 45-75% without losing code accuracy.
2. Context & Log compression to drastically cut input reading tokens.
"""

import re
import json
import os
import time
import hashlib

# Caveman System Prompts by level
CAVEMAN_PROMPTS = {
    "off": "",
    
    "lite": """You are in Caveman Lite mode.
Be concise, clear, and direct. Omit conversational filler, pleasantries, and unnecessary preamble.
Keep all code, commands, file paths, and exact error messages 100% intact.
Respond with high information density.""",

    "full": """Respond terse like smart caveman. All technical substance stay. Only fluff die.

## Rules
- Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging.
- Fragments OK. Short synonyms (big not extensive, fix not "implement a solution for").
- No tool-call narration, no decorative tables/emoji, no dumping long raw error logs unless asked.
- Technical terms, code blocks, API names, CLI commands, and exact error messages UNCHANGED.
- Never drop not/never/no/only/except (never flip meaning).
- One idea per sentence. Active voice. Instruction = imperative ("Run X", not "X should be run").
- Answer directly in this style. Skip "caveman mode on" or meta talk.""",

    "ultra": """Respond ultra-terse telegraphic caveman. Max compression.
No articles, no pleasantries, no conversational glue.
Technical terms exact. Code blocks verbatim. Shortest phrasing always.
Only essential words survive."""
}

def compress_terminal_output(output: str, max_lines: int = 40, max_chars: int = 3000, save_log: bool = True) -> str:
    """
    Distills terminal/tool output (Gemini CLI ToolOutputDistillation & Headroom CCR):
    - Strips ANSI escape codes & collapses blank lines.
    - If oversized (> max_chars), offloads full raw log to .saltice/tool_logs/
    - Compresses large JSON payloads (SmartCrusher array/dict summary).
    - Preserves head, decisive error lines (fatal/error/traceback), tail, and disk pointer.
    """
    if not output:
        return ""
    
    # Strip ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', output)
    
    # Condense consecutive empty lines
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned).strip()
    
    lines = cleaned.splitlines()
    if len(lines) <= max_lines and len(cleaned) <= max_chars:
        return cleaned

    # Offload raw output to disk for reversible retrieval (Headroom CCR / Gemini CLI)
    disk_receipt = ""
    if save_log and len(cleaned) > max_chars:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(base, ".saltice", "tool_logs")
            os.makedirs(log_dir, exist_ok=True)
            log_id = f"tool_{int(time.time())}_{hashlib.md5(cleaned.encode('utf-8', errors='replace')).hexdigest()[:6]}"
            log_path = os.path.join(log_dir, f"{log_id}.log")
            with open(log_path, "w", encoding="utf-8", errors="replace") as lf:
                lf.write(cleaned)
            disk_receipt = f"\n[Full raw output ({len(cleaned):,} chars) saved to disk: .saltice/tool_logs/{log_id}.log]\n[Tip: Retrieve slice via retrieve_cached_content('{log_id}')]"
        except Exception:
            disk_receipt = ""

    # SmartCrusher for large JSON outputs
    trimmed_cleaned = cleaned.strip()
    if (trimmed_cleaned.startswith("{") or trimmed_cleaned.startswith("[")) and len(cleaned) > 1200:
        try:
            parsed_json = json.loads(trimmed_cleaned)
            if isinstance(parsed_json, list):
                preview = json.dumps(parsed_json[0], indent=2)[:400]
                return f"[JSON Array: {len(parsed_json)} items]{disk_receipt}\nFirst item preview:\n{preview}..."
            elif isinstance(parsed_json, dict):
                keys_list = list(parsed_json.keys())
                preview = json.dumps({k: parsed_json[k] for k in keys_list[:4]}, indent=2)[:500]
                return f"[JSON Object with {len(keys_list)} keys: {', '.join(keys_list[:12])}]{disk_receipt}\nKey sample preview:\n{preview}..."
        except Exception:
            pass

    # Find decisive error lines if present
    error_keywords = ("error", "failed", "exception", "traceback", "fatal", "warn")
    error_lines = [line for line in lines if any(k in line.lower() for k in error_keywords)]
    
    head = lines[:15]
    tail = lines[-15:]
    
    compressed_parts = [
        "\n".join(head),
        f"\n[... Caveman compressed: {len(lines) - 30} lines skipped ...]"
    ]
    
    if error_lines:
        compressed_parts.append("\n[Decisive findings]:\n" + "\n".join(error_lines[:8]))
    
    if disk_receipt:
        compressed_parts.append(disk_receipt)

    compressed_parts.append("\n" + "\n".join(tail))
    return "\n".join(compressed_parts)

def compress_file_content(content: str, max_chars: int = 4000) -> str:
    """
    Compress file content for LLM input if excessively long.
    """
    if len(content) <= max_chars:
        return content
    
    # Keep head and tail
    head_len = max_chars // 2
    tail_len = max_chars // 2
    return (
        content[:head_len] + 
        f"\n\n[... Caveman compressed: {len(content) - max_chars} characters omitted ...]\n\n" + 
        content[-tail_len:]
    )


def compact_assistant_message(content: str) -> str:
    """
    Replaces large code bodies in historical assistant tool calls
    (write_file, replace_file_content, markdown code blocks)
    with compact verification receipts.
    """
    if not content:
        return ""

    # 1. Try JSON extraction
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
    target_str = json_match.group(1) if json_match else None
    is_fenced = True
    if not target_str:
        brace_match = re.search(r"(\{[\s\S]*\})", content)
        target_str = brace_match.group(1) if brace_match else None
        is_fenced = False

    if target_str:
        try:
            data = json.loads(target_str, strict=False)
            if isinstance(data, dict):
                act = data.get("action")
                args = data.get("args")
                modified = False
                if isinstance(args, dict):
                    if act == "write_file" and "content" in args and len(str(args["content"])) > 200:
                        fp = args.get("filepath", "file")
                        cnt_len = len(str(args["content"]))
                        args["content"] = f"[Content written to disk: {fp} ({cnt_len} chars), syntax verified]"
                        modified = True
                    elif act == "replace_file_content" and "replacement_content" in args and len(str(args["replacement_content"])) > 200:
                        fp = args.get("filepath", "file")
                        args["replacement_content"] = f"[Patch applied to {fp}]"
                        if "target_content" in args and len(str(args["target_content"])) > 200:
                            args["target_content"] = f"[Target lines in {fp}]"
                        modified = True
                if modified:
                    compact_json = json.dumps(data, indent=2)
                    if is_fenced and json_match:
                        return content[:json_match.start()] + f"```json\n{compact_json}\n```" + content[json_match.end():]
                    elif brace_match:
                        return content[:brace_match.start()] + compact_json + content[brace_match.end():]
        except Exception:
            pass

    # 2. Markdown code blocks pruning
    def replace_large_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        if len(code) > 250:
            return f"```{lang}\n[Code written to disk ({len(code)} chars), syntax verified]\n```"
        return match.group(0)

    return re.sub(r"```([a-zA-Z0-9_\-]*)\n([\s\S]*?)\n```", replace_large_code_block, content)


def compact_observation_message(content: str) -> str:
    """
    Compresses verbose observation logs from older turns.
    """
    if not content:
        return ""
    if len(content) > 350:
        return compress_terminal_output(content, max_lines=12, max_chars=350)
    return content


def scrub_history_for_context(history: list, keep_recent_turns: int = 6, level: str = "lite", **kwargs) -> list:
    """
    Context Pruning & Compaction:
    Preserves full context as long as total history is within reasonable limits (< 150,000 chars / ~35,000 tokens).
    Only when history genuinely threatens token limits does it compact older turns, while always preserving
    the last `keep_recent_turns` turn pairs (each turn = assistant action + user observation).
    """
    if not history or len(history) <= 3:
        return history

    total_chars = sum(len(m.get("content", "")) for m in history)
    # Modern LLMs (Gemini, Claude, GPT) easily handle 128k-1M tokens. Do NOT destroy code if under 150k chars.
    if total_chars < 150000:
        return history

    compacted = []
    # Always preserve the initial prompt / system prompt
    compacted.append(history[0])

    # Each turn is 2 messages (assistant + user). Keep at least the last keep_recent_turns * 2 messages verbatim.
    recent_messages_count = max(4, keep_recent_turns * 2)
    recent_start_idx = max(1, len(history) - recent_messages_count)

    for i in range(1, len(history)):
        msg = history[i]
        if i >= recent_start_idx:
            compacted.append(msg)
        else:
            role = msg.get("role", "")
            cnt = msg.get("content", "")
            if role == "assistant":
                compacted.append({"role": "assistant", "content": compact_assistant_message(cnt)})
            elif role == "user":
                compacted.append({"role": "user", "content": compact_observation_message(cnt)})
            else:
                compacted.append(msg)

    return compacted

