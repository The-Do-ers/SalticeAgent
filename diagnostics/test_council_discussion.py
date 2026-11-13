import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow import MultiAgentWorkflow

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

wf = MultiAgentWorkflow(caveman_level="lite")
topic = "Design and implement a rate-limited queue class in Python that supports max 5 operations per second."
wf.run_discussion(topic, auto_execute=True)
