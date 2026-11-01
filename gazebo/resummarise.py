# resummarise.py - rebuild a Gazebo run's .json summary from its logged .csv
# (no need to re-run Gazebo). Usage: python gazebo/resummarise.py data/gazebo_runs/run_N8_loss0.2_seed0.csv
import csv, json, os, sys, types
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "gazebo")); os.chdir(ROOT)
for m in ["rclpy", "rclpy.node", "rclpy.parameter", "geometry_msgs", "geometry_msgs.msg", "nav_msgs", "nav_msgs.msg"]:
    sys.modules.setdefault(m, types.ModuleType(m))
sys.modules["rclpy.node"].Node = object; sys.modules["rclpy.parameter"].Parameter = object
sys.modules["geometry_msgs.msg"].Twist = object; sys.modules["nav_msgs.msg"].Odometry = object
import gz_stop_scenario as g
path = sys.argv[1]; old = json.load(open(path.replace(".csv", ".json")))
rows = [(float(r["t"]), int(r["robot"]), r["fate"], float(r["x"]), float(r["y"]), float(r["v"])) for r in csv.DictReader(open(path))]
a = types.SimpleNamespace(N=old["N"], loss=old["loss_rate"], burst=old["burst_len"], seed=old["seed"], t_stop=3.0, after=3.0)
s = g.summarise(rows, a, old["fates"])
json.dump(s, open(path.replace(".csv", ".json"), "w"), indent=2)
print(json.dumps({k: s[k] for k in ("violated", "robots_still_moving", "gazebo_stop_time_s_mean", "gazebo_stop_dist_m_mean")}, indent=2))
