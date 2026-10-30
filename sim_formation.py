# sim_formation.py
# Runs N robots under the decentralized controller toward one formation,
# with live animation. Development tool; figures come later.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from robot import Robot, ROBOT_RADIUS
from controller import compute_force, force_to_cmd
from formations import SHAPES

# --- Settings ---
N = 16
DT = 0.02
SHAPE = "circle"          # try "line", "cluster", "split" too
STEPS = 400 + 40 * N      # bigger swarms get more time             # 12 s

# --- Initialise robots at random-ish start positions ---
rng = np.random.default_rng(0)   # fixed seed = reproducible
robots = []
for i in range(N):
    x = rng.uniform(-1.0, 1.0)
    y = rng.uniform(-1.0, 1.0)
    theta = rng.uniform(-np.pi, np.pi)
    robots.append(Robot(x, y, theta, robot_id=i))

slots = SHAPES[SHAPE](N)

# --- Set up the plot ---
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_aspect("equal")
ax.set_title(f"{SHAPE} formation, N={N}")

# Draw target slots as hollow markers.
for (sx, sy) in slots:
    ax.plot(sx, sy, "x", color="grey", markersize=8)

dots, = ax.plot([], [], "o", color="tab:blue", markersize=8)

def update(frame):
    for i, r in enumerate(robots):
        fx, fy = compute_force(r, slots[i], robots)   # robots = neighbours
        v, w = force_to_cmd(r, fx, fy, DT)
        r.step(v, w, DT)
    dots.set_data([r.x for r in robots], [r.y for r in robots])
    return (dots,)

anim = FuncAnimation(fig, update, frames=STEPS, interval=20, blit=True)
plt.show()