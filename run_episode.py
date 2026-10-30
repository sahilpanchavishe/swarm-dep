# run_episode.py
# Clean dependability scenario: a line of robots driving straight forward.
# At t=STOP_TIME the operator issues STOP. Robots that miss it (packet loss or
# gesture misclassification) keep driving -> still moving at the deadline -> VIOLATION.
# No formation / repulsion, so the failure mechanism is unambiguous.

import numpy as np
from robot import Robot, V_MAX
from controller import force_to_cmd
from channel_model import corrupt_gesture, packet_lost
from safety import T_STOP, V_STOPPED

DT = 0.02

def run_episode(N, loss_rate, burst_len, seed, latch=True, misclassify=True):
    rng = np.random.default_rng(seed)

    # Robots spread in a line, 3 m apart, all heading in +x (theta=0).
    robots = [Robot(x=i * 3.0, y=0.0, theta=0.0, robot_id=i) for i in range(N)]

    stop_issued_time = 1.0
    deadline = stop_issued_time + T_STOP
    # Commands: DRIVE forward at t=0 (always delivered), STOP at t=1.0 (lossy).
    schedule = [(0.0, "DRIVE"), (stop_issued_time, "STOP")]

    current_cmd = ["WAIT"] * N
    burst_remaining = [0] * N
    speed_after_deadline = [0.0] * N
    n_missed_stop = 0

    sim_t = 0.0
    steps = 0
    MAX_STEPS = int(3.0 / DT)
    sched_idx = 0

    while steps < MAX_STEPS:
        # --- Deliver scheduled command ---
        if sched_idx < len(schedule) and sim_t >= schedule[sched_idx][0]:
            intended = schedule[sched_idx][1]
            for i in range(N):
                if intended == "STOP":
                    # Loss applies ONLY to STOP (swarm already moving).
                    if burst_remaining[i] > 0:
                        lost = True
                        burst_remaining[i] -= 1
                    else:
                        lost = packet_lost(loss_rate, rng)
                        if lost and burst_len > 1:
                            burst_remaining[i] = int(rng.integers(0, burst_len))
                    if lost:
                        if not latch:
                            current_cmd[i] = "WAIT"
                        else:
                            n_missed_stop += 1    # keeps DRIVE -> dangerous
                    else:
                        # Received. Gesture may be misclassified (if enabled).
                        if misclassify:
                            received = corrupt_gesture("STOP", rng)
                        else:
                            received = "STOP"
                        if received != "STOP":
                            current_cmd[i] = "DRIVE"   # misread -> keeps driving
                            n_missed_stop += 1
                        else:
                            current_cmd[i] = "STOP"
                else:
                    current_cmd[i] = "DRIVE"           # initial drive, always delivered
            sched_idx += 1

        # --- Each robot acts ---
        for i, r in enumerate(robots):
            if current_cmd[i] == "DRIVE":
                v_cmd, w_cmd = V_MAX, 0.0      # drive straight forward
            else:                              # STOP or WAIT
                v_cmd, w_cmd = 0.0, 0.0
            r.step(v_cmd, w_cmd, DT)

            if sim_t >= deadline:
                speed_after_deadline[i] = max(speed_after_deadline[i], abs(r.v))

        sim_t += DT
        steps += 1

    n_still_moving = sum(1 for s in speed_after_deadline if s > V_STOPPED)
    violated = n_still_moving > 0

    return {
        "N": N, "loss_rate": loss_rate, "burst_len": burst_len,
        "seed": seed, "latch": latch, "violated": violated,
        "n_still_moving": n_still_moving, "n_missed_stop": n_missed_stop,
    }


if __name__ == "__main__":
    # Perfect channel: no loss, no misclassification -> must be safe.
    print("Perfect   :", run_episode(N=8, loss_rate=0.0, burst_len=1, seed=0, misclassify=False))

    # Misclassification only (perfect network, real gesture errors).
    mis = sum(run_episode(N=8, loss_rate=0.0, burst_len=1, seed=s)["violated"]
              for s in range(20))
    print(f"Misclass only : {mis}/20 violated")

    # Heavy loss + misclassification.
    heavy = sum(run_episode(N=8, loss_rate=0.4, burst_len=5, seed=s)["violated"]
                for s in range(20))
    print(f"Heavy-loss    : {heavy}/20 violated")