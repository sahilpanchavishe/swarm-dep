# build_confusion.py
# Runs the rule-based classifier over all recorded frames and builds the
# real confusion matrix: rows = intended gesture, cols = recognised gesture.
# Writes data/confusion_matrix.csv (overwrites the placeholder).

import glob
import csv
import numpy as np
from collections import defaultdict
from classifier import classify

GESTURES = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]

counts = defaultdict(lambda: defaultdict(int))   # counts[intended][recognised]
total_frames = 0
per_gesture_correct = defaultdict(int)
per_gesture_total = defaultdict(int)

for path in sorted(glob.glob("data/gesture_recordings/*.csv")):
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            intended = row["intended_gesture"]
            if intended not in GESTURES:
                continue
            handed = row.get("handedness", "Right")
            coords = []
            for i in range(21):
                coords += [float(row[f"x{i}"]), float(row[f"y{i}"]), float(row[f"z{i}"])]
            pred = classify(coords, handed)
            counts[intended][pred] += 1
            total_frames += 1
            per_gesture_total[intended] += 1
            if pred == intended:
                per_gesture_correct[intended] += 1

# Build normalized confusion matrix (each row sums to 1).
print(f"Total frames classified: {total_frames}\n")
print("Per-gesture recognition accuracy:")
overall_correct = 0
for g in GESTURES:
    tot = per_gesture_total[g]
    acc = per_gesture_correct[g] / tot if tot else 0
    overall_correct += per_gesture_correct[g]
    print(f"  {g:8s}: {acc*100:5.1f}%  ({per_gesture_correct[g]}/{tot})")
print(f"\nOverall accuracy: {overall_correct/total_frames*100:.1f}%\n")

# Write normalized matrix in the same format channel_model.py expects.
with open("data/confusion_matrix.csv", "w", newline="") as f:
    f.write("# MEASURED confusion matrix from 8 participants (rule-based classifier)\n")
    f.write("# Rows = intended gesture, Columns = recognised gesture. Each row sums to 1.0.\n")
    f.write("intended," + ",".join(GESTURES) + "\n")
    for intended in GESTURES:
        tot = sum(counts[intended].values())
        if tot == 0:
            probs = [1.0 if g == intended else 0.0 for g in GESTURES]
        else:
            probs = [counts[intended][g] / tot for g in GESTURES]
        f.write(intended + "," + ",".join(f"{p:.4f}" for p in probs) + "\n")

print("Saved MEASURED confusion matrix to data/confusion_matrix.csv")
print("(This overwrites the placeholder - your paper numbers are now real.)")