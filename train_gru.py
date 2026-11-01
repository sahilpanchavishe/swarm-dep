# train_gru.py - the true sequence-model test: run on your PC (needs torch).
# Trains recurrent nets on each gesture hold as a SEQUENCE of 63-dim normalized landmark
# vectors (true temporal modelling, like the Robotica 2026 competitor), leave-ONE-PARTICIPANT-out,
# and reports hold accuracy + STOP misread rate - directly comparable to compare_classifiers_ext.py.
#
# Runs FOUR architectures to match the competitor's model set: GRU, LSTM, BiGRU, BiLSTM.
# Expectation: STOP misread stays ~10-13% for all of them, because STOP (open palm) vs CLUSTER
# (OK-sign) is a POSE-SHAPE ambiguity, not a temporal one - sequence modelling can't resolve it.
#
# NOTE: written but NOT executed in the cloud sandbox (torch would not install there). Sanity-check
# the first run: ~1088 holds, 8 participants, per-fold numbers in a believable range.
#
# Install once:  pip install torch
# Run:           python train_gru.py
import csv, glob
import numpy as np
from classifier import normalize
import torch, torch.nn as nn
from torch.nn.utils.rnn import pad_sequence

G = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]; GI = {g: i for i, g in enumerate(G)}
GAP = 0.2
torch.manual_seed(0); np.random.seed(0)

# segment into holds (same rule as compare_classifiers_ext.py)
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
            holds.append((pidv, curg, np.array(cur))); cur = []
        cur.append(f); curg = g; lastt = t; pidv = r["participant"]
    if cur: holds.append((pidv, curg, np.array(cur)))
parts = sorted(set(h[0] for h in holds))
print(f"{len(holds)} holds, {len(parts)} participants, leave-one-participant-out\n")

class RNNNet(nn.Module):
    def __init__(self, kind, d=63, h=64, c=6, bi=False):
        super().__init__()
        rnn = nn.LSTM if kind == "LSTM" else nn.GRU
        self.rnn = rnn(d, h, batch_first=True, bidirectional=bi)
        self.fc = nn.Linear(h * (2 if bi else 1), c)
    def forward(self, x, lens):
        packed = nn.utils.rnn.pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
        out, _ = self.rnn(packed)
        seq, L = nn.utils.rnn.pad_packed_sequence(out, batch_first=True)
        last = seq[torch.arange(seq.size(0)), torch.tensor(L) - 1]   # last valid step (handles bi)
        return self.fc(last)

def batches(data, bs=32):
    for i in range(0, len(data), bs):
        chunk = data[i:i + bs]
        xs = [torch.tensor(h[2]) for h in chunk]; lens = [len(x) for x in xs]
        X = pad_sequence(xs, batch_first=True); y = torch.tensor([GI[h[1]] for h in chunk])
        yield X, lens, y

def run(kind, bi):
    accs, sms = [], []
    for p in parts:
        tr = [h for h in holds if h[0] != p]; te = [h for h in holds if h[0] == p]
        rng = np.random.default_rng(0); rng.shuffle(tr)
        net = RNNNet(kind, bi=bi); opt = torch.optim.Adam(net.parameters(), 1e-3); lossf = nn.CrossEntropyLoss()
        for _ in range(40):
            net.train()
            for X, lens, y in batches(tr):
                opt.zero_grad(); lossf(net(X, lens), y).backward(); opt.step()
        net.eval(); correct = n = sk = sn = 0
        with torch.no_grad():
            for X, lens, y in batches(te):
                pred = net(X, lens).argmax(1)
                correct += (pred == y).sum().item(); n += len(y)
                for pr, gt in zip(pred.tolist(), y.tolist()):
                    if gt == GI["STOP"]: sn += 1; sk += pr != GI["STOP"]
        accs.append(correct / n); sms.append(sk / sn if sn else 0)
        print(f"  [{('Bi' if bi else '')+kind:<7}] hold-out {p}: acc {100*correct/n:4.1f}%  STOP misread {100*sk/max(sn,1):5.1f}% (n_STOP={sn})")
    return np.mean(accs), np.mean(sms), np.std(sms)

rows = []
for kind, bi in [("GRU", False), ("LSTM", False), ("GRU", True), ("LSTM", True)]:
    name = ("Bi" if bi else "") + kind
    a, s, sd = run(kind, bi)
    rows.append((name, a, s, sd))
    print(f"==> {name:<7} hold acc {100*a:.1f}%   STOP misread {100*s:.2f}%  (SD across folds {100*sd:.1f})\n")

with open("data/gru_result.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "hold_acc", "stop_misread", "stop_misread_sd"])
    for name, a, s, sd in rows: w.writerow([name, round(a, 4), round(s, 4), round(sd, 4)])
print("wrote data/gru_result.csv  -- send this to Claude to fold into the comparison table")
