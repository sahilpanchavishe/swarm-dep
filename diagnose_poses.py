# diagnose_poses.py
# For each intended gesture, prints the most common finger-extension pattern
# actually present in the recorded data. This tells us what poses the team
# used, so the classifier rules can be fit to the real data.

import glob
import csv
import numpy as np
from collections import Counter
from classifier import normalize, finger_extended, thumb_extended

GESTURES = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]
patterns = {g: Counter() for g in GESTURES}

for path in sorted(glob.glob("data/gesture_recordings/*.csv")):
    with open(path) as f:
        for row in csv.DictReader(f):
            g = row["intended_gesture"]
            if g not in GESTURES:
                continue
            handed = row.get("handedness", "Right")
            coords = []
            for i in range(21):
                coords += [float(row[f"x{i}"]), float(row[f"y{i}"]), float(row[f"z{i}"])]
            lm = normalize(np.asarray(coords).reshape(21, 3))
            pat = (
                int(thumb_extended(lm, handed)),
                int(finger_extended(lm, 5, 6, 8)),     # index
                int(finger_extended(lm, 9, 10, 12)),   # middle
                int(finger_extended(lm, 13, 14, 16)),  # ring
                int(finger_extended(lm, 17, 18, 20)),  # pinky
            )
            patterns[g][pat] += 1

print("Pattern = (thumb, index, middle, ring, pinky), 1=extended 0=curled")
print("Showing the top 3 patterns for each gesture:\n")
for g in GESTURES:
    total = sum(patterns[g].values())
    print(f"{g}:")
    for pat, cnt in patterns[g].most_common(3):
        print(f"   {pat}  {cnt/total*100:5.1f}%")
    print()