# per_condition_accuracy.py
# Runs the classifier over the dataset grouped by recording condition
# (near/bright baseline, far/bright, near/dim) and reports accuracy per
# condition. This is the robustness result AND a sanity check on the classifier.

import glob
import csv
import os
from collections import defaultdict
from classifier import classify

GESTURES = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]

def condition_of(filename):
    """Map a filename to a condition group."""
    name = os.path.basename(filename).lower()
    dist = "far" if "far" in name else "near"
    light = "dim" if "dim" in name else "bright"
    return f"{dist}_{light}"

# correct[condition], total[condition]
correct = defaultdict(int)
total = defaultdict(int)
# per gesture per condition
g_correct = defaultdict(lambda: defaultdict(int))
g_total = defaultdict(lambda: defaultdict(int))

for path in sorted(glob.glob("data/gesture_recordings/*.csv")):
    cond = condition_of(path)
    with open(path) as f:
        for row in csv.DictReader(f):
            intended = row["intended_gesture"]
            if intended not in GESTURES:
                continue
            handed = row.get("handedness", "Right")
            coords = []
            for i in range(21):
                coords += [float(row[f"x{i}"]), float(row[f"y{i}"]), float(row[f"z{i}"])]
            pred = classify(coords, handed)
            total[cond] += 1
            g_total[cond][intended] += 1
            if pred == intended:
                correct[cond] += 1
                g_correct[cond][intended] += 1

# --- Overall accuracy per condition ---
print("=== Recognition accuracy by condition ===\n")
conditions = sorted(total.keys())
for cond in conditions:
    acc = correct[cond] / total[cond] * 100 if total[cond] else 0
    print(f"  {cond:14s}: {acc:5.1f}%   ({correct[cond]}/{total[cond]} frames)")

# --- Per-gesture breakdown per condition ---
print("\n=== Per-gesture accuracy by condition ===")
print(f"\n{'Gesture':10s}" + "".join(f"{c:>14s}" for c in conditions))
for g in GESTURES:
    line = f"{g:10s}"
    for cond in conditions:
        t = g_total[cond][g]
        a = g_correct[cond][g] / t * 100 if t else 0
        line += f"{a:13.1f}%"
    print(line)

# --- Save to CSV ---
with open("data/accuracy_by_condition.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["condition", "overall_accuracy_pct", "frames"])
    for cond in conditions:
        acc = correct[cond] / total[cond] * 100 if total[cond] else 0
        w.writerow([cond, round(acc, 2), total[cond]])
print("\nSaved data/accuracy_by_condition.csv")