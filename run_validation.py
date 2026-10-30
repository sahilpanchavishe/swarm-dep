# run_validation.py
# Launches N robot processes for the channel validation run, then you
# start the operator separately. Each robot logs its own measured latency.

import subprocess
import sys
import numpy as np

N = 5                    # number of robot processes for this validation
rng = np.random.default_rng(0)

procs = []
print(f"Launching {N} robot processes...")
for i in range(N):
    x = f"{rng.uniform(-1.0, 1.0):.3f}"
    y = f"{rng.uniform(-1.0, 1.0):.3f}"
    th = f"{rng.uniform(-3.14, 3.14):.3f}"
    p = subprocess.Popen(
        [sys.executable, "robot_node.py", str(i), str(N), x, y, th]
    )
    procs.append(p)

print(f"{N} robots running and listening.")
print("Now run  python op_sender.py  in another terminal.")
print("Waiting for all robots to finish...")

for p in procs:
    p.wait()

print("All robots finished. Check log_robot_0.csv ... log_robot_4.csv")