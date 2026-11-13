"""
End-to-End Integration Test for Saltice Session State Memory & Engine Integration
"""

import os
import sys
import unittest
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_state import SESSION_STATE
from session_manager import SESSION_MANAGER
from tools import set_state, get_state, delete_state, fetch_vector_asset, generate_physics_rig

class TestMemoryIntegration(unittest.TestCase):
    def setUp(self):
        # Reset session and temp
        SESSION_STATE.reset_temp()
        SESSION_STATE.clear_scope("session")

    def test_tools_state_manipulation(self):
        # 1. Test set_state via tool interface
        res = set_state("target_object", "rocket")
        self.assertIn("State updated successfully", res)
        self.assertEqual(SESSION_STATE.get("target_object"), "rocket")

        # 2. Test user-scoped state
        res_u = set_state("user:theme", "aero-frost")
        self.assertIn("State updated successfully", res_u)
        self.assertEqual(SESSION_STATE.get("user:theme"), "aero-frost")

        # 3. Test get_state tool interface
        res_g = get_state("target_object")
        parsed = json.loads(res_g)
        self.assertEqual(parsed.get("target_object"), "rocket")

        # 4. Test get_state for all
        res_all = get_state()
        parsed_all = json.loads(res_all)
        self.assertIn("session", parsed_all)
        self.assertIn("user", parsed_all)

        # 5. Test delete_state tool interface
        res_d = delete_state("target_object")
        self.assertIn("deleted successfully", res_d)
        self.assertIsNone(SESSION_STATE.get("target_object"))

    def test_vector_asset_session_memory_binding(self):
        # When fetch_vector_asset is called, it should record target_object in state
        res_vec = fetch_vector_asset("rocket")
        self.assertEqual(SESSION_STATE.get("target_object"), "rocket")

        # Calling fetch_vector_asset with empty string should retrieve from state
        res_vec2 = fetch_vector_asset("")
        parsed2 = json.loads(res_vec2)
        self.assertEqual(parsed2.get("entity"), "rocket")

    def test_session_manager_state_coordination(self):
        # Start a new session
        sid = SESSION_MANAGER.start_session()
        self.assertEqual(SESSION_STATE.current_session_id, sid)

        # Set session variable
        set_state("project_scope", "aerospace_telemetry")
        self.assertEqual(SESSION_STATE.get("project_scope"), "aerospace_telemetry")

        # Start another session (force_new=True)
        sid2 = SESSION_MANAGER.start_session(force_new=True)
        self.assertEqual(SESSION_STATE.current_session_id, sid2)
        self.assertIsNone(SESSION_STATE.get("project_scope")) # isolated to sid1!

        # Resume first session
        SESSION_MANAGER.load_session(sid)
        self.assertEqual(SESSION_STATE.get("project_scope"), "aerospace_telemetry") # restored!

    def test_engine_tool_dispatch(self):
        from engine import SalticeAntigravityEngine
        engine = SalticeAntigravityEngine(mode="builder")

        # Execute set_state via engine._execute_tool
        out = engine._execute_tool("set_state", {"key": "user:contrast", "value": "ultra-high"})
        self.assertIn("State updated successfully", out)
        self.assertEqual(SESSION_STATE.get("user:contrast"), "ultra-high")

        # Execute get_state via engine._execute_tool
        out_g = engine._execute_tool("get_state", {"key": "user:contrast"})
        self.assertIn("ultra-high", out_g)

if __name__ == "__main__":
    unittest.main()
