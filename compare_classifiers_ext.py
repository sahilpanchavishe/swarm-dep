# compare_classifiers_ext.py - extended classifier comparison (frame-level + hold-level temporal).
# Question: does the STOP safety problem survive stronger / temporal classifiers?
# Protocol: leave-ONE-PARTICIPANT-out (no leakage). Metrics: accuracy + STOP misread rate.
#  - Frame-level: classify each frame, then majority-vote over a 15-frame window per hold.
#  - Hold-level TEMPORAL: summarise each hold's landmark TRAJECTORY (mean/std/min/max/last of the
#    63 normalized coords + duration) and classify the whole gesture at once. This captures the
#    "use the motion, not a frame" idea that sequence models (GRU/LSTM) exploit, with no DL deps.
import csv, glob
import numpy as np
from collections import Counter
from classifier import classify, normalize
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

G = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]; WIN = 15
GI = {g: i for i, g in enumerate(G)}

# load frames, grouped into holds (contiguous same-gesture blocks per file)
frames = []          # (pid, gesture, normalized_feat_63, rule_pred)
holds = []           # (pid, gesture, trajectory array [T,63])
GAP = 0.2   # seconds; a new hold starts after a pause OR a gesture change
for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    cur = []; curg = None; lastt = None
    for r in csv.DictReader(open(path)):
        g = r["intended_gesture"]
        if g not in G: continue
        t = float(r["timestamp"])
        raw = np.array([float(r[f"{a}{i}"]) for i in range(21) for a in "xyz"]).reshape(21, 3)
        f = normalize(raw).flatten()
        frames.append((r["participant"], g, f, classify(raw, r.get("handedness", "Right"))))
        if cur and (g != curg or (lastt is not None and t - lastt > GAP)):
            holds.append((cur[0][0], curg, np.array([c[1] for c in cur]))); cur = []
        cur.append((r["participant"], f)); curg = g; lastt = t
    if cur: holds.append((cur[0][0], curg, np.array([c[1] for c in cur])))

parts = sorted(set(f[0] for f in frames))

# ---- frame-level ----
Xf = np.array([f[2] for f in frames]); yf = np.array([f[1] for f in frames])
pf = np.array([f[0] for f in frames]); rule = np.array([f[3] for f in frames])

def hold_vote(preds, labels):
    k = n = sk = sn = 0; i = 0
    while i < len(labels):
        j = i
        while j < len(labels) and labels[j] == labels[i]: j += 1
        for s in range(i, j, WIN):
            w = preds[s:min(j, s + WIN)]
            if len(w) < WIN // 2: continue
            v = Counter(w).most_common(1)[0][0]; g = labels[i]
            n += 1; k += v == g
            if g == "STOP": sn += 1; sk += v != "STOP"
        i = j
    return k / n, (sk / sn if sn else 0)

frame_models = {"KNN(k=5)": KNeighborsClassifier(5), "SVM(RBF)": SVC(C=10, gamma="scale"),
                "RandomForest": RandomForestClassifier(200, random_state=0),
                "XGBoost": XGBClassifier(n_estimators=300, max_depth=5, random_state=0, verbosity=0),
                "MLP(128,64)": MLPClassifier((128, 64), max_iter=600, random_state=0)}

out = []
print(f"{len(frames)} frames, {len(holds)} holds, {len(parts)} participants, leave-one-participant-out\n")
print("FRAME-LEVEL (vote over 15 frames)")
print(f"{'model':<16}{'hold acc':>10}{'STOP misread':>14}")
ha = [hold_vote(rule[pf == p], yf[pf == p])[0] for p in parts]
sm = [hold_vote(rule[pf == p], yf[pf == p])[1] for p in parts]
out.append(("rule-based(ours)", np.mean(ha), np.mean(sm), np.std(sm)))
print(f"{'rule-based(ours)':<16}{np.mean(ha)*100:>9.1f}%{np.mean(sm)*100:>13.2f}%")
for name, base in frame_models.items():
    ha, sm = [], []
    for p in parts:
        tr, te = pf != p, pf == p
        sc = StandardScaler().fit(Xf[tr])
        yt = np.array([GI[g] for g in yf[tr]]) if name == "XGBoost" else yf[tr]
        clf = base.__class__(**base.get_params()).fit(sc.transform(Xf[tr]), yt)
        pr = clf.predict(sc.transform(Xf[te]))
        if name == "XGBoost": pr = np.array([G[i] for i in pr])
        h, s = hold_vote(pr, yf[te]); ha.append(h); sm.append(s)
    out.append((name, np.mean(ha), np.mean(sm), np.std(sm)))
    print(f"{name:<16}{np.mean(ha)*100:>9.1f}%{np.mean(sm)*100:>13.2f}%")

# ---- hold-level temporal (summary of the whole trajectory) ----
def summ(traj):
    return np.concatenate([traj.mean(0), traj.std(0), traj.min(0), traj.max(0), traj[-1], [len(traj)]])
Xh = np.array([summ(h[2]) for h in holds]); yh = np.array([h[1] for h in holds]); ph = np.array([h[0] for h in holds])
print("\nHOLD-LEVEL TEMPORAL (whole-gesture trajectory summary)")
print(f"{'model':<16}{'hold acc':>10}{'STOP misread':>14}")
for name, base in {"SVM(RBF)": SVC(C=10, gamma="scale"),
                   "XGBoost": XGBClassifier(n_estimators=300, max_depth=5, random_state=0, verbosity=0)}.items():
    acc, sm = [], []
    for p in parts:
        tr, te = ph != p, ph == p
        sc = StandardScaler().fit(Xh[tr])
        yt = np.array([GI[g] for g in yh[tr]]) if name == "XGBoost" else yh[tr]
        clf = base.__class__(**base.get_params()).fit(sc.transform(Xh[tr]), yt)
        pr = clf.predict(sc.transform(Xh[te]))
        if name == "XGBoost": pr = np.array([G[i] for i in pr])
        acc.append((pr == yh[te]).mean())
        st = yh[te] == "STOP"; sm.append((pr[st] != "STOP").mean() if st.any() else 0)
    out.append(("hold-" + name, np.mean(acc), np.mean(sm), np.std(sm)))
    print(f"{name:<16}{np.mean(acc)*100:>9.1f}%{np.mean(sm)*100:>13.2f}%")

with open("data/classifier_comparison.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "hold_acc", "stop_misread", "stop_misread_sd_across_folds"])
    for m, a, s, sd in out: w.writerow([m, round(a, 4), round(s, 4), round(sd, 4)])
print("\nSTOP errors are dominated by STOP->CLUSTER (open palm vs OK-sign). GRU (train_gru.py) still to run.")
