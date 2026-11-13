import os
import sys

# Ensure SalticeAgent directory is in sys.path regardless of execution context
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)
