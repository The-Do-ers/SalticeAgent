import os
import sys
import time

CLI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if CLI_DIR not in sys.path:
    sys.path.insert(0, CLI_DIR)

TARGET_DIR = r"D:\USEME FOLDER\Saltice\space_defense"
os.makedirs(TARGET_DIR, exist_ok=True)
os.chdir(TARGET_DIR)

from engine import SalticeAntigravityEngine

task = (
    "Build a complete, high-difficulty browser game 'space_defense.html' (Neon Void: Cyberpunk Space Defense Arena).\n"
    "Requirements:\n"
    "1. 2D Space Combat with Newtonian ship physics (acceleration, rotational damping, boundary wrapping, inertia).\n"
    "2. Procedural enemy waves: Tier-1 Fast Interceptors, Tier-2 Missile Cruisers, and a multi-phase Orbital Dreadnought Boss with rotating sweeping laser beams and bullet rings.\n"
    "3. Player weapons: Twin Plasma Cannons, Homing Micro-Missiles, and an expanding EMP shockwave that neutralizes enemy projectiles.\n"
    "4. Interactive in-game Upgrade Shop (open with B key or UI button) to upgrade Shields, Fire Rate, Plasma Damage, and Thruster Acceleration using scrap collected from destroyed enemies.\n"
    "5. Particle engine for thruster trails, explosions, shield impacts, and EMP shockwaves.\n"
    "6. Real-time Web Audio API multi-frequency synthesizer for all sound effects (plasma fire, missile launch, laser beam hum, explosion, EMP blast, shop purchase) with no external audio files.\n"
    "7. HUD with shield/health bars, radar mini-map, weapon cooldowns, wave telemetry, score, and scrap counter.\n"
    "8. Create implementation_plan.md and walkthrough.md documenting the architecture and features."
)

print(f"=== LAUNCHING SALTICE BENCHMARK in {os.getcwd()} ===")
t0 = time.time()
engine = SalticeAntigravityEngine(mode="mistral", max_iterations=8)
engine.run(task)
dt = time.time() - t0
print(f"=== BENCHMARK COMPLETED in {dt:.2f}s ===")
