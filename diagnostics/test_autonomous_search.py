import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import ReActAgent

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

agent = ReActAgent(mode="groq", caveman_level="full", max_iterations=4)
task = "Search the web for 'FastAPI' using `search_web`. Summarize what FastAPI is in 2 sentences, and save it to `fastapi_summary.txt`. Once saved, finish."
agent.run(task)
