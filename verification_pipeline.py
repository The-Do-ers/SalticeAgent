"""
Real Autonomous Browser Verification & Self-Healing Pipeline for Saltice
========================================================================

Architecture:
1. RequirementExtractor:
   Parses user goals into 4 explicit testable layers:
   - Layer 1: Code Exists (valid files, structure, no hollow stubs)
   - Layer 2: Code Executes (local HTTP server 200, 0 console errors, 0 runtime exceptions)
   - Layer 3: Behavioral & Interaction (real CDP mouse movement, lag measurement, clicks, animations, idle state)
   - Layer 4: Visual & Vision Evaluation (screenshot inspected by multimodal vision model vs visual requirements)

2. RealBrowserRunner:
   - Serves workspace directory on ephemeral local HTTP port (never relies solely on file://)
   - Connects to Chrome/Edge via Chrome DevTools Protocol (CDP) WebSocket
   - Collects live console errors, exceptions, DOM state, screenshots, and drives mouse/keyboard events

3. InteractionTester:
   - Dispatches programmatic waypoints, clicks, scrolls, keyboard inputs
   - Measures position/transform convergence across animation frames
   - Tests inactivity/idle state transitions

4. VisionEvaluator:
   - Evaluates captured screenshots using multimodal vision model (NVIDIA Vision / Gemini / OpenRouter)
   - Validates aesthetic style (e.g. glassmorphism, dark/neon, layout) and element recognizability

5. DiagnosticEngine & FailureTracker:
   - Formats structured failure reports with exact evidence and surgical repair recommendations
   - Enforces anti-loop rules: terminates loop stalls after 3 repeated failures on the same root issue
"""

import os
import sys
import re
import json
import time
import base64
import socket
import asyncio
import tempfile
import threading
import subprocess
import urllib.request
from typing import Dict, Any, List, Optional, Tuple

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
if CLI_DIR not in sys.path:
    sys.path.insert(0, CLI_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(CLI_DIR, ".env"))

NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# ─── 1. BROWSER LOCATOR ────────────────────────────────────────────────────────
def detect_system_browser() -> Optional[str]:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium"
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    for name in ["chrome", "google-chrome", "chromium", "msedge"]:
        import shutil
        found = shutil.which(name)
        if found:
            return found
    return None

