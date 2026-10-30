# formations.py
# Target slot positions for each formation shape.
# Each returns a list of (x, y) points, one slot per robot.
# Slots are assigned to robots by index (robot i -> slot i), a
# deterministic decentralized assignment (cf. fixed role indexing).

import numpy as np

def circle(n, radius=0.6, center=(0.0, 0.0)):
    """n robots evenly spaced on a circle."""
    cx, cy = center
    slots = []
    for i in range(n):
        angle = 2 * np.pi * i / n
        slots.append((cx + radius * np.cos(angle),
                      cy + radius * np.sin(angle)))
    return slots

def line(n, spacing=0.3, center=(0.0, 0.0)):
    """n robots in a horizontal line, evenly spaced."""
    cx, cy = center
    # centre the line on cx
    start = cx - spacing * (n - 1) / 2
    return [(start + i * spacing, cy) for i in range(n)]

def cluster(n, spacing=0.3, center=(0.0, 0.0)):
    """n robots packed in a rough grid (tight group)."""
    cx, cy = center
    cols = int(np.ceil(np.sqrt(n)))
    slots = []
    for i in range(n):
        row, col = divmod(i, cols)
        slots.append((cx + col * spacing, cy + row * spacing))
    # recentre the grid
    xs = [s[0] for s in slots]; ys = [s[1] for s in slots]
    mx, my = np.mean(xs), np.mean(ys)
    return [(x - mx + cx, y - my + cy) for x, y in slots]

def split(n, gap=1.0, spacing=0.3, center=(0.0, 0.0)):
    """Two sub-groups, left and right of centre."""
    cx, cy = center
    half = n // 2
    left = [(cx - gap/2, cy + (i - half/2) * spacing) for i in range(half)]
    right = [(cx + gap/2, cy + (i - (n-half)/2) * spacing) for i in range(n - half)]
    return left + right

SHAPES = {"circle": circle, "line": line, "cluster": cluster, "split": split}