# gz_stop_scenario.py
# Runs the STOP-under-command-loss scenario on N TurtleBot3 Burgers in Gazebo,
# using the SAME fault sampling as run_episode.py (stop_fates.py), and logs the
# ground-truth trajectories. Physics time (/clock) is used throughout, so the
# result does not depend on how fast the GUI renders.
#
# Usage (from repo root, after launch_swarm.sh is READY):
#   python3 gazebo/gz_stop_scenario.py --N 8 --loss 0.2 --seed 0
# Output: data/gazebo_runs/run_N8_loss0.2_seed0.csv  (+ summary .json)

import argparse, csv, json, math, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "gazebo"))
os.chdir(ROOT)  # channel_model reads data/ with relative paths

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

from robot import V_MAX, A_MAX
from safety import T_STOP, V_STOPPED
from stop_fates import decide_fates


class StopScenario(Node):
    def __init__(self, a):
        super().__init__("gz_stop_scenario",
                         parameter_overrides=[Parameter("use_sim_time", value=True)])
        self.a = a
        self.fates = decide_fates(a.N, a.loss, a.burst, a.seed)
        self.pubs = [self.create_publisher(Twist, f"/burger_{i}/cmd_vel", 10) for i in range(a.N)]
        self.state = [None] * a.N
        for i in range(a.N):
            self.create_subscription(Odometry, f"/burger_{i}/gt_odom",
                                     lambda m, i=i: self._odom(i, m), 10)
        self.t0 = None
        self.rows = []
        self.done = False
        self.create_timer(0.05, self._tick)   # 20 Hz command/heartbeat, sim time

    def _odom(self, i, m):
        v = math.hypot(m.twist.twist.linear.x, m.twist.twist.linear.y)
        self.state[i] = (m.pose.pose.position.x, m.pose.pose.position.y, v)

    def _now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _tick(self):
        if self.done:
            return
        if self.t0 is None:
            if all(s is not None for s in self.state) and self._now() > 0:
                self.t0 = self._now()
                self.get_logger().info(f"all {self.a.N} robots reporting; starting. fates={self.fates}")
            return
        t = self._now() - self.t0
        for i, p in enumerate(self.pubs):
            cmd = Twist()
            if t < self.a.t_stop or self.fates[i] == "DRIVE":
                cmd.linear.x = V_MAX          # driving, or missed STOP (latched)
            p.publish(cmd)                    # STOP/WAIT -> zero twist
            x, y, v = self.state[i]
            self.rows.append((round(t, 3), i, self.fates[i], x, y, v))
        if t >= self.a.t_stop + self.a.after:
            for p in self.pubs:
                p.publish(Twist())            # park everyone at the end
            self.done = True


def summarise(rows, a, fates):
    deadline = a.t_stop + T_STOP
    per = {}
    for t, i, fate, x, y, v in rows:
        r = per.setdefault(i, {"fate": fate, "v_after_deadline": 0.0, "t_rest": None,
                               "x_at_stop": None, "x_rest": None})
        if t >= a.t_stop and r["x_at_stop"] is None:
            r["x_at_stop"] = x
        if t >= deadline:
            r["v_after_deadline"] = max(r["v_after_deadline"], v)
        if t >= a.t_stop and r["t_rest"] is None and v < V_STOPPED and fate != "DRIVE":
            r["t_rest"] = t - a.t_stop
            r["x_rest"] = x
    # Moving after the deadline = displaced > 1 cm over the post-deadline window.
    # (Instantaneous speed alone is unreliable: Gazebo wheel-contact jitter reaches
    #  ~0.012 m/s on a parked robot, which is above V_STOPPED but moves it < 1 mm.)
    xs = {}
    for t, i, fate, x, y, v in rows:
        if t >= deadline:
            xs.setdefault(i, []).append((x, y))
    for i, pts in xs.items():
        per[i]["disp_after_deadline_m"] = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
    receivers = [r for r in per.values() if r["fate"] != "DRIVE" and r["t_rest"] is not None]
    still = [i for i, r in per.items() if r.get("disp_after_deadline_m", 0.0) > 0.01]
    out = {
        "N": a.N, "loss_rate": a.loss, "burst_len": a.burst, "seed": a.seed,
        "fates": fates, "n_missed_stop": fates.count("DRIVE"),
        "violated": len(still) > 0, "robots_still_moving": still,
        "kinematic_stop_time_s": V_MAX / A_MAX,
        "kinematic_stop_dist_m": V_MAX ** 2 / (2 * A_MAX),
        "gazebo_stop_time_s_mean": (sum(r["t_rest"] for r in receivers) / len(receivers)) if receivers else None,
        "gazebo_stop_dist_m_mean": (sum(r["x_rest"] - r["x_at_stop"] for r in receivers) / len(receivers)) if receivers else None,
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=8)
    ap.add_argument("--loss", type=float, default=0.2)
    ap.add_argument("--burst", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--t_stop", type=float, default=3.0, help="drive time before STOP [s]")
    ap.add_argument("--after", type=float, default=3.0, help="observe this long after STOP [s]")
    a = ap.parse_args()

    rclpy.init()
    node = StopScenario(a)
    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.1)

    os.makedirs("data/gazebo_runs", exist_ok=True)
    tag = f"run_N{a.N}_loss{a.loss}_seed{a.seed}"
    with open(f"data/gazebo_runs/{tag}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t", "robot", "fate", "x", "y", "v"]); w.writerows(node.rows)
    s = summarise(node.rows, a, node.fates)
    with open(f"data/gazebo_runs/{tag}.json", "w") as f:
        json.dump(s, f, indent=2)

    # same fault realisation in the kinematic simulator, for direct comparison
    from run_episode import run_episode
    k = run_episode(N=a.N, loss_rate=a.loss, burst_len=a.burst, seed=a.seed)
    print(json.dumps(s, indent=2))
    print(f"kinematic sim, same seed: violated={k['violated']} n_missed_stop={k['n_missed_stop']}")
    print(f"saved data/gazebo_runs/{tag}.csv/.json")
    node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
