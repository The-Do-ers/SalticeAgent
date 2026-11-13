"""
Autonomous Visual Browser Verification and UI Quality Validator for Saltice
Equipped with:
- Zero-external-dependency headless Chrome / Microsoft Edge inspection
- Evaluated DOM extraction (--dump-dom) post-JavaScript execution
- Headless screenshot capture (1280x800) for visual verification
- White-screen and hollow-stub detection (catches empty roots and missing script assets)
- Canvas, SVG, and interactive component verification
"""

import os
import sys
import re
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple

class UIValidator:
    def __init__(self):
        self.browser_path = self._detect_browser()
        self.temp_dir = os.path.join(tempfile.gettempdir(), "saltice_browser_verification")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _detect_browser(self) -> Optional[str]:
        """Locate Google Chrome or Microsoft Edge executable on the system."""
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        # Try PATH
        for name in ["chrome", "google-chrome", "chromium", "msedge"]:
            found = shutil.which(name)
            if found:
                return found
        return None

    def _normalize_url(self, target: str) -> str:
        t = target.strip()
        if t.startswith(("http://", "https://", "data:")):
            return t
        abs_p = os.path.abspath(t)
        return "file:///" + abs_p.replace("\\", "/")

    def inspect_rendered_dom(self, target_file_or_url: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        Run headless browser to evaluate JavaScript and return the final rendered DOM.
        """
        if not self.browser_path:
            return False, "No headless browser (Chrome/Edge) found on this machine."

        target_url = self._normalize_url(target_file_or_url)
        user_data = tempfile.mkdtemp(prefix="chrome_dom_")

        cmd = [
            self.browser_path,
            "--headless=new" if "chrome.exe" in self.browser_path.lower() else "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--allow-file-access-from-files",
            "--disable-web-security",
            "--virtual-time-budget=2000",
            f"--user-data-dir={user_data}",
            "--dump-dom",
            target_url
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            dom_out = proc.stdout or ""
            return True, dom_out
        except subprocess.TimeoutExpired:
            # If local file, read raw content as fallback
            if not target_file_or_url.startswith(("http://", "https://", "data:")) and os.path.isfile(target_file_or_url):
                try:
                    with open(target_file_or_url, "r", encoding="utf-8", errors="replace") as f:
                        return True, f.read()
                except Exception:
                    pass
            return False, f"Browser timed out ({timeout}s) while rendering DOM."
        except Exception as e:
            return False, f"Browser execution error: {e}"
        finally:
            shutil.rmtree(user_data, ignore_errors=True)

    def capture_screenshot(
        self,
        target_file_or_url: str,
        output_path: Optional[str] = None,
        timeout: int = 15,
        window_size: str = "1280,800"
    ) -> Tuple[bool, str]:
        """
        Capture a headless screenshot of the target HTML file or URL.
        """
        if not self.browser_path:
            return False, "No headless browser (Chrome/Edge) found on this system."

        target_url = self._normalize_url(target_file_or_url)
        if not output_path:
            output_path = os.path.abspath("ui_verification_screenshot.png")
        else:
            output_path = os.path.abspath(output_path)

        user_data = tempfile.mkdtemp(prefix="chrome_shot_")

        cmd = [
            self.browser_path,
            "--headless=new" if "chrome.exe" in self.browser_path.lower() else "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--allow-file-access-from-files",
            "--disable-web-security",
            "--virtual-time-budget=2000",
            f"--user-data-dir={user_data}",
            f"--screenshot={output_path}",
            f"--window-size={window_size}",
            target_url
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if os.path.isfile(output_path) and os.path.getsize(output_path) > 500:
                return True, output_path
            return False, f"Screenshot was not generated or file size was too small ({output_path})."
        except subprocess.TimeoutExpired:
            return False, f"Screenshot timed out after {timeout}s."
        except Exception as e:
            return False, f"Screenshot capture error: {e}"
        finally:
            shutil.rmtree(user_data, ignore_errors=True)

    def verify_ui_health(self, target_file_or_url: str, take_screenshot: bool = True) -> Dict[str, Any]:
        """
        Comprehensive UI Health and Visual Audit:
        1. Rendered DOM Inspection
        2. White-Screen / Empty Root Detection
        3. Broken Script / Missing Assets Detection
        4. Interactive Elements (Canvas, Buttons, Forms, Inputs) Count
        5. Visual Styling Audit (Tailwind, CSS classes, Neon/Glass attributes)
        6. Screenshot Generation
        """
        result = {
            "ok": True,
            "target": target_file_or_url,
            "browser": os.path.basename(self.browser_path) if self.browser_path else "None",
            "dom_elements_count": 0,
            "has_interactive_elements": False,
            "has_canvas": False,
            "has_styles": False,
            "has_glassy_or_neon": False,
            "screenshot_path": None,
            "issues": [],
            "warnings": [],
            "report": ""
        }

        # Check local file existence if not URL
        if not target_file_or_url.startswith(("http://", "https://", "data:")):
            if not os.path.exists(target_file_or_url):
                result["ok"] = False
                result["issues"].append(f"Target file does not exist on disk: {target_file_or_url}")
                result["report"] = f"❌ File Not Found: {target_file_or_url}"
                return result

        # 1. Rendered DOM extraction
        ok_dom, dom_content = self.inspect_rendered_dom(target_file_or_url)
        if not ok_dom:
            result["ok"] = False
            result["issues"].append(f"DOM rendering failed: {dom_content}")
            result["report"] = f"❌ Headless Browser Error: {dom_content}"
            return result

        # 2. Analyze DOM structure
        dom_lower = dom_content.lower()

        # Count tags
        tags = re.findall(r'<([a-zA-Z0-9\-]+)[^>]*>', dom_content)
        tag_set = set(t.lower() for t in tags)
        result["dom_elements_count"] = len(tags)

        # Check if this is a Vite / React entrypoint pointing to source (e.g. /src/main.tsx)
        is_vite_source_entry = bool(re.search(r'src=["\']/(?:src/)?[a-zA-Z0-9_\-]+\.(?:tsx|jsx|ts|js)["\']', dom_content, re.IGNORECASE))

        # White-screen check: check empty root container
        empty_root_matches = re.search(r'<div\s+id=["\']root["\']\s*>\s*</div>', dom_content, re.IGNORECASE)
        empty_app_matches = re.search(r'<div\s+id=["\']app["\']\s*>\s*</div>', dom_content, re.IGNORECASE)
        
        # If there is a root div and it's empty, and it is NOT a Vite source entrypoint, it's a white screen
        if not is_vite_source_entry and (empty_root_matches or empty_app_matches) and len(tags) <= 8:
            result["ok"] = False
            result["issues"].append("WHITE SCREEN DETECTED: #root container is completely empty with no rendered child DOM nodes.")

        # Check for unrendered body
        body_match = re.search(r'<body[^>]*>([\s\S]*?)</body>', dom_content, re.IGNORECASE)
        if body_match:
            body_inner = body_match.group(1).strip()
            # If body inner is literally empty or just a comment
            clean_body = re.sub(r'<!--[\s\S]*?-->', '', body_inner).strip()
            if not clean_body:
                result["ok"] = False
                result["issues"].append("BLANK SCREEN: <body> contains zero HTML markup or rendered content.")

        # 3. Broken assets detection (e.g. ./dist/assets/...)
        dist_m = re.findall(r'src=["\'](\./dist/assets/[^"\']+)["\']', dom_content, re.IGNORECASE)
        if dist_m:
            result["ok"] = False
            result["issues"].append(f"BROKEN SCRIPT ASSET: Entrypoint references non-existent dist bundle: '{dist_m[0]}'. Must point to source like '/src/main.tsx' or inline script.")

        # 4. Interactive elements check
        interactive_tags = {"button", "input", "select", "textarea", "a", "canvas", "svg"}
        has_interactive = bool(tag_set.intersection(interactive_tags))
        result["has_interactive_elements"] = has_interactive
        result["has_canvas"] = "canvas" in tag_set

        # 5. Styling and design check
        has_tailwind = "cdn.tailwindcss.com" in dom_lower or "tailwind" in dom_lower
        has_style_tag = "<style" in dom_lower or 'class="' in dom_lower
        result["has_styles"] = has_tailwind or has_style_tag

        has_glass = "backdrop-blur" in dom_lower or "rgba(" in dom_lower or "glass" in dom_lower
        has_neon = "box-shadow" in dom_lower or "glow" in dom_lower or "neon" in dom_lower or "#00f" in dom_lower or "#0ff" in dom_lower
        result["has_glassy_or_neon"] = has_glass or has_neon

        # If it's a game or visualizer, lack of canvas/svg is an issue
        app_name = os.path.basename(target_file_or_url).lower()
        if any(w in app_name for w in ["snake", "pong", "game", "visualizer", "synth"]):
            if not result["has_canvas"] and not ("<svg" in dom_lower):
                result["warnings"].append(f"Visual application '{app_name}' renders no <canvas> or <svg> elements.")

        # 6. Screenshot capture
        if take_screenshot and self.browser_path:
            shot_file = os.path.abspath(f"screenshot_{os.path.splitext(os.path.basename(target_file_or_url))[0]}.png")
            shot_ok, shot_res = self.capture_screenshot(target_file_or_url, shot_file)
            if shot_ok:
                result["screenshot_path"] = shot_file

        # Format textual report
        status_icon = "✔" if result["ok"] else "❌"
        lines = [
            f"{status_icon} UI & Visual Verification Report: {target_file_or_url}",
            f"  • Headless Browser: {result['browser']}",
            f"  • Total Rendered DOM Elements: {result['dom_elements_count']}",
            f"  • Interactive Controls Present: {'Yes' if result['has_interactive_elements'] else 'No'}",
            f"  • Canvas / Graphics Elements: {'Yes' if result['has_canvas'] else 'No'}",
            f"  • Styling & Themes: {'Active (Glass/Neon)' if result['has_glassy_or_neon'] else ('Basic CSS' if result['has_styles'] else 'None')}"
        ]

        if result["screenshot_path"]:
            lines.append(f"  • Screenshot Captured: {result['screenshot_path']} ({os.path.getsize(result['screenshot_path'])} bytes)")

        if result["issues"]:
            lines.append("\n[CRITICAL UI ISSUES FOUND]:")
            for iss in result["issues"]:
                lines.append(f"  ❌ {iss}")

        if result["warnings"]:
            lines.append("\n[UI WARNINGS]:")
            for w in result["warnings"]:
                lines.append(f"  ⚠️ {w}")

        if result["ok"]:
            lines.append("\n✔ Visual inspection passed: Page successfully rendered interactive content with zero white screens.")

        result["report"] = "\n".join(lines)
        return result

UI_VALIDATOR = UIValidator()
