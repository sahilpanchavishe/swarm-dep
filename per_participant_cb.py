# per_participant_cb.py
# Rigor check: does the classifier work for EVERY participant, or just on average?
# Consistent accuracy across all 8 people = the rules generalize (good).

import glob, csv, os
from collections import defaultdict
from classifier import classify
import statistics

GESTURES = ["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]
acc = defaultdict(lambda:[0,0])   # participant -> [correct, total]

for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    pid = os.path.basename(path).split("_")[0]   # P01, P02, ...
    with open(path) as f:
        for row in csv.DictReader(f):
            g = row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords += [float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            acc[pid][1]+=1
            if classify(coords, row.get("handedness","Right"))==g:
                acc[pid][0]+=1

print("Participant   Accuracy")
print("-"*24)
vals=[]
for pid in sorted(acc):
    a=acc[pid][0]/acc[pid][1]*100
    vals.append(a)
    print(f"{pid:10s}   {a:6.1f}%")
print(f"\nmean={statistics.mean(vals):.1f}%  stdev={statistics.pstdev(vals):.1f}%  "
      f"range={min(vals):.1f}-{max(vals):.1f}%")
print("Low stdev + no big outliers = classifier generalizes across people (good).")