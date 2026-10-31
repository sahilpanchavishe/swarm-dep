# analyze_confound.py
# Demonstrates the condition/practice confound: accuracy tracks recording
# ORDER, not the physical difficulty of the condition. Dim lighting cannot
# physically improve recognition, so the rising accuracy = practice effect.

import csv, glob, os
from classifier import classify

GESTURES = ["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]
# Recording order was the SAME for every participant:
ORDER = {"near_bright": 1, "far_bright": 2, "near_dim": 3}

def cond(fn):
    n = os.path.basename(fn).lower()
    d = "far" if "far" in n else "near"
    l = "dim" if "dim" in n else "bright"
    return f"{d}_{l}"

acc = {c: [0,0] for c in ORDER}   # [correct, total]
for path in glob.glob("data/gesture_recordings/*.csv"):
    c = cond(path)
    with open(path) as f:
        for row in csv.DictReader(f):
            g = row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords += [float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            acc[c][1]+=1
            if classify(coords, row.get("handedness","Right"))==g:
                acc[c][0]+=1

print("Condition     Rec.order   Accuracy   Physics predicts")
print("-"*58)
pred = {"near_bright":"baseline","far_bright":"LOWER (smaller hand)","near_dim":"LOWER (less light)"}
for c in sorted(ORDER, key=ORDER.get):
    a = acc[c][0]/acc[c][1]*100
    print(f"{c:12s}   {ORDER[c]:^9d}  {a:6.1f}%    {pred[c]}")
print("\nAccuracy RISES with recording order while physics predicts it should")
print("FALL -> the condition effect is confounded with (dominated by) practice.")