# threshold_sensitivity_cb.py
# Rigor check: sweep each threshold and confirm the chosen value sits on a
# stable plateau (not a fragile spike). Uses the clean counterbalanced data.

import glob, csv
import classifier
from classifier import classify

GESTURES = ["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]

data=[]
for path in glob.glob("data/gesture_recordings_cb/*.csv"):
    with open(path) as f:
        for row in csv.DictReader(f):
            g=row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords += [float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            data.append((coords, row.get("handedness","Right"), g))

def overall_acc():
    c=sum(1 for coords,h,g in data if classify(coords,h)==g)
    return c/len(data)*100

print("Sweeping FINGER_EXT_RATIO (current=1.05):")
for v in [0.95,1.00,1.05,1.10,1.15,1.20]:
    classifier.FINGER_EXT_RATIO=v
    print(f"  ratio={v:.2f} -> {overall_acc():5.1f}%")
classifier.FINGER_EXT_RATIO=1.05

print("\nSweeping THUMB_PALM_DIST (current=0.55):")
for v in [0.40,0.50,0.55,0.60,0.70,0.80]:
    classifier.THUMB_PALM_DIST=v
    print(f"  dist={v:.2f} -> {overall_acc():5.1f}%")
classifier.THUMB_PALM_DIST=0.55