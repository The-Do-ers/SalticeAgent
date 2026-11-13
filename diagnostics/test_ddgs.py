import sys
import json
from ddgs import DDGS

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("Python 3.13 features", max_results=3))
        print("DDGS SUCCESS:", json.dumps(results, indent=2))
except Exception as e:
    print("DDGS ERROR:", e)
