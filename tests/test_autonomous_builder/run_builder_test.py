import os
import sys

TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(TARGET_DIR)

ROOT_DIR = os.path.abspath(os.path.join(TARGET_DIR, "..", ".."))
AGENT_DIR = os.path.join(ROOT_DIR, "SalticeAgent")
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from engine import SalticeAntigravityEngine

prompt = """Build a futuristic interactive web observatory in index.html for 'ORBITAL DYNAMICS' - Aerospace Telemetry & Orbital Mechanics Lab.

Follow Rule 7 (Iterative Part-by-Part Construction) and execute across multiple turns:
Stage 1 (Turn 1): Create index.html with the foundational structure:
  - Responsive layout, modern CSS design tokens (deep obsidian background, cyan/amber glowing telemetry accents, clean typography).
  - Main viewport header, status badges, canvas container for orbital telemetry, and placeholder bento grid sections.

Stage 2 (Turn 2): Inject UI Components & Bento Grid:
  - Kokonut UI style Dynamic Island floating control dock at bottom (Telemetry Toggle, Orbit Zoom, Gravity Well, Sound Synth).
  - Spotlight telemetry cards for Satellite Orbit, Velocity vector, Apogee/Perigee telemetry readouts.
  - Decrypted matrix text effect on hero headers.

Stage 3 (Turn 3): Inject GSAP 3 Motion & Interactive Canvas Physics:
  - GSAP animations for HUD elements entering viewport.
  - Interactive HTML5 Canvas showing planets/satellites orbiting a central gravitational body, responding to mouse position/gravity well pull.
  - Web Audio API synthesizer for telemetry sound fx on dock button clicks.

Stage 4 (Turn 4): Verify:
  - Call verify_with_real_browser('index.html') to confirm clean headless execution and visual render.
  - Call finish(summary) when verified!

Execute Stage 1 now!"""

print("==========================================================")
print("🚀 Launching Saltice Agent in Autonomous Multi-Turn Mode")
print("==========================================================")

engine = SalticeAntigravityEngine(mode="gemini", max_iterations=25)
summary = engine.run(user_goal=prompt, target_override="index.html")

print("\n==========================================================")
print("✔ Saltice Autonomous Execution Complete!")
print("==========================================================")
print("Summary:", summary)
