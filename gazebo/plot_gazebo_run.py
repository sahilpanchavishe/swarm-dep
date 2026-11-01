# plot_gazebo_run.py - figures from a logged Gazebo run (real physics data).
# Usage: python3 gazebo/plot_gazebo_run.py data/gazebo_runs/run_N8_loss0.2_seed0.csv
import csv, json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from robot import V_MAX, A_MAX

path = sys.argv[1]
summ = json.load(open(path.replace(".csv", ".json")))
t_stop = 3.0 if len(sys.argv) < 3 else float(sys.argv[2])
tr = {}
for r in csv.DictReader(open(path)):
    d = tr.setdefault(int(r["robot"]), {"fate": r["fate"], "t": [], "x": [], "y": [], "v": []})
    for k in ("t", "x", "y", "v"):
        d[k].append(float(r[k]))
tag = os.path.basename(path)[:-4]
os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
col = lambda f: "tab:red" if f == "DRIVE" else "tab:green"

fig, ax = plt.subplots(figsize=(5, 5.5))
for i, d in tr.items():
    ax.plot(d["x"], d["y"], color=col(d["fate"]), lw=1.5)
    ax.plot(d["x"][-1], d["y"][-1], "o", color=col(d["fate"]), ms=6)
ax.plot([], [], color="tab:green", label="received STOP"); ax.plot([], [], color="tab:red", label="missed STOP (latched DRIVE)")
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_aspect("equal")
ax.set_xlim(-0.1, max(max(d["x"]) for d in tr.values()) + 0.6)
ax.axvline(min(d["x"][0] for d in tr.values()), color="lightgrey", lw=0.8)
ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
ax.set_title(f"Gazebo ground truth, N={summ['N']}, loss={summ['loss_rate']}, seed={summ['seed']}")
plt.tight_layout(); plt.savefig(f"{ROOT}/figures/gazebo_{tag}_traj.png", dpi=200); plt.close()

fig, ax = plt.subplots(figsize=(7, 4))
for i, d in tr.items():
    ax.plot(d["t"], d["v"], color=col(d["fate"]), lw=1, alpha=0.8)
tk = [t_stop + k * 0.01 for k in range(0, 101)]
ax.plot(tk, [max(0.0, V_MAX - A_MAX * (t - t_stop)) for t in tk], "k--", lw=1.5, label="kinematic model")
ax.axvline(t_stop, color="grey", ls=":"); ax.axvline(t_stop + 1.0, color="grey", ls="--", lw=0.8)
ax.text(t_stop, ax.get_ylim()[1], " STOP issued", va="top", fontsize=8, color="grey")
ax.text(t_stop + 1.0, ax.get_ylim()[1], " deadline (T_stop=1 s)", va="top", fontsize=8, color="grey")
ax.plot([], [], color="tab:green", label="Gazebo: received STOP")
ax.plot([], [], color="tab:red", label="Gazebo: missed STOP")
ax.set_xlabel("sim time (s)"); ax.set_ylabel("speed (m/s)"); ax.legend(fontsize=8, loc="center right")
ax.set_title("Robot speed in Gazebo vs kinematic braking model")
plt.tight_layout(); plt.savefig(f"{ROOT}/figures/gazebo_{tag}_speed.png", dpi=200); plt.close()
print("saved figures/gazebo_%s_traj.png and _speed.png" % tag)
