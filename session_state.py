"""
Session State Memory Manager for Saltice
Implements the 4-Tier State Namespace Architecture (Google Agent Development Kit / Enterprise Agent Model):

1. Temporary (`temp:`) - Lifetime: Current turn only. Discarded after invocation.
   Example: temp:step = "validating", temp:last_score = 8
2. Session   (`(none)`) - Lifetime: Current conversation. Persists across turns in this session.
   Example: topic = "spacecraft_simulation", target_object = "rocket", active_palette = "aero-frost"
3. User      (`user:`) - Lifetime: All sessions for this user. Persists across conversations.
   Example: user:theme = "aero-frost", user:contrast = "high", user:code_style = "typescript"
4. App       (`app:`)  - Lifetime: Global for entire workspace/app. Persists project-wide.
   Example: app:api_url = "https://api.iconify.design", app:framework = "html5_canvas"

Key Differentiators from Conversation History:
- History: Text messages (user + agent turns) for LLM context.
- State: Structured dictionary of key-value pairs for programmatic code access, exact variables, and {key} templating.
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

class SessionStateManager:
    def __init__(self, workspace_dir: Optional[str] = None):
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        self.workspace_dir = os.path.abspath(workspace_dir or agent_dir)
        self.saltice_dir = os.path.join(self.workspace_dir, ".saltice")
        self.sessions_dir = os.path.join(self.saltice_dir, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.current_session_id: Optional[str] = None

        # 4 State Namespaces
        self._temp_state: Dict[str, Any] = {}
        self._session_state: Dict[str, Any] = {}
        self._user_state: Dict[str, Any] = {}
        self._app_state: Dict[str, Any] = {}

        # Load global app & user states from disk
        self._load_app_state()
        self._load_user_state()

    # --- Disk Paths ---

    def _get_app_state_path(self) -> str:
        return os.path.join(self.saltice_dir, "app_state.json")

    def _get_user_state_path(self) -> str:
        return os.path.join(self.saltice_dir, "user_state.json")

    def _get_session_state_path(self, session_id: Optional[str] = None) -> str:
        sid = session_id or self.current_session_id or "default"
        return os.path.join(self.sessions_dir, f"{sid}.state.json")

    # --- Persistence Helpers ---

    def _load_app_state(self):
        p = self._get_app_state_path()
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._app_state = json.load(f)
            except Exception:
                self._app_state = {}
        else:
            # Default sensible app configuration
            self._app_state = {
                "app:version": "2.4.0",
                "app:framework": "html5_canvas_glass",
                "app:vector_provider": "iconify_presets"
            }
            self._save_app_state()

    def _save_app_state(self):
        try:
            with open(self._get_app_state_path(), "w", encoding="utf-8") as f:
                json.dump(self._app_state, f, indent=2)
        except Exception:
            pass

    def _load_user_state(self):
        p = self._get_user_state_path()
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._user_state = json.load(f)
            except Exception:
                self._user_state = {}
        else:
            # Default user preferences: Aero-Frost high-contrast glass
            self._user_state = {
                "user:theme": "aero-frost",
                "user:contrast": "high",
                "user:motion_inertia": "spring_damper"
            }
            self._save_user_state()

    def _save_user_state(self):
        try:
            with open(self._get_user_state_path(), "w", encoding="utf-8") as f:
                json.dump(self._user_state, f, indent=2)
        except Exception:
            pass

    def _load_session_state(self):
        if not self.current_session_id:
            return
        p = self._get_session_state_path(self.current_session_id)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._session_state = json.load(f)
            except Exception:
                self._session_state = {}
        else:
            self._session_state = {}

    def _save_session_state(self):
        if not self.current_session_id:
            return
        try:
            with open(self._get_session_state_path(self.current_session_id), "w", encoding="utf-8") as f:
                json.dump(self._session_state, f, indent=2)
        except Exception:
            pass

    # --- Namespace Key Resolution ---

    def _parse_key(self, key: str) -> Tuple[str, str]:
        """
        Parse raw key into (namespace, clean_key).
        Namespaces: 'temp', 'session', 'user', 'app'.
        """
        k = key.strip()
        if k.startswith("temp:"):
            return "temp", k[5:].strip()
        elif k.startswith("user:"):
            return "user", k[5:].strip()
        elif k.startswith("app:"):
            return "app", k[4:].strip()
        elif k.startswith("session:"):
            return "session", k[8:].strip()
        else:
            return "session", k

    # --- Core State Operations ---

    def set(self, key: str, value: Any) -> None:
        """
        Set a state variable in its appropriate namespace.
        - 'temp:step' -> Temporary (turn-only)
        - 'user:theme' -> User-wide (persists across sessions)
        - 'app:url' -> App-wide (persists project-wide)
        - 'target_object' -> Session-level (persists in current session)
        """
        ns, clean_key = self._parse_key(key)
        if ns == "temp":
            self._temp_state[clean_key] = value
        elif ns == "session":
            self._session_state[clean_key] = value
            self._save_session_state()
        elif ns == "user":
            self._user_state[clean_key] = value
            self._save_user_state()
        elif ns == "app":
            self._app_state[clean_key] = value
            self._save_app_state()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a state variable.
        If key includes a prefix ('temp:', 'user:', 'app:', 'session:'), routes directly.
        If key has NO prefix, searches hierarchical fallback:
        1. temp -> 2. session -> 3. user -> 4. app -> default.
        """
        k = key.strip()
        if k.startswith("temp:"):
            return self._temp_state.get(k[5:].strip(), default)
        elif k.startswith("user:"):
            return self._user_state.get(k[5:].strip(), default)
        elif k.startswith("app:"):
            return self._app_state.get(k[4:].strip(), default)
        elif k.startswith("session:"):
            return self._session_state.get(k[8:].strip(), default)

        # Unprefixed lookup: Hierarchical resolution
        if k in self._temp_state:
            return self._temp_state[k]
        if k in self._session_state:
            return self._session_state[k]
        if k in self._user_state:
            return self._user_state[k]
        if k in self._app_state:
            return self._app_state[k]

        return default

    def delete(self, key: str) -> bool:
        """Remove a key from its namespace."""
        ns, clean_key = self._parse_key(key)
        deleted = False
        if ns == "temp" and clean_key in self._temp_state:
            del self._temp_state[clean_key]
            deleted = True
        elif ns == "session" and clean_key in self._session_state:
            del self._session_state[clean_key]
            self._save_session_state()
            deleted = True
        elif ns == "user" and clean_key in self._user_state:
            del self._user_state[clean_key]
            self._save_user_state()
            deleted = True
        elif ns == "app" and clean_key in self._app_state:
            del self._app_state[clean_key]
            self._save_app_state()
            deleted = True
        return deleted

    def reset_temp(self) -> None:
        """Discard turn-level temporary state (called at the beginning or end of every turn invocation)."""
        self._temp_state.clear()

    def clear_scope(self, scope: str = "all") -> None:
        """Clear state for a specific scope ('temp', 'session', 'user', 'app', or 'all')."""
        s = scope.lower().strip()
        if s in ["temp", "all"]:
            self._temp_state.clear()
        if s in ["session", "all"]:
            self._session_state.clear()
            self._save_session_state()
        if s in ["user", "all"]:
            self._user_state.clear()
            self._save_user_state()
        if s in ["app", "all"]:
            self._app_state.clear()
            self._save_app_state()

    def bind_session(self, session_id: str) -> None:
        """Bind state manager to an active session ID and hydrate session state from disk."""
        self.current_session_id = session_id
        self._load_session_state()

    def get_all(self, flatten: bool = True) -> Dict[str, Any]:
        """Return all active state across all 4 namespaces."""
        if not flatten:
            return {
                "temp": dict(self._temp_state),
                "session": dict(self._session_state),
                "user": dict(self._user_state),
                "app": dict(self._app_state)
            }
        flat = {}
        for k, v in self._app_state.items():
            flat[f"app:{k}"] = v
        for k, v in self._user_state.items():
            flat[f"user:{k}"] = v
        for k, v in self._session_state.items():
            flat[k] = v
        for k, v in self._temp_state.items():
            flat[f"temp:{k}"] = v
        return flat

    # --- LLM Prompt Formatting & Templating ---

    def format_for_prompt(self) -> str:
        """
        Format active state into a high-signal, compact markdown block for LLM prompt injection.
        Only displays non-empty namespaces to minimize token consumption.
        """
        sections = []
        if self._app_state:
            items = [f"  * app:{k} = {json.dumps(v)}" for k, v in sorted(self._app_state.items())]
            sections.append("- Global App State (app:*):\n" + "\n".join(items))
        if self._user_state:
            items = [f"  * user:{k} = {json.dumps(v)}" for k, v in sorted(self._user_state.items())]
            sections.append("- User Preferences (user:*):\n" + "\n".join(items))
        if self._session_state:
            items = [f"  * {k} = {json.dumps(v)}" for k, v in sorted(self._session_state.items())]
            sections.append("- Active Session State:\n" + "\n".join(items))
        if self._temp_state:
            items = [f"  * temp:{k} = {json.dumps(v)}" for k, v in sorted(self._temp_state.items())]
            sections.append("- Current Turn State (temp:*):\n" + "\n".join(items))

        if not sections:
            return ""

        return "[STRUCTURED SESSION STATE (Exact Runtime Memory)]:\n" + "\n\n".join(sections)

    def apply_templating(self, template: str) -> str:
        """
        Replace {key}, {user:key}, {app:key}, {temp:key} in text if key exists in state.
        Preserves unmapped brackets (like JSON braces or Python code blocks).
        """
        if not template or "{" not in template:
            return template

        def replacer(match):
            placeholder = match.group(1).strip()
            val = self.get(placeholder)
            if val is not None:
                return str(val)
            return match.group(0)

        # Match single identifier {var_name} or {ns:var_name}
        return re.sub(r'\{([a-zA-Z0-9_:\-]+)\}', replacer, template)


# Global singleton instance
SESSION_STATE = SessionStateManager()
