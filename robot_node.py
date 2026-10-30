# robot_node.py
# One robot as its own process: listens for UDP commands, measures latency,
# logs its state over time. Run several of these (one per robot).
# Usage:  python robot_node.py <robot_id> <N> <start_x> <start_y> <start_theta>

import socket
import sys
import time
import json
import numpy as np
from robot import Robot
from controller import compute_force, force_to_cmd
from formations import SHAPES
from protocol import UDP_PORT, BUFFER_SIZE, parse_packet

DT = 0.02

def main():
    rid    = int(sys.argv[1])
    N      = int(sys.argv[2])
    x      = float(sys.argv[3])
    y      = float(sys.argv[4])
    theta  = float(sys.argv[5])

    me = Robot(x, y, theta, robot_id=rid)

    # --- Set up UDP listening socket ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("", UDP_PORT))
    sock.setblocking(False)      # don't freeze the control loop waiting for packets

    current_cmd = "WAIT"
    slots = None
    log = []     # (sim_time, x, y, theta, latency_ms or '')

    sim_t = 0.0
    steps = 0
    MAX_STEPS = 1500

    while steps < MAX_STEPS:
        loop_start = time.perf_counter()
        latency_ms = ""

        # --- Check for a new command (non-blocking) ---
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            pkt = parse_packet(data)
            t_recv = time.perf_counter()
            latency_ms = (t_recv - pkt["t_send"]) * 1000.0   # REAL measured latency
            current_cmd = pkt["command"]
            if current_cmd in SHAPES:
                slots = SHAPES[current_cmd](N)
            print(f"[robot {rid}] seq={pkt['seq']} {current_cmd} "
                  f"latency={latency_ms:.3f} ms")
        except BlockingIOError:
            pass   # no packet this step; latching keeps last command

        # --- Act on current command ---
        if current_cmd == "STOP":
            v, w = 0.0, 0.0
        elif current_cmd == "WAIT":
            v, w = 0.0, 0.0
        elif slots is not None:
            # NOTE: single-robot test has no neighbours; pass empty list.
            fx, fy = compute_force(me, slots[rid], [])
            v, w = force_to_cmd(me, fx, fy, DT)
        else:
            v, w = 0.0, 0.0

        me.step(v, w, DT)
        log.append((round(sim_t, 3), me.x, me.y, me.theta, latency_ms))

        sim_t += DT
        steps += 1
        # pace the loop to ~real time so latency numbers are meaningful
        elapsed = time.perf_counter() - loop_start
        if elapsed < DT:
            time.sleep(DT - elapsed)

    # --- Save this robot's log ---
    with open(f"log_robot_{rid}.csv", "w") as f:
        f.write("t,x,y,theta,latency_ms\n")
        for row in log:
            f.write(",".join(str(v) for v in row) + "\n")
    print(f"[robot {rid}] done, wrote log_robot_{rid}.csv")

if __name__ == "__main__":
    main()