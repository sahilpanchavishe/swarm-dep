# train_gru.py - the true sequence-model (GRU) test: run on your PC (needs torch).
# NOTE: this script was written but NOT executed in the cloud sandbox (torch would not install
# there). Sanity-check the first run: it should print ~1088 holds, 8 participants, and numbers in
# a plausible range. If something looks off, tell Claude before trusting the result.
#
# What it does: trains a GRU on each gesture hold as a SEQUENCE of 63-dim normalized landmark
# vectors (true temporal modelling, like RAIST's BiGRU), leave-ONE-PARTICIPANT-out, and reports
# hold accuracy + STOP misread rate - directly comparable to compare_classifiers_ext.py.
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
print(f"{len(holds)} holds, {len(parts)} participants, leave-one-participant-out GRU")

class GRUNet(nn.Module):
    def __init__(self, d=63, h=64, c=6):
        super().__init__(); self.gru = nn.GRU(d, h, batch_first=True); self.fc = nn.Linear(h, c)
    def forward(self, x, lens):
        packed = nn.utils.rnn.pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
        _, hn = self.gru(packed); return self.fc(hn[-1])

def batches(data, bs=32):
    for i in range(0, len(data), bs):
        chunk = data[i:i + bs]
        xs = [torch.tensor(h[2]) for h in chunk]; lens = [len(x) for x in xs]
        X = pad_sequence(xs, batch_first=True); y = torch.tensor([GI[h[1]] for h in chunk])
        yield X, torch.tensor(lens), y

accs, sms = [], []
for p in parts:
    tr = [h for h in holds if h[0] != p]; te = [h for h in holds if h[0] == p]
    np.random.shuffle(tr)
    net = GRUNet(); opt = torch.optim.Adam(net.parameters(), 1e-3); lossf = nn.CrossEntropyLoss()
    for epoch in range(40):
        net.train()
        for X, lens, y in batches(tr):
            opt.zero_grad(); loss = lossf(net(X, lens), y); loss.backward(); opt.step()
    net.eval(); correct = n = sk = sn = 0
    with torch.no_grad():
        for X, lens, y in batches(te):
            pred = net(X, lens).argmax(1)
            correct += (pred == y).sum().item(); n += len(y)
            for pr, gt in zip(pred.tolist(), y.tolist()):
                if gt == GI["STOP"]: sn += 1; sk += pr != GI["STOP"]
    accs.append(correct / n); sms.append(sk / sn if sn else 0)
    print(f"  hold-out {p}: acc {100*correct/n:.1f}%  STOP misread {100*sk/max(sn,1):.1f}% (n_STOP={sn})")

print(f"\nGRU  hold acc {100*np.mean(accs):.1f}%   STOP misread {100*np.mean(sms):.2f}% "
      f"(SD across folds {100*np.std(sms):.1f})")
with open("data/gru_result.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["model", "hold_acc", "stop_misread", "stop_misread_sd"])
    w.writerow(["GRU", round(np.mean(accs), 4), round(np.mean(sms), 4), round(np.std(sms), 4)])
print("wrote data/gru_result.csv  -- send this to Claude to fold into the comparison table")
