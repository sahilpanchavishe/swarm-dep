# significance_tests.py
# Two-proportion z-tests for the main claims (no scipy needed).
#  (1) N-scaling: does baseline violation rate differ by swarm size?
#  (2) Condition effect: does recognition accuracy differ by condition?

import math, csv, glob, os
from collections import defaultdict, Counter
from classifier import classify

def ztest(c1, n1, c2, n2):
    p1, p2 = c1/n1, c2/n2
    p = (c1+c2)/(n1+n2)
    se = math.sqrt(p*(1-p)*(1/n1 + 1/n2))
    if se == 0: return 0.0, 1.0
    z = (p1-p2)/se
    return z, math.erfc(abs(z)/math.sqrt(2))   # two-sided p

print("=== (1) N-scaling: baseline (0% loss) violation rate by swarm size ===")
base = {}
with open("data/study_results.csv") as f:
    for row in csv.DictReader(f):
        if float(row["loss_rate"])==0.0:
            N=int(row["N"]); n=int(row["n_seeds"])
            base[N]=(round(float(row["violation_rate"])*n), n)
for a,b in [(8,16),(16,32),(8,32)]:
    z,p = ztest(base[a][0],base[a][1], base[b][0],base[b][1])
    print(f"  N={a} ({base[a][0]}/{base[a][1]}) vs N={b} ({base[b][0]}/{base[b][1]}): "
          f"z={z:.2f}, p={p:.4f} -> {'SIGNIFICANT' if p<0.05 else 'not significant'}")

print("\n=== (2) Condition recognition accuracy (voted instances) ===")
GESTURES=["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]; WINDOW=15
cond_c=defaultdict(int); cond_n=defaultdict(int)
def cond_of(fn):
    n=os.path.basename(fn).lower()
    return f"{'far' if 'far' in n else 'near'}_{'dim' if 'dim' in n else 'bright'}"
for path in glob.glob("data/gesture_recordings_cb/*.csv"):
    c=cond_of(path); seq=defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            g=row["intended_gesture"]
            if g not in GESTURES: continue
            coords=[]
            for i in range(21):
                coords+=[float(row[f"x{i}"]),float(row[f"y{i}"]),float(row[f"z{i}"])]
            seq[g].append(classify(coords,row.get("handedness","Right")))
    for g,preds in seq.items():
        for i in range(0,len(preds),WINDOW):
            w=preds[i:i+WINDOW]
            if len(w)<WINDOW//2: continue
            cond_n[c]+=1
            if Counter(w).most_common(1)[0][0]==g: cond_c[c]+=1
for c in sorted(cond_n):
    print(f"  {c:12s}: {cond_c[c]/cond_n[c]*100:.1f}%  ({cond_c[c]}/{cond_n[c]})")
print()
conds=sorted(cond_n)
for i in range(len(conds)):
    for j in range(i+1,len(conds)):
        a,b=conds[i],conds[j]
        z,p=ztest(cond_c[a],cond_n[a], cond_c[b],cond_n[b])
        print(f"  {a} vs {b}: z={z:.2f}, p={p:.4f} -> {'SIGNIFICANT' if p<0.05 else 'not significant'}")