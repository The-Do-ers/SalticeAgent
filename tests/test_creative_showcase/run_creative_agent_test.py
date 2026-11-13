import os
import sys

# Change working directory to test_creative_showcase so files are generated here
TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(TARGET_DIR)

ROOT_DIR = os.path.abspath(os.path.join(TARGET_DIR, ".."))
AGENT_DIR = os.path.join(ROOT_DIR, "SalticeAgent")
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from engine import SalticeAntigravityEngine

prompt = """Build a cutting-edge creative agency website in index.html for 'AETHER LABS', an avant-garde digital design & creative development studio.

Requirements:
1. GSAP & Lenis Smooth Motion (gsap-lenis-motion):
   - Include Lenis v1.1.18 smooth scroll and synchronize with GSAP 3.12.5 and ScrollTrigger.
   - Hero headline with kinetic typography and staggered character reveal: 'BEYOND THE HORIZON'.
   - A pinned horizontal scroll showcase section for featured projects.

2. React Bits Micro-Interactions (react-bits):
   - Hero Decrypted Text effect that unscrambles cyber matrix glyphs on hover.
   - Interactive Canvas Dot Grid background that reacts to mouse proximity.
   - Spotlight Cards with cursor-following radial glow borders.

3. Kokonut UI Modern Components (kokonut-ui):
   - Dynamic Island bottom floating dock with navigation icons (Home, Projects, Labs, AI, Contact) and hover spring physics.
   - Modern AI prompt command input bar with search toggle pill and gradient submit button.
   - Bento Grid cards for studio capabilities.

4. Awards-Grade Aesthetics (creative-web-design):
   - Procedural SVG film grain / paper texture overlay (Niccolo Miranda style).
   - High-contrast editorial typography (Danilo De Marco style) with dark obsidian, cyan, and silver accents.
   - Stacked card deck (Ollivere style) where cards pin and scale down on scroll.
   - Absolutely NO generic frosted glass boxes or dark-on-dark rounded squares!

Output the complete, fully functional, 100% working implementation in index.html with all scripts and styles included!"""

print("==================================================")
print("🚀 Launching Saltice Agent on Creative Test Prompt")
print("==================================================")

engine = SalticeAntigravityEngine(mode="gemini", max_iterations=10)
summary = engine.run(user_goal=prompt, target_override="index.html")

print("\n==================================================")
print("✔ Saltice Agent Execution Finished!")
print("==================================================")
print("Summary:", summary)
