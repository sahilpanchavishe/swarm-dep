# build_confusion_voted.py
# Temporal voting: group consecutive frames of the same gesture into windows
# and take the MAJORITY vote -> one decision per window (= one command instance).
# More realistic than per-frame, gives near-independent samples, usually higher accuracy.

import glob, csv
from collections import defaultdict, Counter
from classifier import classify

GESTURES = ["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]
WINDOW = 15   # frames per decision (~0.5 s). Each window = one command instance.

counts = defaultdict(lambda: defaultdict(int))
per_correct = defaultdict(int); per_total = defaultdict(int)
total_instances = 0; total_correct = 0

for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    seq = defaultdict(list)   # gesture -> ordered list of per-frame predictions
    with open(path) as f:
        for row in csv.DictReader(f):
            g = row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords += [float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            seq[g].append(classify(coords, row.get("handedness","Right")))
    for g, preds in seq.items():
        for i in range(0, len(preds), WINDOW):
            window = preds[i:i+WINDOW]
            if len(window) < WINDOW//2:   # skip tiny leftover chunk
                continue
            voted = Counter(window).most_common(1)[0][0]
            counts[g][voted]+=1
            per_total[g]+=1; total_instances+=1
            if voted==g:
                per_correct[g]+=1; total_correct+=1

print(f"Temporal voting (window={WINDOW} frames = one command instance)")
print(f"Total command instances: {total_instances}\n")
print("Per-gesture accuracy (voted):")
for g in GESTURES:
    t=per_total[g]; a=per_correct[g]/t*100 if t else 0
    print(f"  {g:8s}: {a:5.1f}%  ({per_correct[g]}/{t})")
print(f"\nOverall VOTED accuracy: {total_correct/total_instances*100:.1f}%")
print("(Compare to per-frame 83.4%)")

# Save the voted confusion matrix = the correct per-COMMAND error model.
with open("data/confusion_matrix.csv","w",newline="") as f:
    f.write("# MEASURED confusion matrix (temporal voting, window=15) - 8 participants\n")
    f.write("# Rows=intended, Cols=recognised. Each row sums to 1.0.\n")
    f.write("intended,"+",".join(GESTURES)+"\n")
    for intended in GESTURES:
        tot=sum(counts[intended].values())
        probs=[counts[intended][g]/tot if tot else (1.0 if g==intended else 0.0) for g in GESTURES]
        f.write(intended+","+",".join(f"{p:.4f}" for p in probs)+"\n")
print("\nSaved VOTED confusion matrix to data/confusion_matrix.csv")