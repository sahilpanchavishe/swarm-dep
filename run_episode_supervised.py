# run_episode_supervised.py
# Episode WITH a fail-safe supervisor on each robot:
#   - operator re-broadcasts the current command every heartbeat_interval
#   - each robot stops if it hasn't heard a heartbeat within `timeout`
#   - STOP latches until an explicit RESUME
# Measures BOTH safety violations and nuisance stops as `timeout` varies.

import numpy as np
from robot import Robot, V_MAX
from channel_model import corrupt_gesture, packet_lost
from safety import T_STOP, V_STOPPED

DT = 0.02

def run_episode_supervised(N, loss_rate, timeout, seed,
                           heartbeat_interval=0.1, burst_len=5,
                           issue_stop=True):
    """
    timeout     : seconds without a heartbeat before a robot fail-safe stops
    issue_stop  : if True, a real STOP is sent at t=1.0 (safety test).
                  if False, NO stop is ever sent (nuisance test) - any robot
                  that stops did so needlessly.
    Returns violation (bool) and nuisance_stops (count).
    """
    rng = np.random.default_rng(seed)
    robots = [Robot(x=i * 3.0, y=0.0, theta=0.0, robot_id=i) for i in range(N)]

    # Per-robot state.
    current_cmd = ["DRIVE"] * N          # swarm starts driving
    last_heard = [0.0] * N               # sim time each robot last got a heartbeat
    stopped_by_stop = [False] * N        # has this robot latched a real STOP?
    fail_safe_stopped = [False] * N      # did timeout force it to stop?

    stop_time = 1.0 if issue_stop else None
    deadline = (stop_time + T_STOP) if issue_stop else None

    speed_after_deadline = [0.0] * N
    sim_t = 0.0
    steps = 0
    MAX_STEPS = int(3.0 / DT)
    next_heartbeat = 0.0

    while steps < MAX_STEPS:
        # --- Operator broadcasts a heartbeat at regular intervals ---
        if sim_t >= next_heartbeat:
            # What is the operator currently commanding?
            if issue_stop and sim_t >= stop_time:
                intended = "STOP"
            else:
                intended = "DRIVE"

            for i in range(N):
                # Each heartbeat packet can be lost independently.
                if packet_lost(loss_rate, rng):
                    continue    # robot hears nothing this beat
                # Received a heartbeat.
                last_heard[i] = sim_t
                received = corrupt_gesture(intended, rng) if intended == "STOP" else "DRIVE"
                if received == "STOP":
                    stopped_by_stop[i] = True       # latch STOP
            next_heartbeat += heartbeat_interval

        # --- Each robot decides what to do ---
        for i, r in enumerate(robots):
            # Fail-safe: no heartbeat for too long -> stop.
            if (sim_t - last_heard[i]) > timeout:
                fail_safe_stopped[i] = True

            if stopped_by_stop[i] or fail_safe_stopped[i]:
                v_cmd = 0.0
            else:
                v_cmd = V_MAX      # keep driving
            r.step(v_cmd, 0.0, DT)

            if deadline is not None and sim_t >= deadline:
                speed_after_deadline[i] = max(speed_after_deadline[i], abs(r.v))

        sim_t += DT
        steps += 1

    # --- Metrics ---
    if issue_stop:
        # Safety: any robot still moving after a real STOP's deadline.
        violated = any(s > V_STOPPED for s in speed_after_deadline)
        return {"violated": violated, "nuisance_stops": 0}
    else:
        # Nuisance: no STOP was ever issued, so ANY fail-safe stop was needless.
        nuisance = sum(1 for f in fail_safe_stopped if f)
        return {"violated": False, "nuisance_stops": nuisance}


if __name__ == "__main__":
    # Quick sanity check at one timeout value.
    N, loss, timeout = 8, 0.2, 0.3
    saf = sum(run_episode_supervised(N, loss, timeout, seed=s, issue_stop=True)["violated"]
              for s in range(20))
    nui = sum(run_episode_supervised(N, loss, timeout, seed=s, issue_stop=False)["nuisance_stops"]
              for s in range(20))
    print(f"timeout={timeout}s  loss={loss}")
    print(f"  safety violations : {saf}/20 episodes")
    print(f"  nuisance stops    : {nui} (total across 20 episodes, no STOP issued)")