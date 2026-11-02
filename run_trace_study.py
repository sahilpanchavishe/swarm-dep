# run_trace_study.py - replay MEASURED Wi-Fi loss traces (data/wifi_runs/R*/session*/rx_*.csv) through the
# same robot/safety model as sim_v2 (shared misread, 30 Hz rebroadcast with latching, optional fail-safe timeout).
# Each robot draws one measured receiver trace and a random start offset (so the STOP lands at a random phase of
# the real burst process); robots are independent (cross-receiver overlap measured to be small).
# Usage: python3 run_trace_study.py [wifi_runs_dir]      Writes data/trace_study.csv
import csv, glob, json, math, sys
import numpy as np
from multiprocessing import Pool
from robot import Robot, V_MAX, A_MAX
from safety import T_STOP, V_STOPPED
from sim_v2 import DT, RATE_HZ
ROOT = sys.argv[1] if len(sys.argv) > 1 else "data/wifi_runs"
PM = json.load(open("data/misread_vs_window.json"))["stop"][0]["p"]
SESS = ["session1_quiet", "session2_busy", "session3_far"]; NPKT = 18000
SLACK = T_STOP - 0.033 - V_MAX / A_MAX          # fail-safe timeout bound (0.234 s)

def load(rcv, sess):
    fn = glob.glob(f"{ROOT}/{rcv}/{sess}/rx_*.csv")[0]
    got = {int(r["seq"]) for r in csv.DictReader(open(fn))}
    return np.array([i not in got for i in range(NPKT)], dtype=bool)   # True = lost
TRACES = {(r, s): load(r, s) for r in ("R2", "R4") for s in SESS}

def episode(N, trace, seed, timeout_s=None, issue_stop=True, rec_delay_s=0.033, t_stop_cmd=1.0, sim_s=3.0):
    rng = np.random.default_rng(seed)
    off = rng.integers(0, len(trace), size=N)
    misread = False                                # channel-only violation; misread added in closed form
    robots = [Robot(x=i * 3.0, y=0.0, theta=0.0, robot_id=i) for i in range(N)]
    t_emit = t_stop_cmd + rec_delay_s
    latched = ["DRIVE"] * N; last_rx = [0.0] * N; failsafe = [False] * N
    deadline = t_stop_cmd + T_STOP; v_after = [0.0] * N; k = 0; next_tx = 0.0; t = 0.0
    while t < sim_s:
        if t >= next_tx - 1e-9:
            cmd = "STOP" if (issue_stop and t >= t_emit) else "DRIVE"
            for i in range(N):
                if not trace[(off[i] + k) % len(trace)]:
                    last_rx[i] = t
                    if latched[i] != "STOP": latched[i] = cmd
            k += 1; next_tx += 1.0 / RATE_HZ
        for i, r in enumerate(robots):
            if timeout_s is not None and t - last_rx[i] > timeout_s: failsafe[i] = True
            stop = latched[i] == "STOP" or failsafe[i]
            r.step(0.0 if stop else V_MAX, 0.0, DT)
            if t >= deadline: v_after[i] = max(v_after[i], abs(r.v))
        t += DT
    return sum(v > V_STOPPED for v in v_after) > 0

def runs(lost):
    out, c = [], 0
    for x in lost:
        if x: c += 1
        elif c: out.append(c); c = 0
    if c: out.append(c)
    return out

def cell(a):
    rcv, sess, N, timeout, seeds = a
    tr = TRACES[(rcv, sess)]
    pl = sum(episode(N, tr, s, timeout) for s in range(seeds)) / seeds
    se = math.sqrt(max(pl * (1 - pl), 1e-12) / seeds)
    k = 8                                           # broadcasts in the slack window (see analytic_violation)
    q = float(np.mean([tr[j:j + k].all() for j in range(len(tr) - k + 1)]))
    nuis_per_min = sum(1 for b in runs(tr) if b >= math.ceil(SLACK * RATE_HZ)) / (NPKT / RATE_HZ / 60)
    return {"receiver": rcv, "session": sess, "N": N, "timeout_s": "none" if timeout is None else round(timeout, 3),
            "p_loss_violation": round(pl, 4), "ci95": round(1.96 * se, 4),
            "empirical_q_per_robot": round(q, 5), "closed_form_N": round(1 - (1 - q) ** N, 4),
            "total_violation": round(PM + (1 - PM) * pl, 4),
            "failsafe_trips_per_min_per_robot": round(nuis_per_min, 2) if timeout is not None else 0.0,
            "p_misread": round(PM, 4), "seeds": seeds}

if __name__ == "__main__":
    grid = [(r, s, N, to, 500) for r in ("R2", "R4") for s in SESS for N in (1, 8) for to in (None, SLACK)]
    with Pool() as p: rows = p.map(cell, grid)
    with open("data/trace_study.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("done", len(rows), "rows; fail-safe timeout bound %.3f s; p_misread %.4f" % (SLACK, PM))
