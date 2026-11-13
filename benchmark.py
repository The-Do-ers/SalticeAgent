"""
Multi-Agent Benchmark Suite
Iterates 7 distinct coding challenges comparing Standard vs Caveman (Full) mode.
Measures:
- Latency (seconds)
- Output tokens
- Generation speed (tok/s)
- Token savings (%)
- Code validity (AST parsing)
"""

import os
import sys
import time
import ast
import json
from providers import call_groq, call_nvidia_nim, call_gemini, call_llm
from caveman import CAVEMAN_PROMPTS

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BENCHMARK_TASKS = [
    {
        "name": "Factorial with Memoization",
        "prompt": "Write a Python function `memoized_factorial(n: int) -> int` with input validation and caching."
    },
    {
        "name": "Binary Search Algorithm",
        "prompt": "Implement binary search in Python: `binary_search(arr: list[int], target: int) -> int`."
    },
    {
        "name": "Palindrome Permutation",
        "prompt": "Write a Python function `can_permute_palindrome(s: str) -> bool`."
    },
    {
        "name": "In-Place QuickSort",
        "prompt": "Implement in-place quicksort in Python: `quicksort(arr: list[int], low: int, high: int)`."
    },
    {
        "name": "LRU Cache Data Structure",
        "prompt": "Implement an LRU Cache in Python with `get(key)` and `put(key, value)` in O(1) time."
    }
]

def check_python_syntax(text: str) -> bool:
    """Extract code block and test if it parses with Python ast."""
    import re
    blocks = re.findall(r"```(?:python)?\s*([\s\S]*?)```", text)
    if not blocks:
        # Check if the raw text is python
        code_to_test = text
    else:
        code_to_test = "\n\n".join(blocks)
    
    try:
        ast.parse(code_to_test)
        return True
    except SyntaxError:
        return False

def run_benchmark():
    print("=" * 80)
    print("🚀 STARTING MULTI-AGENT & CAVEMAN BENCHMARK SUITE (7 ITERATIONS)")
    print("=" * 80)

    results = []

    for idx, task in enumerate(BENCHMARK_TASKS, 1):
        print(f"\n--- [Iteration {idx}/7] Task: {task['name']} ---")
        prompt = task["prompt"]

        # Run 1: Standard Mode (Caveman OFF)
        std_messages = [
            {"role": "system", "content": "You are a helpful software engineer. Provide a concise solution."},
            {"role": "user", "content": prompt}
        ]
        t0 = time.time()
        std_res = call_llm(std_messages, preferred_provider="groq", max_tokens=600)
        std_dt = time.time() - t0
        std_tokens = std_res["completion_tokens"]
        std_valid = check_python_syntax(std_res["content"])

        print(f"  [Standard Mode]  Tokens: {std_tokens:4d} | Time: {std_dt:5.2f}s | Speed: {std_res['speed']:5.1f} tok/s | Model: {std_res['model']} | Valid Code: {std_valid}", flush=True)

        # Pace calls to allow free tier OTPM bucket to refill
        time.sleep(10)

        # Run 2: Caveman Mode (Full)
        caveman_system = CAVEMAN_PROMPTS["full"]
        cv_messages = [
            {"role": "system", "content": caveman_system},
            {"role": "user", "content": prompt}
        ]
        t0 = time.time()
        cv_res = call_llm(cv_messages, preferred_provider="groq", max_tokens=600)
        cv_dt = time.time() - t0
        cv_tokens = cv_res["completion_tokens"]
        cv_valid = check_python_syntax(cv_res["content"])

        savings_pct = ((std_tokens - cv_tokens) / std_tokens * 100) if std_tokens > 0 else 0
        speedup = (std_dt / cv_dt) if cv_dt > 0 else 1.0
        print(f"  [Caveman Mode]   Tokens: {cv_tokens:4d} | Time: {cv_dt:5.2f}s | Speed: {cv_res['speed']:5.1f} tok/s | Model: {cv_res['model']} | Valid Code: {cv_valid}", flush=True)
        print(f"  --> Token Reduction: {savings_pct:5.1f}% saved! (Speedup: {speedup:.2f}x faster)", flush=True)

        results.append({
            "iteration": idx,
            "task": task["name"],
            "standard": {
                "tokens": std_tokens,
                "time": round(std_dt, 2),
                "speed": round(std_res["speed"], 1),
                "model": std_res["model"],
                "valid": std_valid
            },
            "caveman": {
                "tokens": cv_tokens,
                "time": round(cv_dt, 2),
                "speed": round(cv_res["speed"], 1),
                "model": cv_res["model"],
                "valid": cv_valid
            },
            "savings_pct": round(savings_pct, 1)
        })



    # Summary Table
    print("\n" + "=" * 80)
    print("📊 BENCHMARK SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Task Name':<28} | {'Std Tok':<7} | {'Cv Tok':<7} | {'Savings':<8} | {'Std Time':<8} | {'Cv Time':<8}")
    print("-" * 80)
    total_std_tok = 0
    total_cv_tok = 0
    total_std_time = 0.0
    total_cv_time = 0.0

    for r in results:
        t_name = r["task"][:27]
        st = r["standard"]["tokens"]
        ct = r["caveman"]["tokens"]
        sav = f"{r['savings_pct']}%"
        st_t = f"{r['standard']['time']}s"
        ct_t = f"{r['caveman']['time']}s"
        total_std_tok += st
        total_cv_tok += ct
        total_std_time += r['standard']['time']
        total_cv_time += r['caveman']['time']
        print(f"{t_name:<28} | {st:<7} | {ct:<7} | {sav:<8} | {st_t:<8} | {ct_t:<8}")

    avg_savings = ((total_std_tok - total_cv_tok) / total_std_tok * 100) if total_std_tok > 0 else 0
    print("-" * 80)
    print(f"{'TOTAL / AVERAGE':<28} | {total_std_tok:<7} | {total_cv_tok:<7} | {avg_savings:.1f}%    | {total_std_time:.2f}s   | {total_cv_time:.2f}s")
    print("=" * 80)

    # Save to json
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tasks": len(results),
        "total_std_tokens": total_std_tok,
        "total_caveman_tokens": total_cv_tok,
        "total_tokens_saved": total_std_tok - total_cv_tok,
        "avg_token_reduction_pct": round(avg_savings, 2),
        "total_standard_time_sec": round(total_std_time, 2),
        "total_caveman_time_sec": round(total_cv_time, 2),
        "speedup_factor": round(total_std_time / total_cv_time, 2) if total_cv_time > 0 else 1.0,
        "details": results
    }
    with open("benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nBenchmark report successfully saved to benchmark_report.json")

if __name__ == "__main__":
    run_benchmark()
