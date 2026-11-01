# make_paper_figures.py
# Generates key paper figures into figures/:
#  1. Confusion matrix heatmap
#  2. Latency distribution histogram
#  3. Recognition accuracy by condition (bar chart)
#  4. Swarm STOP-scenario trajectory (illustrates the failure mode)

import os, csv
import numpy as np
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
GESTURES=["CIRCLE","LINE","CLUSTER","SPLIT","STOP","WAIT"]

# 1. Confusion matrix heatmap
M=[]
with open("data/confusion_matrix.csv") as f:
    for line in f:
        if line.startswith("#") or line.startswith("intended"): continue
        parts=line.strip().split(",")
        if len(parts)==7: M.append([float(x) for x in parts[1:]])
M=np.array(M)
fig,ax=plt.subplots(figsize=(6,5))
im=ax.imshow(M, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(6)); ax.set_yticks(range(6))
ax.set_xticklabels(GESTURES, rotation=45, ha="right"); ax.set_yticklabels(GESTURES)
ax.set_xlabel("Recognised"); ax.set_ylabel("Intended")
ax.set_title("Gesture recognition confusion matrix")
for i in range(6):
    for j in range(6):
        ax.text(j,i,f"{M[i,j]:.2f}",ha="center",va="center",
                color="white" if M[i,j]>0.5 else "black", fontsize=8)
fig.colorbar(im, label="Probability")
plt.tight_layout(); plt.savefig("figures/confusion_matrix.png", dpi=200); plt.close()
print("saved figures/confusion_matrix.png")

# 2. Latency histogram
lat=np.loadtxt("data/latency_raw.csv", skiprows=1)
fig,ax=plt.subplots(figsize=(6,4))
ax.hist(lat, bins=30, color="tab:blue", edgecolor="white")
ax.axvline(np.median(lat), color="red", ls="--", label=f"median={np.median(lat):.1f} ms")
ax.set_xlabel("Command latency (ms)"); ax.set_ylabel("Count")
ax.set_title(f"Measured command latency (n={len(lat)})")
ax.legend(); plt.tight_layout(); plt.savefig("figures/latency_histogram.png", dpi=200); plt.close()
print("saved figures/latency_histogram.png")

# 3. Accuracy by condition
conds=[]; accs=[]
with open("data/accuracy_by_condition_voted.csv") as f:
    for row in csv.DictReader(f):
        conds.append(row["condition"]); accs.append(float(row["accuracy_pct"]))
fig,ax=plt.subplots(figsize=(6,4))
bars=ax.bar(conds, accs, color=["tab:green","tab:blue","tab:orange"])
ax.set_ylabel("Recognition accuracy (%)"); ax.set_ylim(0,100)
ax.set_title("Per-command recognition accuracy by condition (voted)")
for b,a in zip(bars,accs):
    ax.text(b.get_x()+b.get_width()/2, a+1, f"{a:.1f}%", ha="center")
plt.tight_layout(); plt.savefig("figures/accuracy_by_condition.png", dpi=200); plt.close()
print("saved figures/accuracy_by_condition.png")

# 4. Swarm STOP-scenario trajectory
from robot import Robot, V_MAX
DT=0.02; N=8
rng=np.random.default_rng(2)
robots=[Robot(0.0, i*0.5, 0.0, i) for i in range(N)]   # a line, all facing +x
missed=set(rng.choice(N, size=2, replace=False))        # 2 robots miss STOP
stop_t=1.0
trajX=[[] for _ in range(N)]; trajY=[[] for _ in range(N)]
t=0.0
for step in range(int(2.5/DT)):
    for i,r in enumerate(robots):
        v = 0.0 if (t>=stop_t and i not in missed) else V_MAX
        r.step(v,0.0,DT)
        trajX[i].append(r.x); trajY[i].append(r.y)
    t+=DT
fig,ax=plt.subplots(figsize=(7,4))
for i in range(N):
    c="tab:red" if i in missed else "tab:green"
    ax.plot(trajX[i], trajY[i], color=c, lw=1.5)
    ax.plot(trajX[i][-1], trajY[i][-1], "o", color=c, ms=7)
ax.plot([],[],color="tab:green",label="received STOP (stopped)")
ax.plot([],[],color="tab:red",label="missed STOP (kept driving)")
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_aspect("equal")
ax.set_title("STOP scenario: robots that miss the STOP keep driving")
ax.legend(loc="upper left", fontsize=8)
plt.tight_layout(); plt.savefig("figures/stop_scenario.png", dpi=200); plt.close()
print("saved figures/stop_scenario.png")

print("\nAll paper figures saved to figures/")