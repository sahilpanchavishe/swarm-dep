# trace.py - diagnostic: watch what one robot actually does around the STOP deadline.
import numpy as np
from robot import Robot
from controller import compute_force, force_to_cmd
from formations import SHAPES
from channel_model import corrupt_gesture, packet_lost
from safety import T_STOP, V_STOPPED

N = 8
DT = 0.02
rng = np.random.default_rng(3)
robots = [Robot(rng.uniform(-1,1), rng.uniform(-1,1),
                rng.uniform(-np.pi,np.pi), robot_id=i) for i in range(N)]
stop_issued_time = 1.0
deadline = stop_issued_time + T_STOP
schedule = [(0.0,"CIRCLE"), (stop_issued_time,"STOP")]
current_cmd = ["WAIT"]*N
slots = [None]*N
sim_t = 0.0; steps = 0; sched_idx = 0
MAX_STEPS = int(3.0/DT)

print(f"deadline={deadline}s  T_STOP={T_STOP}  V_STOPPED={V_STOPPED}")
while steps < MAX_STEPS:
    if sched_idx < len(schedule) and sim_t >= schedule[sched_idx][0]:
        intended = schedule[sched_idx][1]
        print(f"\n--- t={sim_t:.2f}: delivering {intended} ---")
        for i in range(N):
            if packet_lost(0.4, rng):
                print(f"  robot {i}: LOST, keeps '{current_cmd[i]}'")
            else:
                rec = corrupt_gesture(intended, rng)
                current_cmd[i] = rec
                if rec in SHAPES:
                    slots[i] = SHAPES[rec](N, radius=20.0) if rec=="CIRCLE" else SHAPES[rec](N)
                print(f"  robot {i}: got '{rec}'")
        sched_idx += 1

    for i, r in enumerate(robots):
        cmd = current_cmd[i]
        if cmd in ("STOP","WAIT"):
            v, w = 0.0, 0.0
        elif slots[i] is not None:
            fx, fy = compute_force(r, slots[i][i], robots)
            v, w = force_to_cmd(r, fx, fy, DT)
        else:
            v, w = 0.0, 0.0
        r.step(v, w, DT)

    if abs(sim_t - deadline) < 0.25:
        speeds = [f"{r.v:.3f}" for r in robots]
        print(f"t={sim_t:.2f}  cmds={current_cmd}  speeds={speeds}")

    sim_t += DT; steps += 1
    