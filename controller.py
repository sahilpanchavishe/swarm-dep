# controller.py
# Decentralized potential-field controller for one robot.
# Each robot computes its own (v, w) using ONLY:
#   - its own assigned slot (its goal)
#   - the positions of neighbours within SENSE_RADIUS
# No global controller is used. This enforces the "decentralized" claim.

import numpy as np
from robot import V_MAX, W_MAX, ROBOT_RADIUS

# --- Controller gains and ranges (tunable; report final values) ---
K_ATT = 1.0            # strength of pull toward the target slot
K_REP = 0.02           # strength of push away from close neighbours
SENSE_RADIUS = 0.5     # [m] a robot only "sees" neighbours within this range
SAFE_DIST = 2 * ROBOT_RADIUS + 0.05   # desired min centre-to-centre spacing [m]
HEADING_GAIN = 3.0     # how hard the robot turns to face its desired direction

def compute_force(me, slot, neighbours):
    """Return the desired velocity vector (fx, fy) for robot `me`.
    me        : the Robot computing its move
    slot      : (sx, sy) its target position in the formation
    neighbours: list of OTHER robots (we filter by sensing radius here)
    """
    # --- Attraction to the assigned slot ---
    sx, sy = slot
    fx = K_ATT * (sx - me.x)
    fy = K_ATT * (sy - me.y)

    # --- Repulsion from neighbours within sensing range ---
    for other in neighbours:
        if other.id == me.id:
            continue
        dx = me.x - other.x
        dy = me.y - other.y
        dist = np.hypot(dx, dy)
        # Decentralized: ignore anyone outside the sensing radius.
        if dist < SENSE_RADIUS and dist > 1e-6:
            if dist < SAFE_DIST:
                # Push strength grows as robots get closer than SAFE_DIST.
                strength = K_REP * (1.0/dist - 1.0/SAFE_DIST) / (dist**2)
                fx += strength * dx
                fy += strength * dy
    return fx, fy

def force_to_cmd(me, fx, fy, dt):
    """Convert a desired velocity vector into (v, w) the diff-drive robot
    can execute. A TurtleBot cannot move sideways, so it turns toward the
    desired direction and drives forward.
    """
    desired_angle = np.arctan2(fy, fx)
    magnitude = np.hypot(fx, fy)

    # Smallest signed angle between current heading and desired direction.
    angle_err = (desired_angle - me.theta + np.pi) % (2*np.pi) - np.pi

    # Turn rate proportional to heading error.
    w = HEADING_GAIN * angle_err

    # Only drive forward when roughly facing the goal; otherwise turn in place.
    # (cos(angle_err) is ~1 when aligned, ~0 or negative when not.)
    v = magnitude * max(0.0, np.cos(angle_err))

    return np.clip(v, 0, V_MAX), np.clip(w, -W_MAX, W_MAX)