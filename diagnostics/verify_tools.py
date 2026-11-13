import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import search_web, fetch_webpage, run_command

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== 1. Web Search Test ===")
res = search_web("FastAPI python framework")
print(res[:300])

print("\n=== 2. Command Success Test ===")
print(run_command("python --version"))

print("\n=== 3. Error Capture Test ===")
print(run_command("python -c \"import non_existent_pkg\""))
