#!/usr/bin/env python3
"""
Saltice Autonomous Agent Web UI Server
Provides a local HTTP REST API & serves the Glassy Chat Interface.
Zero external pip dependencies: built on Python standard library http.server & threading.
"""

import os
import sys
import json
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

# Ensure SalticeAgent directory is in sys.path
AGENT_DIR = Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from session_manager import SESSION_MANAGER
from engine import SalticeAntigravityEngine
from tools import get_workspace_summary
from context_manager import CONTEXT_MANAGER
from agents_auxiliary import TELEMETRY
try:
    from ui_validator import UI_VALIDATOR
except ImportError:
    UI_VALIDATOR = None

try:
    from vector_intelligence import get_vector_status as _vec_status_fn, index_workspace_async as _vec_index_ws
    _VEC_UI_OK = True
except ImportError:
    _VEC_UI_OK = False

WEB_UI_DIR = AGENT_DIR / "web_ui"
DEFAULT_PORT = 54321

# In-memory execution event buffers and active session tracker
SESSION_LIVE_EVENTS = {}
ACTIVE_SESSIONS = set()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

class SalticeAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress routine GET logging to keep console clean
        if "GET /api/" in format % args or "GET /static/" in format % args or "GET / " in format % args:
            return
        super().log_message(format, *args)

    def _send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content, status_code=200):
        body = html_content.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. API: List sessions
        if path == "/api/sessions":
            sessions = SESSION_MANAGER.list_sessions()
            return self._send_json({"status": "ok", "sessions": sessions})

        # 2. API: Current Workspace state
        elif path == "/api/workspace":
            cwd = os.getcwd()
            files = []
            try:
                for entry in os.scandir(cwd):
                    if not entry.name.startswith((".", "__pycache__", "node_modules")):
                        files.append({
                            "name": entry.name,
                            "is_dir": entry.is_dir(),
                            "size": entry.stat().st_size if entry.is_file() else 0
                        })
            except Exception:
                pass
            return self._send_json({
                "status": "ok",
                "workspace": cwd,
                "current_session_id": SESSION_MANAGER.current_session_id,
                "files_count": len(files),
                "files": files[:30]
            })

        # 3. API: Get details for specific session: /api/sessions/<session_id>
        elif path.startswith("/api/sessions/"):
            session_id = path.replace("/api/sessions/", "").strip()
            if session_id:
                try:
                    details = SESSION_MANAGER.get_session_details(session_id)
                    return self._send_json({"status": "ok", "session": details})
                except Exception as e:
                    return self._send_json({"status": "error", "message": str(e)}, status_code=404)

        # 4. API: Live execution events stream for active session
        elif path == "/api/live" or "/live" in path:
            sid = ""
            if "session_id=" in self.path:
                qs = urllib.parse.parse_qs(parsed.query)
                sid = qs.get("session_id", [""])[0]
            elif path.startswith("/api/session/"):
                parts = path.split("/")
                if len(parts) >= 4 and parts[1] == "api" and parts[2] == "session":
                    sid = parts[3]
            if not sid:
                sid = SESSION_MANAGER.current_session_id
            events = SESSION_LIVE_EVENTS.get(sid, [])
            return self._send_json({
                "status": "ok",
                "session_id": sid,
                "is_running": sid in ACTIVE_SESSIONS,
                "events_count": len(events),
                "events": events
            })

        # 5. API: Anti-patterns / negative feedback constraints
        elif path == "/api/anti_patterns":
            return self._send_json({
                "status": "ok",
                "anti_patterns": CONTEXT_MANAGER.anti_patterns,
                "active_count": len([p for p in CONTEXT_MANAGER.anti_patterns if p.get("active", True)])
            })

        # 6. API: SQLite Telemetry summary
        elif path == "/api/telemetry":
            summary = TELEMETRY.get_summary()
            browser_name = "None"
            if UI_VALIDATOR and UI_VALIDATOR.browser_path:
                browser_name = os.path.basename(UI_VALIDATOR.browser_path)
            return self._send_json({
                "status": "ok",
                "telemetry": summary,
                "browser": browser_name,
                "active_constraints_count": len([p for p in CONTEXT_MANAGER.anti_patterns if p.get("active", True)]),
                "workspace": os.getcwd()
            })

        # 7. API: Vector Intelligence status
        elif path == "/api/vector/status":
            if _VEC_UI_OK:
                status = _vec_status_fn()
                return self._send_json({"status": "ok", "vector": status})
            else:
                return self._send_json({
                    "status": "unavailable",
                    "message": "LangChain/FAISS not installed. Run: pip install langchain langchain-community langchain-google-genai faiss-cpu"
                })

        # 7. Web UI Root
        elif path == "/" or path == "/index.html":
            index_file = WEB_UI_DIR / "index.html"
            if index_file.is_file():
                with open(index_file, "r", encoding="utf-8") as f:
                    return self._send_html(f.read())
            else:
                return self._send_html("<h1>Saltice UI: index.html not found.</h1>", status_code=404)

        # Static assets
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Parse request body
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

        # 1. API: Start New Session
        if path == "/api/sessions/new":
            new_id = SESSION_MANAGER.start_session()
            return self._send_json({"status": "ok", "session_id": new_id})

        # 2. API: Switch Workspace Directory
        elif path == "/api/workspace/set":
            new_dir = body.get("workspace", "").strip()
            if new_dir and os.path.isdir(new_dir):
                try:
                    os.chdir(new_dir)
                    SESSION_MANAGER.workspace_dir = os.path.abspath(new_dir)
                    return self._send_json({"status": "ok", "workspace": os.getcwd()})
                except Exception as e:
                    return self._send_json({"status": "error", "message": str(e)}, status_code=400)
            return self._send_json({"status": "error", "message": "Invalid directory path"}, status_code=400)

        # 3. API: Delete Session
        elif path == "/api/sessions/delete":
            target_id = body.get("session_id", "").strip()
            if target_id:
                ok = SESSION_MANAGER.delete_session(target_id)
                return self._send_json({"status": "ok" if ok else "error"})
            return self._send_json({"status": "error", "message": "Missing session_id"}, status_code=400)

        # 4. API: Execute Chat Turn
        elif path == "/api/chat":
            message = body.get("message", "").strip()
            session_id = body.get("session_id", "").strip()
            mode = body.get("mode", "builder").strip().lower()
            caveman = body.get("caveman", "lite").strip().lower()
            iterations = int(body.get("iterations", 0))

            if not message:
                return self._send_json({"status": "error", "message": "Message cannot be empty."}, status_code=400)

            # Ensure session loaded
            if session_id:
                try:
                    if SESSION_MANAGER.current_session_id != session_id:
                        SESSION_MANAGER.load_session(session_id)
                except Exception:
                    SESSION_MANAGER.start_session()
            else:
                session_id = SESSION_MANAGER.current_session_id

            # Initialize live events buffer for this session
            SESSION_LIVE_EVENTS[session_id] = []
            ACTIVE_SESSIONS.add(session_id)

            def event_callback(event_type: str, data: dict):
                events_list = SESSION_LIVE_EVENTS.setdefault(session_id, [])
                events_list.append(data)
                if len(events_list) > 60:
                    SESSION_LIVE_EVENTS[session_id] = events_list[-60:]

            # Execute Saltice Engine Turn
            start_time = time.time()
            try:
                engine = SalticeAntigravityEngine(mode=mode, caveman_level=caveman, max_iterations=iterations, event_callback=event_callback)
                session_history = SESSION_MANAGER.get_session_history_list()
                
                # Run the autonomous ReAct cycle
                summary = engine.run(message, session_context=session_history, event_callback=event_callback)
                t_files = list(getattr(engine, "touched_files", []))
                duration = time.time() - start_time
                
                # Persist turn to disk immediately
                target_file = getattr(engine, "active_target_file", None)
                turn_record = SESSION_MANAGER.record_turn(
                    user_goal=message,
                    target_file=target_file,
                    summary=summary or "Turn completed.",
                    touched_files=t_files
                )

                # Record to SQLite Telemetry
                try:
                    TELEMETRY.record(
                        user_goal=message,
                        domain="web_ui",
                        target_file=target_file or "workspace",
                        providers_used=[mode],
                        duration=duration,
                        syntax_passed=True,
                        runtime_passed=True
                    )
                except Exception:
                    pass

                return self._send_json({
                    "status": "ok",
                    "session_id": SESSION_MANAGER.current_session_id,
                    "summary": summary,
                    "target_file": target_file,
                    "touched_files": t_files,
                    "turn": turn_record,
                    "events": SESSION_LIVE_EVENTS.get(session_id, [])
                })

            except Exception as e:
                return self._send_json({
                    "status": "error",
                    "message": str(e)
                }, status_code=500)
            finally:
                ACTIVE_SESSIONS.discard(session_id)

        # 5. API: Submit Negative / Positive Feedback & Reinforce Anti-Patterns
        elif path == "/api/feedback":
            rating = body.get("rating", "negative").lower()
            tag = body.get("tag", "General Feedback").strip()
            custom_note = body.get("custom_note", "").strip()
            constraint_text = body.get("constraint", "").strip()
            
            if not constraint_text:
                if custom_note:
                    constraint_text = f"User feedback: {custom_note}"
                elif tag == "Bland / Non-Glassy UI":
                    constraint_text = "Never output flat unstyled white backgrounds or generic cards. Always deliver modern Glassmorphism (backdrop-filter: blur(20px), translucent obsidian rgba(18, 18, 22, 0.75), subtle neon glow, 1px specular borders)."
                elif tag == "Placeholder / Truncated Code":
                    constraint_text = "Never write placeholder comments (e.g. '/* TODO: add full logic here */') or truncate code with '...'. Always provide 100% complete, runnable code."
                elif tag == "Duplicate / Wrong File":
                    constraint_text = "Never create duplicate files or wipe working functionality. Modify existing files surgically using replace_file_content."
                elif tag == "Broken JavaScript / Script Error":
                    constraint_text = "Ensure all JavaScript code is 100% syntactically valid and tested. Do not reference undefined variables or missing DOM elements."
                else:
                    constraint_text = f"Avoid: {tag}. Follow user preferences strictly."

            if rating == "negative":
                entry = CONTEXT_MANAGER.record_anti_pattern(tag=tag, constraint=constraint_text, source="user_negative_feedback")
                return self._send_json({
                    "status": "ok",
                    "action": "constraint_recorded",
                    "entry": entry,
                    "active_constraints": CONTEXT_MANAGER.anti_patterns
                })
            else:
                return self._send_json({
                    "status": "ok",
                    "action": "positive_feedback_logged"
                })

        # 6. API: Toggle Anti-Pattern Active Status
        elif path == "/api/anti_patterns/toggle":
            pid = body.get("id", "")
            active = bool(body.get("active", True))
            ok = CONTEXT_MANAGER.toggle_anti_pattern(pid, active)
            return self._send_json({"status": "ok" if ok else "error"})

        # 7. API: Delete Anti-Pattern
        elif path == "/api/anti_patterns/delete":
            pid = body.get("id", "")
            ok = CONTEXT_MANAGER.delete_anti_pattern(pid)
            return self._send_json({"status": "ok" if ok else "error"})

        else:
            self.send_response(404)
            self.end_headers()

def start_ui_server(port=DEFAULT_PORT, auto_open=True):
    """Start the Saltice Web UI server and launch the default browser."""
    # Find next available port if port is taken
    chosen_port = port
    for p in range(port, port + 10):
        try:
            server = ThreadedHTTPServer(("127.0.0.1", p), SalticeAPIHandler)
            chosen_port = p
            break
        except OSError:
            continue
    else:
        server = ThreadedHTTPServer(("127.0.0.1", 0), SalticeAPIHandler)
        chosen_port = server.server_address[1]

    url = f"http://localhost:{chosen_port}"
    print(f"\n⚡ Saltice Autonomous UI Server Active: {url}")
    print(f"📂 Workspace: {os.getcwd()}")
    print("Press Ctrl+C in this terminal to stop the server.\n")

    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Saltice UI server.")
        server.server_close()

if __name__ == "__main__":
    start_ui_server()
