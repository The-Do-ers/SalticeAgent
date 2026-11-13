"""
End-to-End Test for Multi-Agent Workflow
Executes:
1. Architect (Gemini 3.6 Flash)
2. Coder (Groq Qwen 3.8 27B)
3. Reviewer (NVIDIA NIM Llama 3.2 11B)
4. Executor (Tool caller executing Python verification)
"""

import sys
from workflow import MultiAgentWorkflow

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_e2e_test():
    wf = MultiAgentWorkflow(caveman_level="full")
    prompt = "Create a python CLI tool in file `calculator_cli.py` that supports add, subtract, multiply, and divide with command line arguments using argparse, and include a self-test when run with --test."
    wf.run_task(prompt, auto_execute=True)

if __name__ == "__main__":
    run_e2e_test()
