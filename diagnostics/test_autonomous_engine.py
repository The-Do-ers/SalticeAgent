import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import ReActAgent

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Test autonomous iterative loop
agent = ReActAgent(mode="groq", caveman_level="full", max_iterations=5)
task = "Create a python file `fib_test.py` that implements `fib(n) -> int`. Then run `python fib_test.py` to verify that `fib(10) == 55` and prints 'FIB_PASS'. Once verified, call finish."
agent.run(task)