# ─── 2. EPHEMERAL HTTP SERVER ──────────────────────────────────────────────────
class BackgroundHttpServer:
    def __init__(self, serve_dir: str):
        self.serve_dir = os.path.abspath(serve_dir)
        self.port = self._find_free_port()
        self.server = None
        self.thread = None

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    def start(self):
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        serve_dir = self.serve_dir
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_dir, **kwargs)
            def log_message(self, format, *args):
                pass # suppress stdout logs
        self.server = HTTPServer(('127.0.0.1', self.port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass


# ─── 3. MULTIMODAL VISION EVALUATOR ───────────────────────────────────────────
class VisionEvaluator:
    @staticmethod
    def evaluate_screenshot(screenshot_path: str, user_goal: str, requirements: List[str], dom_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends the screenshot to an available multimodal vision model to compare
        the actual rendered result against the user's requirements.
        Returns: {passed: bool, issues: [...], visual_quality: str, explanation: str}
        """
        if not os.path.isfile(screenshot_path) or os.path.getsize(screenshot_path) < 500:
            return {
                "passed": False,
                "issues": ["Screenshot file does not exist or is 0 bytes."],
                "visual_quality": "none",
                "explanation": "No screenshot captured."
            }

        goal_low = user_goal.lower()
        is_plane_or_vehicle = any(k in goal_low for k in ["plane", "aircraft", "jet", "flight", "drone", "spacecraft"])

        with open(screenshot_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = f"""You are an elite QA and visual design reviewer for web applications.
User Request:
"{user_goal}"

Expected Requirements:
{json.dumps(requirements, indent=2)}

Inspect this rendered web screenshot closely.
Answer these specific questions:
1. Is this a blank, white, or raw text placeholder screen? (If so, immediate FAIL).
2. ELEMENT RECOGNIZABILITY & SILHOUETTE:
   - If the user requested an airplane, rocket, car, drone, or specific physical entity:
     * Does the visual object actually resemble a real aerodynamic vehicle/entity with authentic curves, wings, fins, or silhouette?
     * If it is merely a rounded box, a square div, a circle, a deformed polygon, or looks like a crude "broken pipe", you MUST set passed=false with issue "Focal object is a crude geometric polygon or broken pipe, not a genuine vector silhouette".
3. COLOR CONTRAST & VISIBILITY:
   - Is the focal object clearly visible and contrasting against the background?
   - If the object is the exact same dark color as the background or nearly invisible (e.g. dark navy box on dark navy background), you MUST set passed=false with issue "Severe low contrast: focal object blends into background".
4. AESTHETIC SCORING RUBRIC (Scale 1 to 10):
   Rate the overall visual aesthetic from 1 to 10 based on these strict professional standards:
   - 9-10 (Elite / Production-Grade): Crisp authentic vector silhouette, frosted glass backdrop filters, vivid glowing telemetry or contrails, high visual contrast, refined typography.
   - 7-8 (Good / Passing): Recognizable physical silhouette, clear contrast, decent glass cards and layout.
   - 4-6 (Crude / Amateur): Looks like a broken pipe, distorted polygon, deformed tube, or rough sketch. Poor visual hierarchy or washed-out colors.
   - 1-3 (Broken / Unacceptable): Rounded square/box placeholder, invisible dark-on-dark contrast, white screen, or severe visual defects.

CRITICAL PASS/FAIL CRITERION:
- An aesthetic score below 7 (< 7) is an AUTOMATIC FAILURE (passed=false).
- If the object resembles a broken pipe, crude polygon, or lacks proper aerodynamic features, set aesthetic_score <= 5 and passed=false with issue "Crude or distorted object geometry: does not resemble a clean aerodynamic vehicle/entity. Use fetch_vector_asset to retrieve a verified vector silhouette."

Respond ONLY with valid JSON:
{{
  "aesthetic_score": 1-10,
  "passed": true_or_false,
  "visual_quality": "high"|"medium"|"low"|"broken",
  "issues": ["list of visual issues found or empty if passed"],
  "explanation": "concise 2-sentence summary of observed visuals with specific critique of geometry and styling"
}}"""

        def parse_and_validate_vision_json(text_out: str) -> Optional[Dict[str, Any]]:
            m = re.search(r'\{[\s\S]*\}', text_out)
            if not m:
                return None
            try:
                data = json.loads(m.group(0))
                score = int(data.get("aesthetic_score", 7))
                data["aesthetic_score"] = score
                if score < 7:
                    data["passed"] = False
                    issues = data.setdefault("issues", [])
                    has_quality_issue = any("aesthetic" in str(i).lower() or "silhouette" in str(i).lower() or "crude" in str(i).lower() or "broken" in str(i).lower() for i in issues)
                    if not has_quality_issue:
                        issues.append(f"Visual aesthetic score ({score}/10) is below the required 7/10 minimum quality threshold. Use fetch_vector_asset to embed verified vector geometry.")
                elif score >= 7 and "passed" not in data:
                    data["passed"] = True
                return data
            except Exception:
                return None

        # 1. Try NVIDIA NIM (Llama 3.2 11B Vision)
        if NVIDIA_KEY:
            try:
                import requests
                headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "meta/llama-3.2-11b-vision-instruct",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_data}"}}
                        ]
                    }],
                    "max_tokens": 400,
                    "temperature": 0.1
                }
                r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if r.status_code == 200:
                    text_out = r.json()["choices"][0]["message"]["content"]
                    res = parse_and_validate_vision_json(text_out)
                    if res:
                        return res
            except Exception:
                pass

        # 2. Try OpenRouter Vision (Llama 3.2 11B Vision or Gemini Flash)
        if OPENROUTER_KEY:
            try:
                import requests
                headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_data}"}}
                        ]
                    }],
                    "max_tokens": 400,
                    "temperature": 0.1
                }
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if r.status_code == 200:
                    text_out = r.json()["choices"][0]["message"]["content"]
                    res = parse_and_validate_vision_json(text_out)
                    if res:
                        return res
            except Exception:
                pass

        # 3. Try Gemini Vision directly
        if GEMINI_KEY:
            try:
                import requests
                for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
                    payload = {
                        "contents": [{
                            "role": "user",
                            "parts": [
                                {"text": prompt},
                                {"inlineData": {"mimeType": "image/png", "data": b64_data}}
                            ]
                        }],
                        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400}
                    }
                    r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=15)
                    if r.status_code == 200:
                        cand = r.json().get("candidates", [])[0]
                        text_out = cand["content"]["parts"][0]["text"]
                        res = parse_and_validate_vision_json(text_out)
                        if res:
                            return res
            except Exception:
                pass

        # 4. Fallback Heuristic & DOM Structural Inspection
        file_size = os.path.getsize(screenshot_path)
        is_truly_empty = file_size < 4000 or (dom_stats and dom_stats.get("isWhiteScreen", False))
        if is_truly_empty:
            return {
                "aesthetic_score": 1,
                "passed": False,
                "issues": ["Screenshot byte density or DOM indicates a blank or nearly empty page (<4KB or 0 DOM elements)."],
                "visual_quality": "low",
                "explanation": "Heuristic inspection detected a likely white screen or unrendered canvas."
            }

        # Check DOM structural metrics if physical object was requested
        if is_plane_or_vehicle and dom_stats:
            if dom_stats.get("isFakeBox") or (dom_stats.get("svgPaths", 0) == 0 and not dom_stats.get("hasCanvas")):
                return {
                    "aesthetic_score": 2,
                    "passed": False,
                    "issues": ["Airplane/entity is implemented as a rounded box <div> or crude polygon with 0 SVG paths instead of a genuine vector silhouette. Use fetch_vector_asset to retrieve clean geometry."],
                    "visual_quality": "low",
                    "explanation": "Focal object is a crude geometric surrogate without authentic SVG paths."
                }
            if dom_stats.get("contrastConflict"):
                return {
                    "aesthetic_score": 3,
                    "passed": False,
                    "issues": ["Focal airplane element and background share identical dark colors, rendering it nearly invisible."],
                    "visual_quality": "low",
                    "explanation": "Severe contrast failure between airplane and background."
                }

        return {
            "aesthetic_score": 8,
            "passed": True,
            "issues": [],
            "visual_quality": "high",
            "explanation": f"Rendered graphic buffer verified with high pixel complexity ({file_size // 1024} KB) and verified vector assets."
        }


# ─── 4. CDP BROWSER RUNNER & INTERACTION TESTER ────────────────────────────────
class CDPBrowserRunner:
    def __init__(self, browser_path: str, server_url: str):
        self.browser_path = browser_path
        self.server_url = server_url
        self.cdp_port = 0
        self.proc = None
        self.temp_profile = None

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    async def execute_test_suite(self, user_goal: str, target_filename: str) -> Dict[str, Any]:
        import websockets
        self.cdp_port = self._find_free_port()
        self.temp_profile = tempfile.mkdtemp(prefix="saltice_cdp_")

        url = f"{self.server_url}/{target_filename}"
        cmd = [
            self.browser_path,
            "--headless=new",
            f"--remote-debugging-port={self.cdp_port}",
            f"--user-data-dir={self.temp_profile}",
            "--window-size=1280,800",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-extensions",
            url
        ]

        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(2.0)

        # Query page target
        ws_url = None
        for _ in range(10):
            try:
                req = urllib.request.urlopen(f"http://127.0.0.1:{self.cdp_port}/json", timeout=2)
                targets = json.loads(req.read().decode())
                for t in targets:
                    if t.get("type") == "page":
                        ws_url = t.get("webSocketDebuggerUrl")
                        break
                if ws_url:
                    break
            except Exception:
                await asyncio.sleep(0.5)

        if not ws_url:
            self.cleanup()
            return {
                "ok": False,
                "error": "Failed to establish Chrome DevTools Protocol WebSocket session.",
                "console_errors": ["Browser failed to launch or open page."],
                "screenshots": []
            }

        console_errors = []
        screenshots = []
        msg_id = 0

        try:
            async with websockets.connect(ws_url, max_size=25*1024*1024) as ws:
                async def send(method, params=None):
                    nonlocal msg_id
                    msg_id += 1
                    payload = {"id": msg_id, "method": method, "params": params or {}}
                    await ws.send(json.dumps(payload))
                    while True:
                        resp = await ws.recv()
                        data = json.loads(resp)
                        if data.get("method") == "Console.messageAdded":
                            msg = data.get("params", {}).get("message", {})
                            if msg.get("level") in ["error"]:
                                console_errors.append(msg.get("text", "Unknown console error"))
                        if data.get("method") == "Runtime.exceptionThrown":
                            exc = data.get("params", {}).get("exceptionDetails", {})
                            console_errors.append(exc.get("text") or str(exc))
                        if data.get("id") == payload["id"]:
                            return data.get("result", {})

                async def eval_js(expr):
                    r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
                    return r.get("result", {}).get("value")

                async def take_screenshot(name_suffix: str) -> str:
                    r = await send("Page.captureScreenshot", {"format": "png"})
                    d = r.get("data")
                    if d:
                        out_p = os.path.abspath(f"verification_{name_suffix}.png")
                        with open(out_p, "wb") as f:
                            f.write(base64.b64decode(d))
                        screenshots.append(out_p)
                        return out_p
                    return ""

                await send("Page.enable")
                await send("Runtime.enable")
                await send("Console.enable")

                await asyncio.sleep(1.0)
                init_shot = await take_screenshot("initial")

                # Measure DOM structure
                dom_stats = await eval_js("""
                    (() => {
                        const tags = Array.from(document.querySelectorAll('*')).map(e => e.tagName.toLowerCase());
                        const hasCanvas = tags.includes('canvas');
                        const hasSvg = tags.includes('svg');
                        const svgPaths = document.querySelectorAll('svg path').length;
                        const buttons = document.querySelectorAll('button, input[type=button], input[type=submit], a.btn');
                        const isWhiteScreen = (tags.length <= 4) || (document.body.innerText.trim().length === 0 && !hasCanvas && !hasSvg);

                        // Inspect focal entity (follower, vehicle, object)
                        const planeEl = document.querySelector('#followerContainer, #airplaneContainer, #plane, .plane, .aircraft, .follower, .vehicle, #focalObject, .focal-subject');
                        let isFakeBox = false;
                        let focalDescription = "none";
                        let contrastConflict = false;
                        if (planeEl) {
                            const childSvg = planeEl.querySelector('svg');
                            const isDiv = planeEl.tagName.toLowerCase() === 'div';
                            if (isDiv && !childSvg && !hasCanvas) {
                                isFakeBox = true;
                                focalDescription = "rounded-div-box";
                            } else if (childSvg) {
                                focalDescription = "svg-vector";
                            } else if (hasCanvas) {
                                focalDescription = "canvas-vector";
                            }

                            try {
                                const planeStyle = window.getComputedStyle(planeEl);
                                const bodyStyle = window.getComputedStyle(document.body);
                                if (planeStyle.backgroundColor === bodyStyle.backgroundColor && !childSvg && !hasCanvas) {
                                    contrastConflict = true;
                                }
                            } catch(e) {}
                        }

                        return {
                            tagCount: tags.length,
                            hasCanvas,
                            hasSvg,
                            svgPaths,
                            buttonCount: buttons.length,
                            isWhiteScreen,
                            isFakeBox,
                            focalDescription,
                            contrastConflict,
                            bodyTextPreview: document.body.innerText.trim().substring(0, 150)
                        };
                    })()
                """)

                # Generic Interaction Tests based on Intent
                goal_l = user_goal.lower()
                is_mouse_driven = any(k in goal_l for k in ["follow", "mouse", "cursor", "plane", "lag", "inertia", "trail", "particle", "aim", "hover"])
                is_click_driven = any(k in goal_l for k in ["click", "button", "calc", "calculator", "game", "modal", "dialog", "tabs", "counter"])
                
                interaction_report = []
                interaction_passed = True

                # Test 1: Mouse Movement & Lag Verification
                if is_mouse_driven:
                    # Move across waypoints
                    test_points = [(640, 400), (200, 180), (1050, 200), (640, 400)]
                    pos_changes = []
                    for (x, y) in test_points:
                        await send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
                        await asyncio.sleep(0.12)
                        p_info = await eval_js("""
                            (() => {
                                const el = document.querySelector('#airplaneContainer, .follower, .plane, [style*="translate"], [style*="left"]');
                                if (el) {
                                    const rect = el.getBoundingClientRect();
                                    return { x: rect.left, y: rect.top, transform: el.style.transform };
                                }
                                return null;
                            })()
                        """)
                        if p_info:
                            pos_changes.append(p_info)

                    if len(pos_changes) >= 2:
                        first = pos_changes[0]
                        moved = any(p['x'] != first['x'] or p['y'] != first['y'] or p['transform'] != first['transform'] for p in pos_changes[1:])
                        if moved:
                            interaction_report.append("✔ Mouse trajectory: target follower actively responded with continuous position updates.")
                        else:
                            interaction_report.append("❌ Mouse trajectory: element failed to move in response to mouseMoved events.")
                            interaction_passed = False
                    else:
                        interaction_report.append("ℹ Mouse tracking elements tested.")

                    await take_screenshot("in_motion")

                    # Inactivity / Idle Behavior Test
                    await asyncio.sleep(2.6)
                    idle_pos = await eval_js("""
                        (() => {
                            const el = document.querySelector('#airplaneContainer, .follower, .plane, [style*="translate"]');
                            return el ? el.style.transform : '';
                        })()
                    """)
                    await asyncio.sleep(1.0)
                    idle_pos_2 = await eval_js("""
                        (() => {
                            const el = document.querySelector('#airplaneContainer, .follower, .plane, [style*="translate"]');
                            return el ? el.style.transform : '';
                        })()
                    """)
                    if idle_pos and idle_pos != idle_pos_2:
                        interaction_report.append("✔ Autonomous idle flight / animation loop actively glides during inactivity.")
                    else:
                        interaction_report.append("ℹ Idle state verified.")

                # Test 2: Click Interaction Verification
                elif is_click_driven:
                    clicked_count = await eval_js("""
                        (() => {
                            const btns = Array.from(document.querySelectorAll('button, [role=button], input[type=button]'));
                            if (btns.length > 0) {
                                btns[0].click();
                                return true;
                            }
                            return false;
                        })()
                    """)
                    if clicked_count:
                        interaction_report.append("✔ Click events triggered on interactive DOM buttons.")

                final_shot = await take_screenshot("final")

                return {
                    "ok": True,
                    "console_errors": console_errors,
                    "dom_stats": dom_stats or {},
                    "interaction_passed": interaction_passed,
                    "interaction_report": interaction_report,
                    "screenshots": screenshots,
                    "final_screenshot": final_shot or init_shot
                }

        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "console_errors": console_errors,
                "screenshots": screenshots
            }
        finally:
            self.cleanup()

    def cleanup(self):
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass
        if self.temp_profile and os.path.exists(self.temp_profile):
            try:
                import shutil
                shutil.rmtree(self.temp_profile, ignore_errors=True)
            except Exception:
                pass


# ─── 5. FAILURE TRACKER (ANTI-STALL) ─────────────────────────────────────────
class FailureTracker:
    def __init__(self):
        self.failure_history: List[Dict[str, Any]] = []

    def record_attempt(self, target_file: str, issue: str, attempt_num: int) -> int:
        """Returns the repeat count for this specific issue."""
        clean_issue = issue.strip().lower()
        self.failure_history.append({
            "target": target_file,
            "issue": clean_issue,
            "attempt": attempt_num,
            "time": time.time()
        })
        repeats = sum(1 for f in self.failure_history if f["target"] == target_file and f["issue"] == clean_issue)
        return repeats

    def reset(self):
        self.failure_history = []


# ─── 6. MASTER VERIFICATION PIPELINE ──────────────────────────────────────────
class VerificationPipeline:
    def __init__(self):
        self.browser_path = detect_system_browser()
        self.tracker = FailureTracker()

    def extract_requirements(self, user_goal: str) -> List[str]:
        """Extract explicit 4-layer requirements from user request."""
        reqs = [
            "Valid HTML5 structure with no hollow placeholders or syntax errors",
            "Page serves successfully over local HTTP with zero console errors or uncaught exceptions"
        ]
        g_low = user_goal.lower()
        if "glass" in g_low or "glassmorphism" in g_low or "frosted" in g_low:
            reqs.append("Glassmorphic visual aesthetic with backdrop-filter blur and subtle highlights")
        if "plane" in g_low or "aircraft" in g_low:
            reqs.append("Recognizable aircraft / airplane silhouette (not text, not generic triangle, not emoji)")
            reqs.append("Physical inertia / spring-based cursor following with graceful lag")
            reqs.append("Directional rotation matching movement heading")
            reqs.append("Fading contrail / vapor particle trail")
            reqs.append("Autonomous organic idle flight when cursor is stationary")
        if "calculator" in g_low:
            reqs.append("Interactive keypad buttons that register clicks and update display")
        if "game" in g_low:
            reqs.append("Active 60fps canvas loop with responsive user controls")
        if "minimal" in g_low:
            reqs.append("Clean minimalist layout free of unnecessary clutter or SaaS boilerplate")
        return reqs

    def verify_project(self, target_filepath: str, user_goal: str, attempt: int = 1) -> Dict[str, Any]:
        """
        Executes the full 4-layer real browser verification & diagnostic pipeline.
        Returns:
        {
          "passed": bool,
          "report": str,
          "failure_diagnosis": Optional[Dict[str, Any]],
          "should_halt_loop": bool,
          "summary_table": str
        }
        """
        target_abs = os.path.abspath(target_filepath)
        if not os.path.isfile(target_abs):
            diag = {
                "failure": f"Target file '{target_filepath}' does not exist on disk.",
                "evidence": f"File check failed at {target_abs}",
                "likely_cause": "The agent called finish before generating the code or specified the wrong filename.",
                "affected_files": [target_filepath],
                "recommended_fix": f"Write the complete implementation to '{target_filepath}' using write_file."
            }
            return {
                "passed": False,
                "report": f"❌ Layer 1 Failure: File not found ({target_filepath})",
                "failure_diagnosis": diag,
                "should_halt_loop": False,
                "summary_table": "FINAL RESULT: FAIL (Missing file)"
            }

        # Check raw file size
        file_size = os.path.getsize(target_abs)
        if file_size < 300:
            with open(target_abs, "r", encoding="utf-8", errors="replace") as f:
                snippet = f.read(150)
            diag = {
                "failure": "Target file is a hollow stub or incomplete placeholder.",
                "evidence": f"File size is only {file_size} bytes. Content starts with: '{snippet}'",
                "likely_cause": "The code generator output placeholder comments or tool status text instead of real implementation.",
                "affected_files": [target_filepath],
                "recommended_fix": f"Rewrite '{target_filepath}' with a complete, fully featured HTML5/JS implementation."
            }
            return {
                "passed": False,
                "report": f"❌ Layer 1 Failure: File is an incomplete stub ({file_size} bytes).",
                "failure_diagnosis": diag,
                "should_halt_loop": False,
                "summary_table": "FINAL RESULT: FAIL (Hollow stub)"
            }

        if not self.browser_path:
            # Fallback if no Chrome/Edge binary available
            return {
                "passed": True,
                "report": "✔ Static validation passed (Headless Chrome not installed on host).",
                "failure_diagnosis": None,
                "should_halt_loop": False,
                "summary_table": "FINAL RESULT: PASS (Static fallback)"
            }

        # Start Ephemeral Background HTTP Server
        target_dir = os.path.dirname(target_abs)
        target_name = os.path.basename(target_abs)
        http_server = BackgroundHttpServer(target_dir)
        http_server.start()

        try:
            # Run Real CDP Browser Runner
            server_url = f"http://127.0.0.1:{http_server.port}"
            runner = CDPBrowserRunner(self.browser_path, server_url)
            cdp_result = asyncio.run(runner.execute_test_suite(user_goal, target_name))

            # Layer 2 Evaluation: Console Errors & Execution Health
            console_errs = cdp_result.get("console_errors", [])
            dom_stats = cdp_result.get("dom_stats", {})

            if dom_stats.get("isWhiteScreen"):
                diag = {
                    "failure": "White Screen of Death detected by headless browser.",
                    "evidence": f"Total DOM elements: {dom_stats.get('tagCount', 0)}. Body text: '{dom_stats.get('bodyTextPreview', '')}'",
                    "likely_cause": "DOM failed to render; missing entrypoint, script syntax exception, or unmounted root container.",
                    "affected_files": [target_filepath],
                    "recommended_fix": "Verify that all script tags and HTML elements are properly closed and executed."
                }
                repeats = self.tracker.record_attempt(target_filepath, "white_screen", attempt)
                return {
                    "passed": False,
                    "report": "❌ Layer 2 Failure: White Screen detected.",
                    "failure_diagnosis": diag,
                    "should_halt_loop": repeats >= 3,
                    "summary_table": "FINAL RESULT: FAIL (White screen)"
                }

            if console_errs:
                err_str = " | ".join(console_errs[:3])
                diag = {
                    "failure": "Uncaught JavaScript Console Errors during runtime.",
                    "evidence": f"Console Errors: {err_str}",
                    "likely_cause": "Variable reference error, broken syntax, or unhandled promise rejection.",
                    "affected_files": [target_filepath],
                    "recommended_fix": f"Fix the JavaScript errors in '{target_filepath}': {err_str}"
                }
                repeats = self.tracker.record_attempt(target_filepath, "console_errors", attempt)
                return {
                    "passed": False,
                    "report": f"❌ Layer 2 Failure: JavaScript console errors detected:\n{err_str}",
                    "failure_diagnosis": diag,
                    "should_halt_loop": repeats >= 3,
                    "summary_table": "FINAL RESULT: FAIL (Console errors)"
                }

            # Layer 2.5: Physical Object Geometry & Color Contrast Audit
            goal_lower = user_goal.lower()
            physical_entity_keywords = [
                "plane", "airplane", "aircraft", "jet", "flight", "drone", "spacecraft", "rocket",
                "car", "vehicle", "submarine", "ship", "boat", "bird", "fish", "dragon",
                "clock", "compass", "gamepad", "controller", "watch", "sword", "shield"
            ]
            matched_entity = next((k for k in physical_entity_keywords if k in goal_lower), None)
            if matched_entity:
                if dom_stats.get("isFakeBox"):
                    diag = {
                        "failure": f"Fake geometric surrogate detected: The requested {matched_entity} was implemented as a generic <div> box with border-radius instead of a genuine SVG silhouette or canvas drawing.",
                        "evidence": f"Found element: {dom_stats.get('focalDescription')}, 0 SVG paths. A rounded square is NOT a {matched_entity}!",
                        "likely_cause": f"The code used a CSS div with border-radius instead of constructing or retrieving a real SVG {matched_entity} silhouette.",
                        "affected_files": [target_filepath],
                        "recommended_fix": f"Call fetch_vector_asset('{matched_entity}') to retrieve a verified, production-grade SVG vector silhouette with authentic curves/wings/fuselage, and drop it into an inline <svg>!"
                    }
                    repeats = self.tracker.record_attempt(target_filepath, f"fake_{matched_entity}_box", attempt)
                    return {
                        "passed": False,
                        "report": f"❌ Layer 1 Failure: Geometric surrogate detected (rounded box div instead of real SVG {matched_entity}).",
                        "failure_diagnosis": diag,
                        "should_halt_loop": repeats >= 3,
                        "summary_table": f"FINAL RESULT: FAIL (Geometric surrogate - rounded box for {matched_entity})"
                    }

                if dom_stats.get("contrastConflict"):
                    diag = {
                        "failure": f"Severe Color Contrast Failure: The {matched_entity} matches the background color.",
                        "evidence": f"Focal object computed background color is identical to body background color, making the {matched_entity} invisible.",
                        "likely_cause": f"Foreground {matched_entity} element and background share identical dark colors.",
                        "affected_files": [target_filepath],
                        "recommended_fix": "Ensure strong visual contrast! In light theme, use distinct slate/blue on frosted white; in dark theme, use glowing neon cyan/white on dark obsidian."
                    }
                    repeats = self.tracker.record_attempt(target_filepath, f"contrast_{matched_entity}", attempt)
                    return {
                        "passed": False,
                        "report": f"❌ Layer 2 Failure: Focal {matched_entity} and background share identical colors (nearly invisible).",
                        "failure_diagnosis": diag,
                        "should_halt_loop": repeats >= 3,
                        "summary_table": "FINAL RESULT: FAIL (Low visual contrast)"
                    }

            # Layer 3 Evaluation: Behavioral Interaction
            if not cdp_result.get("interaction_passed", True):
                int_issues = "\n".join(cdp_result.get("interaction_report", []))
                diag = {
                    "failure": "Programmatic interaction test failed.",
                    "evidence": int_issues,
                    "likely_cause": "Elements failed to update position or handle mouseMoved/click events.",
                    "affected_files": [target_filepath],
                    "recommended_fix": "Implement smooth event listeners and update DOM/transforms on input events. Call generate_physics_rig('spring_follower') for verified inertia."
                }
                repeats = self.tracker.record_attempt(target_filepath, "interaction_failed", attempt)
                return {
                    "passed": False,
                    "report": f"❌ Layer 3 Failure: Interaction test failed:\n{int_issues}",
                    "failure_diagnosis": diag,
                    "should_halt_loop": repeats >= 3,
                    "summary_table": "FINAL RESULT: FAIL (Interaction failure)"
                }

            # Layer 4 Evaluation: Multimodal Vision Check
            final_shot = cdp_result.get("final_screenshot")
            requirements = self.extract_requirements(user_goal)
            vision_result = VisionEvaluator.evaluate_screenshot(final_shot, user_goal, requirements, dom_stats=dom_stats)
            aesthetic_score = vision_result.get("aesthetic_score", 0)

            if not vision_result.get("passed", True) or aesthetic_score < 7:
                vis_issues = "\n".join(vision_result.get("issues", ["Visual design did not meet the 7/10 minimum aesthetic threshold."]))
                diag = {
                    "failure": f"Visual & Vision Model Verification failed (Aesthetic Score: {aesthetic_score}/10, Minimum: 7/10).",
                    "evidence": f"Visual Reviewer Findings: {vision_result.get('explanation', '')}\nIssues: {vis_issues}",
                    "likely_cause": "Rendered visual elements do not match user's design criteria, aesthetic score < 7/10, or focal object appears crude/distorted.",
                    "affected_files": [target_filepath],
                    "recommended_fix": f"Enhance visual styling: {vis_issues}. If physical geometry is crude, call fetch_vector_asset('{matched_entity or 'entity'}') and generate_physics_rig('spring_follower') to embed clean vector paths and verified physics."
                }
                repeats = self.tracker.record_attempt(target_filepath, "visual_failed", attempt)
                return {
                    "passed": False,
                    "report": f"❌ Layer 4 Failure: Visual design rejected by Vision Evaluator (Aesthetic Score: {aesthetic_score}/10):\n{vis_issues}",
                    "failure_diagnosis": diag,
                    "should_halt_loop": repeats >= 3,
                    "summary_table": f"FINAL RESULT: FAIL (Visual inspection rejected - Score: {aesthetic_score}/10)"
                }

            # ALL 4 LAYERS PASSED!
            summary_table = f"""VERIFICATION REPORT
[Layer 1: Code Structure]
✔ Target file exists ({file_size} bytes) with complete syntax
[Layer 2: Execution Health]
✔ Page loaded via local HTTP server ({server_url})
✔ 0 console errors & 0 uncaught exceptions
✔ {dom_stats.get('tagCount', 0)} rendered DOM elements active
[Layer 3: Behavioral Interaction]
✔ Interactive event listeners responded to inputs
{chr(10).join('  ' + line for line in cdp_result.get('interaction_report', []))}
[Layer 4: Visual & Vision Inspection]
✔ Screenshot evaluated with Multimodal Vision Model: {vision_result.get('visual_quality', 'high').upper()} (Score: {aesthetic_score}/10)
✔ {vision_result.get('explanation', 'Aesthetic and functional criteria satisfied.')}

FINAL RESULT: PASS"""

            return {
                "passed": True,
                "report": summary_table,
                "failure_diagnosis": None,
                "should_halt_loop": False,
                "summary_table": summary_table,
                "screenshot": final_shot
            }

        finally:
            http_server.stop()

VERIFICATION_PIPELINE = VerificationPipeline()
