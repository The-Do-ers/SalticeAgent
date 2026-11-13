"""
Test suite for Saltice SessionStateManager (4-Tier Memory Architecture)
"""

import os
import sys
import unittest

# Ensure SalticeAgent is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_state import SessionStateManager

class TestSessionStateManager(unittest.TestCase):
    def setUp(self):
        # Create a fresh isolated manager in a temporary test dir
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".test_saltice")
        self.mgr = SessionStateManager(workspace_dir=test_dir)
        self.mgr.clear_scope("all")
        self.mgr.bind_session("test_session_001")

    def tearDown(self):
        self.mgr.clear_scope("all")

    def test_namespace_routing_and_lifetimes(self):
        # 1. Turn-level Temporary State (temp:)
        self.mgr.set("temp:step", "validating")
        self.assertEqual(self.mgr.get("temp:step"), "validating")
        self.assertEqual(self.mgr.get("step"), "validating") # Unprefixed resolution

        # 2. Session-level State (none)
        self.mgr.set("target_object", "rocket")
        self.assertEqual(self.mgr.get("target_object"), "rocket")

        # 3. User-level State (user:)
        self.mgr.set("user:theme", "aero-frost")
        self.assertEqual(self.mgr.get("user:theme"), "aero-frost")
        self.assertEqual(self.mgr.get("theme"), "aero-frost")

        # 4. App-level State (app:)
        self.mgr.set("app:api_url", "https://api.iconify.design")
        self.assertEqual(self.mgr.get("app:api_url"), "https://api.iconify.design")
        self.assertEqual(self.mgr.get("api_url"), "https://api.iconify.design")

    def test_temp_reset(self):
        self.mgr.set("temp:step", "code_generation")
        self.mgr.set("target_object", "airplane")
        self.assertEqual(self.mgr.get("temp:step"), "code_generation")

        # Reset temp (simulating end of turn)
        self.mgr.reset_temp()
        self.assertIsNone(self.mgr.get("temp:step"))
        # Session state must remain untouched
        self.assertEqual(self.mgr.get("target_object"), "airplane")

    def test_session_persistence_and_resumption(self):
        self.mgr.set("target_object", "drone")
        self.mgr.set("motion_rig", "spring_follower")

        # Create a new instance binding to the same session
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".test_saltice")
        mgr2 = SessionStateManager(workspace_dir=test_dir)
        mgr2.bind_session("test_session_001")

        self.assertEqual(mgr2.get("target_object"), "drone")
        self.assertEqual(mgr2.get("motion_rig"), "spring_follower")

    def test_templating_expansion(self):
        self.mgr.set("target_object", "spacecraft")
        self.mgr.set("user:theme", "cyber-obsidian")

        template_str = "Build a {target_object} styled with {user:theme} and JSON {\"action\": \"run\"}."
        expanded = self.mgr.apply_templating(template_str)
        self.assertEqual(expanded, "Build a spacecraft styled with cyber-obsidian and JSON {\"action\": \"run\"}.")

    def test_prompt_formatting(self):
        self.mgr.set("app:framework", "html5_canvas")
        self.mgr.set("user:theme", "aero-frost")
        self.mgr.set("target_object", "rocket")
        self.mgr.set("temp:step", "verifying")

        prompt_block = self.mgr.format_for_prompt()
        self.assertIn("[STRUCTURED SESSION STATE (Exact Runtime Memory)]:", prompt_block)
        self.assertIn("app:framework", prompt_block)
        self.assertIn("user:theme", prompt_block)
        self.assertIn("target_object", prompt_block)
        self.assertIn("temp:step", prompt_block)

if __name__ == "__main__":
    unittest.main()
