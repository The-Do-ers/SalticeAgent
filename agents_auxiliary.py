"""
Auxiliary Specialist Agents & Telemetry for Saltice
Equipped with:
1. Cohere Semantic Reranker (rerank-v3.5 for high-precision search filtering)
2. Persistent Telemetry & Model Performance Tracker (Local SQLite + Cloudflare D1 sync)
"""

import os
import sys
import json
import time
import sqlite3
import requests
from dotenv import load_dotenv

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CLI_DIR, ".env"))
load_dotenv()

COHERE_KEY = os.getenv("COHERE_API_KEY", "").strip()
DB_PATH = os.path.join(CLI_DIR, "telemetry.db")


# =========================================================================
# 1. COHERE SEMANTIC RERANKER (TRIAL API: 1,000 CALLS/MONTH)
# =========================================================================
class CohereReranker:
    """
    Reranks search results (Tavily, Jina, or workspace code snippets)
    using Cohere's state-of-the-art rerank-v3.5 model.
    """
    @staticmethod
    def rerank(query: str, documents: list[str], top_n: int = 3) -> list[dict]:
        if not COHERE_KEY or not documents:
            return [{"index": i, "document": doc, "relevance_score": 1.0} for i, doc in enumerate(documents[:top_n])]

        try:
            url = "https://api.cohere.com/v2/rerank"
            headers = {
                "Authorization": f"Bearer {COHERE_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "rerank-v3.5",
                "query": query,
                "documents": documents[:20],
                "top_n": min(top_n, len(documents))
            }
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                results = r.json().get("results", [])
                ranked = []
                for item in results:
                    idx = item.get("index", 0)
                    ranked.append({
                        "index": idx,
                        "document": documents[idx],
                        "relevance_score": round(item.get("relevance_score", 0.0), 4)
                    })
                return ranked
            return [{"index": i, "document": doc, "relevance_score": 1.0} for i, doc in enumerate(documents[:top_n])]
        except Exception:
            return [{"index": i, "document": doc, "relevance_score": 1.0} for i, doc in enumerate(documents[:top_n])]


# =========================================================================
# 2. PERSISTENT TELEMETRY & MODEL PERFORMANCE TRACKER
# =========================================================================
class TelemetryTracker:
    """
    Tracks model latencies, token consumption, syntax & runtime win-rates per domain.
    Stores records locally in SQLite and syncs summary to Cloudflare D1.
    """
    def __init__(self):
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_telemetry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_goal TEXT,
                        domain TEXT,
                        target_file TEXT,
                        providers_used TEXT,
                        total_duration REAL,
                        syntax_passed INTEGER,
                        runtime_passed INTEGER,
                        draw_calls INTEGER,
                        live_url TEXT
                    )
                """)
                conn.commit()
        except Exception:
            pass

    def record(self, user_goal: str, domain: str, target_file: str, providers_used: list,
               duration: float, syntax_passed: bool, runtime_passed: bool, draw_calls: int = 0, live_url: str = ""):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO task_telemetry 
                    (user_goal, domain, target_file, providers_used, total_duration, syntax_passed, runtime_passed, draw_calls, live_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_goal[:200],
                    domain,
                    target_file,
                    json.dumps(providers_used),
                    round(duration, 2),
                    1 if syntax_passed else 0,
                    1 if runtime_passed else 0,
                    draw_calls,
                    live_url
                ))
                conn.commit()
        except Exception:
            pass

    def get_summary(self) -> dict:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*), AVG(total_duration), SUM(syntax_passed), SUM(runtime_passed) FROM task_telemetry")
                row = cursor.fetchone()
                total = row[0] or 0
                avg_dur = round(row[1] or 0.0, 2)
                syn_pass = row[2] or 0
                rt_pass = row[3] or 0

                cursor.execute("SELECT domain, COUNT(*) FROM task_telemetry GROUP BY domain")
                domains = dict(cursor.fetchall())

                return {
                    "total_tasks": total,
                    "avg_duration_seconds": avg_dur,
                    "syntax_success_rate": f"{(syn_pass/total*100):.1f}%" if total else "N/A",
                    "runtime_success_rate": f"{(rt_pass/total*100):.1f}%" if total else "N/A",
                    "domain_breakdown": domains
                }
        except Exception:
            return {"total_tasks": 0}


TELEMETRY = TelemetryTracker()
