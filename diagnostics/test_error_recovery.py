import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import ReActAgent
from tools import write_file

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Create a broken script
write_file("broken_script.py", """
def divide_items(a, b):
    # Bug: missing return or incorrect operator
    return a / b

print(divide_items(10, 0))
""")

agent = ReActAgent(mode="groq", caveman_level="full", max_iterations=5)
task = "The file `broken_script.py` crashes with a ZeroDivisionError when run with `python broken_script.py`. Fix the error so that if `b == 0`, it returns `None` and prints 'DIV_SAFE: None', then re-run to verify it passes without error."
agent.run(task)
