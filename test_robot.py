# test_robot.py
import numpy as np
import matplotlib.pyplot as plt
from robot import Robot

dt = 0.02          # 50 Hz
steps = 500        # 10 seconds

# Test 1: drive straight. Robot should move in a straight line along +x.
r = Robot(x=0, y=0, theta=0, robot_id=0)
xs, ys = [], []
for _ in range(steps):
    r.step(v_cmd=0.22, w_cmd=0.0, dt=dt)   # full speed, no turn
    xs.append(r.x); ys.append(r.y)
print(f"Straight test: after 10 s at 0.22 m/s, x = {r.x:.3f} m (expect ~2.2 m)")

# Test 2: drive in a circle. Constant v and w should trace a circle.
r2 = Robot(x=0, y=0, theta=0, robot_id=1)
cx, cy = [], []
for _ in range(steps):
    r2.step(v_cmd=0.15, w_cmd=0.5, dt=dt)
    cx.append(r2.x); cy.append(r2.y)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(xs, ys); ax[0].set_title("Straight line"); ax[0].axis("equal")
ax[1].plot(cx, cy); ax[1].set_title("Circle"); ax[1].axis("equal")
plt.tight_layout(); plt.savefig("robot_test.png", dpi=120); plt.show()