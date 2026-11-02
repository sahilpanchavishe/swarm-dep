# train_advanced.py - the two frontier models: 1D-CNN and ST-GCN (skeleton graph net).
# Run on your PC (needs torch). Same holds, same leave-ONE-PARTICIPANT-out protocol, same metrics
# as compare_classifiers_ext.py / train_gru.py, so all rows are directly comparable.
#
#   1D-CNN : temporal convolution over the 63-dim landmark vector sequence.
#   ST-GCN : models the hand as a GRAPH of its 21 joints (MediaPipe skeleton) with spatial graph
#            convolution + temporal convolution - the SOTA family for skeleton gesture recognition.
#
# Each hold is resampled to a fixed length T=32 by linear interpolation (standard for action nets).
#
# NOTE: written but NOT executed in the cloud sandbox (torch would not install there). WATCH THE
# FIRST FOLD: it should print ~1088 holds, 8 participants, acc in the 80-95% range. If a fold is
# 100% / 0% or it errors on a tensor shape, STOP and paste me the output before trusting anything.
#
# Install once:  pip install torch
# Run:           python train_advanced.py
import csv, glob
import numpy as np
from classifier import normalize
import torch, torch.nn as nn

G = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]; GI = {g: i for i, g in enumerate(G)}
GAP = 0.2; T = 32
torch.manual_seed(0); np.random.seed(0)

# MediaPipe Hands skeleton: 21 joints, bones as (a,b) pairs
BONES = [(0,1),(1,2),(2,3),(3,4), (0,5),(5,6),(6,7),(7,8), (5,9),(9,10),(10,11),(11,12),
         (9,13),(13,14),(14,15),(15,16), (13,17),(17,18),(18,19),(19,20), (0,17)]
def norm_adj():
    A = np.eye(21, dtype=np.float32)
    for a, b in BONES: A[a, b] = A[b, a] = 1.0
    d = A.sum(1); Dinv = np.diag(1.0 / np.sqrt(d))
    return torch.tensor(Dinv @ A @ Dinv)          # symmetric-normalized adjacency with self-loops
A = norm_adj()

def resample(traj, t=T):                           # traj: (T0, 63) -> (t, 63) linear interp
    T0 = len(traj)
    if T0 == t: return traj
    xi = np.linspace(0, T0 - 1, t)
    return np.stack([np.interp(xi, np.arange(T0), traj[:, c]) for c in range(traj.shape[1])], 1).astype(np.float32)

# segment into holds
holds = []
for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    cur = []; curg = None; lastt = None; pidv = None
    for r in csv.DictReader(open(path)):
        g = r["intended_gesture"]
        if g not in G: continue
        t = float(r["timestamp"])
        raw = np.array([float(r[f"{a}{i}"]) for i in range(21) for a in "xyz"]).reshape(21, 3)
        f = normalize(raw).flatten().astype(np.float32)
        if cur and (g != curg or (lastt is not None and t - lastt > GAP)):
            holds.append((pidv, curg, resample(np.array(cur)))); cur = []
        cur.append(f); curg = g; lastt = t; pidv = r["participant"]
    if cur: holds.append((pidv, curg, resample(np.array(cur))))
parts = sorted(set(h[0] for h in holds))
print(f"{len(holds)} holds, {len(parts)} participants, fixed length T={T}, leave-one-participant-out\n")

class CNN1D(nn.Module):
    def __init__(self, c=6):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(63, 64, 5, padding=2), nn.ReLU(), nn.BatchNorm1d(64),
            nn.Conv1d(64, 128, 5, padding=2), nn.ReLU(), nn.BatchNorm1d(128),
            nn.AdaptiveAvgPool1d(1))
        self.fc = nn.Linear(128, c)
    def forward(self, x):                          # x: (N, 63, T)
        return self.fc(self.net(x).squeeze(-1))

class STGCNBlock(nn.Module):
    def __init__(self, cin, cout, Amat, tk=9):
        super().__init__()
        self.register_buffer("A", Amat)
        self.gconv = nn.Conv2d(cin, cout, 1)
        self.tconv = nn.Conv2d(cout, cout, (tk, 1), padding=((tk - 1) // 2, 0))
        self.bn = nn.BatchNorm2d(cout); self.relu = nn.ReLU()
        self.res = nn.Conv2d(cin, cout, 1) if cin != cout else nn.Identity()
    def forward(self, x):                          # x: (N, C, T, V)
        res = self.res(x)
        x = torch.einsum("nctv,vw->nctw", x, self.A)   # spatial graph aggregation over joints
        x = self.tconv(self.gconv(x))
        return self.relu(self.bn(x) + res)

class STGCN(nn.Module):
    def __init__(self, Amat, c=6):
        super().__init__()
        self.b1 = STGCNBlock(3, 32, Amat); self.b2 = STGCNBlock(32, 64, Amat)
        self.fc = nn.Linear(64, c)
    def forward(self, x):                          # x: (N, 3, T, V=21)
        x = self.b2(self.b1(x))
        return self.fc(x.mean(dim=(2, 3)))         # global average over time and joints

def to_cnn(batch):   # (N,63,T)
    return torch.tensor(np.stack([h[2].T for h in batch]))
def to_gcn(batch):   # (N,3,T,21)
    arr = np.stack([h[2].reshape(T, 21, 3).transpose(2, 0, 1) for h in batch])
    return torch.tensor(arr)

def run(kind):
    accs, sms = [], []
    for p in parts:
        tr = [h for h in holds if h[0] != p]; te = [h for h in holds if h[0] == p]
        rng = np.random.default_rng(0); rng.shuffle(tr)
        net = CNN1D() if kind == "1D-CNN" else STGCN(A)
        opt = torch.optim.Adam(net.parameters(), 1e-3); lossf = nn.CrossEntropyLoss()
        feat = to_cnn if kind == "1D-CNN" else to_gcn
        for _ in range(40):
            net.train()
            for i in range(0, len(tr), 32):
                b = tr[i:i + 32]
                X = feat(b); y = torch.tensor([GI[h[1]] for h in b])
                opt.zero_grad(); lossf(net(X), y).backward(); opt.step()
        net.eval(); correct = n = sk = sn = 0
        with torch.no_grad():
            for i in range(0, len(te), 32):
                b = te[i:i + 32]
                pred = net(feat(b)).argmax(1); y = [GI[h[1]] for h in b]
                for pr, gt in zip(pred.tolist(), y):
                    correct += pr == gt; n += 1
                    if gt == GI["STOP"]: sn += 1; sk += pr != GI["STOP"]
        accs.append(correct / n); sms.append(sk / sn if sn else 0)
        print(f"  [{kind:<7}] hold-out {p}: acc {100*correct/n:4.1f}%  STOP misread {100*sk/max(sn,1):5.1f}% (n_STOP={sn})")
    return np.mean(accs), np.mean(sms), np.std(sms)

rows = []
for kind in ["1D-CNN", "ST-GCN"]:
    a, s, sd = run(kind)
    rows.append((kind, a, s, sd))
    print(f"==> {kind:<7} hold acc {100*a:.1f}%   STOP misread {100*s:.2f}%  (SD across folds {100*sd:.1f})\n")

with open("data/advanced_result.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "hold_acc", "stop_misread", "stop_misread_sd"])
    for name, a, s, sd in rows: w.writerow([name, round(a, 4), round(s, 4), round(sd, 4)])
print("wrote data/advanced_result.csv  -- send this to Claude to fold into the comparison table")
