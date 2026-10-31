# per_condition_cb.py
# Per-condition accuracy on the COUNTERBALANCED recordings.
# Because condition order was randomized across participants, accuracy
# differences here ARE attributable to the condition (no practice confound).

import glob, csv, os
from collections import defaultdict
from classifier import classify

GESTURES = ["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]

def cond(fn):
    n = os.path.basename(fn).lower()
    d = "far" if "far" in n else "near"
    l = "dim" if "dim" in n else "bright"
    return f"{d}_{l}"

correct = defaultdict(int); total = defaultdict(int)
g_correct = defaultdict(lambda: defaultdict(int)); g_total = defaultdict(lambda: defaultdict(int))

for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    c = cond(path)
    with open(path) as f:
        for row in csv.DictReader(f):
            g = row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords += [float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            total[c]+=1; g_total[c][g]+=1
            if classify(coords, row.get("handedness","Right"))==g:
                correct[c]+=1; g_correct[c][g]+=1

conds = sorted(total.keys())
print("=== Accuracy by condition (counterbalanced data) ===\n")
for c in conds:
    a = correct[c]/total[c]*100 if total[c] else 0
    print(f"  {c:12s}: {a:5.1f}%   ({correct[c]}/{total[c]} frames)")

print("\n=== Per-gesture by condition ===")
print(f"\n{'Gesture':10s}" + "".join(f"{c:>14s}" for c in conds))
for g in GESTURES:
    line=f"{g:10s}"
    for c in conds:
        t=g_total[c][g]; a=g_correct[c][g]/t*100 if t else 0
        line+=f"{a:13.1f}%"
    print(line)

with open("data/accuracy_by_condition_cb.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["condition","accuracy_pct","frames"])
    for c in conds:
        a=correct[c]/total[c]*100 if total[c] else 0
        w.writerow([c, round(a,2), total[c]])
print("\nSaved data/accuracy_by_condition_cb.csv")