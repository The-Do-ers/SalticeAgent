"""
Session and Conversational Memory Manager for Saltice
Inspired by Antigravity, Claude Code, Cline, and Aider conversation architectures.

Features:
- Real-time disk persistence in .saltice/sessions/<session_id>.jsonl
- Master session index in .saltice/sessions/index.json
- Session resumption (/resume <session_id>), session listing (/sessions), and new sessions (/new)
- Sliding-window context compaction: keeps recent turns in full fidelity while
  distilling older turns into a dense chronological memory ledger.
- Zero data loss: every turn, thought, tool call, and touched file is flushed to disk immediately.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from session_state import SESSION_STATE

class SessionManager:
    def __init__(self, workspace_dir: Optional[str] = None):
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        self.workspace_dir = os.path.abspath(workspace_dir or agent_dir)
        self.saltice_dir = os.path.join(self.workspace_dir, ".saltice")
        self.sessions_dir = os.path.join(self.saltice_dir, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        self.current_session_id: Optional[str] = None
        self.current_turns: List[Dict[str, Any]] = []
        self.session_metadata: Dict[str, Any] = {}
        
        # Start or resume current session
        self.start_session()

    def _generate_session_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        rand_suffix = uuid.uuid4().hex[:6]
        return f"session_{date_str}_{rand_suffix}"

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.sessions_dir, f"{session_id}.jsonl")

    def _get_index_path(self) -> str:
        return os.path.join(self.sessions_dir, "index.json")

    def _load_index(self) -> Dict[str, Any]:
        idx_p = self._get_index_path()
        if os.path.isfile(idx_p):
            try:
                with open(idx_p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self, index_data: Dict[str, Any]):
        idx_p = self._get_index_path()
        try:
            with open(idx_p, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception:
            pass

    def start_session(self, session_id: Optional[str] = None, force_new: bool = False) -> str:
        """Start a new session or load an existing session."""
        if session_id:
            return self.load_session(session_id)

        # If current session already exists with 0 turns, reuse it unless force_new=True
        if not force_new and self.current_session_id and len(self.current_turns) == 0:
            return self.current_session_id

        self.current_session_id = self._generate_session_id()
        self.current_turns = []
        self.session_metadata = {
            "session_id": self.current_session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "workspace": self.workspace_dir,
            "total_turns": 0,
            "deliverables": [],
            "touched_files": []
        }
        
        # Register in index
        index = self._load_index()
        index[self.current_session_id] = {
            "session_id": self.current_session_id,
            "created_at": self.session_metadata["created_at"],
            "first_goal": "",
            "turns": 0,
            "last_active": self.session_metadata["updated_at"],
            "workspace": self.session_metadata.get("workspace", self.workspace_dir)
        }
        self._save_index(index)

        # Initialize session transcript on disk immediately
        target_path = self._get_session_path(self.current_session_id)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"type": "session_meta", "data": self.session_metadata}) + "\n")
        except Exception:
            pass

        # Hydrate session state memory
        SESSION_STATE.bind_session(self.current_session_id)

        return self.current_session_id

    def load_session(self, session_id: str) -> str:
        """Load an existing session transcript from disk."""
        target_path = self._get_session_path(session_id)
        if not os.path.isfile(target_path):
            index = self._load_index()
            if session_id in index:
                meta = {
                    "session_id": session_id,
                    "created_at": index[session_id].get("created_at", datetime.now().isoformat()),
                    "updated_at": index[session_id].get("last_active", datetime.now().isoformat()),
                    "workspace": index[session_id].get("workspace", self.workspace_dir),
                    "total_turns": 0,
                    "deliverables": [],
                    "touched_files": []
                }
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps({"type": "session_meta", "data": meta}) + "\n")
                except Exception:
                    pass
            else:
                raise FileNotFoundError(f"Session transcript not found: {session_id}")

        self.current_session_id = session_id
        self.current_turns = []
        all_touched = set()
        deliverables = []

        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("type") == "session_meta":
                        self.session_metadata = record.get("data", {})
                    elif record.get("type") == "turn":
                        t_data = record.get("data", {})
                        self.current_turns.append(t_data)
                        for tf in t_data.get("touched_files", []):
                            all_touched.add(tf)
                        if t_data.get("target_file"):
                            deliverables.append(t_data.get("target_file"))
                except Exception:
                    pass

        self.session_metadata["session_id"] = session_id
        self.session_metadata["total_turns"] = len(self.current_turns)
        self.session_metadata["touched_files"] = list(all_touched)
        self.session_metadata["deliverables"] = deliverables

        # Hydrate session state memory
        SESSION_STATE.bind_session(session_id)

        return session_id

    def record_turn(
        self,
        user_goal: str,
        target_file: Optional[str] = None,
        summary: str = "",
        touched_files: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        thought: str = "",
        token_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record an interactive conversation turn immediately to disk."""
        if not self.current_session_id:
            self.start_session()

        turn_index = len(self.current_turns) + 1
        turn_data = {
            "turn_index": turn_index,
            "timestamp": datetime.now().isoformat(),
            "user_goal": user_goal,
            "target_file": target_file or "",
            "summary": summary,
            "touched_files": list(set(touched_files or [])),
            "tool_calls": tool_calls or [],
            "thought": thought,
            "token_stats": token_stats or {}
        }
        self.current_turns.append(turn_data)

        # Update metadata
        self.session_metadata["updated_at"] = datetime.now().isoformat()
        self.session_metadata["total_turns"] = len(self.current_turns)
        if target_file and target_file not in self.session_metadata.get("deliverables", []):
            self.session_metadata.setdefault("deliverables", []).append(target_file)
        for f in (touched_files or []):
            if f not in self.session_metadata.get("touched_files", []):
                self.session_metadata.setdefault("touched_files", []).append(f)

        # Append to JSONL file on disk
        target_path = self._get_session_path(self.current_session_id)
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "turn", "data": turn_data}) + "\n")

        # Update session index
        index = self._load_index()
        first_goal = index.get(self.current_session_id, {}).get("first_goal") or user_goal[:80]
        index[self.current_session_id] = {
            "session_id": self.current_session_id,
            "created_at": self.session_metadata.get("created_at", datetime.now().isoformat()),
            "first_goal": first_goal,
            "turns": len(self.current_turns),
            "last_active": self.session_metadata["updated_at"],
            "last_deliverable": target_file or "",
            "workspace": self.session_metadata.get("workspace", self.workspace_dir)
        }
        self._save_index(index)

        return turn_data

    def list_sessions(self, include_empty: bool = False) -> List[Dict[str, Any]]:
        """List all saved sessions sorted by most recent first. Filters out 0-turn empty sessions unless active."""
        index = self._load_index()
        sessions = [
            s for s in index.values()
            if include_empty or s.get("turns", 0) > 0 or s.get("session_id") == self.current_session_id
        ]
        sessions.sort(key=lambda s: s.get("last_active", ""), reverse=True)
        return sessions

    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Load and return all turns and metadata for a specific session."""
        self.load_session(session_id)
        return {
            "session_id": self.current_session_id,
            "metadata": self.session_metadata,
            "turns": self.current_turns
        }

    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session transcript from disk and index."""
        try:
            p = self._get_session_path(session_id)
            if os.path.exists(p):
                os.remove(p)
            state_p = os.path.join(self.sessions_dir, f"{session_id}.state.json")
            if os.path.exists(state_p):
                try:
                    os.remove(state_p)
                except Exception:
                    pass
            index = self._load_index()
            if session_id in index:
                del index[session_id]
                self._save_index(index)
            if self.current_session_id == session_id:
                self.start_session()
            return True
        except Exception:
            return False

    def get_context_for_prompt(self, window_size: int = 6) -> str:
        """
        Produce a high-signal conversational memory prompt block.
        - Recent turns (up to window_size) are preserved in detail.
        - Older turns are distilled into a compact chronological state ledger.
        """
        if not self.current_turns:
            return ""

        total = len(self.current_turns)
        lines = [
            f"[CONVERSATIONAL CHAT MEMORY (Session ID: {self.current_session_id} | Total Turns: {total})]:"
        ]

        # 1. Distill older turns if total > window_size
        if total > window_size:
            older_turns = self.current_turns[:-window_size]
            lines.append("--- Chronological Summary of Earlier Turns ---")
            for t in older_turns:
                idx = t.get("turn_index", 0)
                goal_snippet = t.get("user_goal", "")[:60]
                res_snippet = t.get("summary", "")[:70]
                tgt = t.get("target_file", "")
                files = ", ".join(t.get("touched_files", []))
                f_info = f" -> File: {tgt or files}" if (tgt or files) else ""
                lines.append(f"Turn {idx}: \"{goal_snippet}\"{f_info} => {res_snippet}")
            lines.append("-------------------------------------------------")

        # 2. Detailed recent turns
        recent_turns = self.current_turns[-window_size:]
        lines.append("--- Recent Interactive Conversation ---")
        for t in recent_turns:
            idx = t.get("turn_index", 0)
            u_goal = t.get("user_goal", "")
            summary = t.get("summary", "") or "Task completed."
            tgt = t.get("target_file", "")
            touched = ", ".join(t.get("touched_files", []))
            touched_info = f" (Touched: {touched})" if touched else ""
            lines.append(f"Turn {idx}:")
            lines.append(f"  User: \"{u_goal}\"")
            lines.append(f"  Agent Result ({tgt or 'workspace'}{touched_info}): {summary}")

        # 3. Session Cumulative State
        all_touched = self.session_metadata.get("touched_files", [])
        if all_touched:
            lines.append(f"\nSession Files Modified So Far: {', '.join(all_touched[:12])}")

        return "\n".join(lines)

    def get_session_history_list(self) -> List[Dict[str, Any]]:
        """Return the current turns in memory for CLI table rendering."""
        return self.current_turns

SESSION_MANAGER = SessionManager()
