# make_swarm_models.py
# Builds one SDF per robot from the official TurtleBot3 Burger model so that N
# robots can live in one Gazebo world without sharing topics.
#
# Changes vs the stock model (each is stated in the paper's Methods):
#   - every robot gets its own topics: /burger_i/cmd_vel, /burger_i/odom, ...
#     (the stock model uses the shared topic "cmd_vel", so N copies would all
#      obey the same command - unusable for a swarm)
#   - DiffDrive max_linear_acceleration set to A_MAX from robot.py (0.3 m/s^2)
#     so Gazebo enforces the same limit as the kinematic model
#   - lidar and IMU removed (not used in this study; saves CPU)
#   - a ground-truth OdometryPublisher added (/burger_i/gt_odom): true pose and
#     velocity from the physics engine, independent of wheel odometry
#
# Usage (from repo root):  python3 gazebo/make_swarm_models.py 8
# Writes: /tmp/swarm_models/burger_<i>.sdf and /tmp/swarm_models/bridge.yaml

import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robot import A_MAX

OUT = "/tmp/swarm_models"


def find_burger_sdf():
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory("turtlebot3_gazebo")
    return os.path.join(share, "models", "turtlebot3_burger", "model.sdf")


def make_sdf(src, i):
    ns = f"/burger_{i}"
    s = src
    s = re.sub(r"<sensor\b.*?</sensor>", "", s, flags=re.S)           # drop lidar/IMU
    s = s.replace("<topic>cmd_vel</topic>", f"<topic>{ns}/cmd_vel</topic>")
    s = s.replace("<odom_topic>odom</odom_topic>", f"<odom_topic>{ns}/odom</odom_topic>")
    s = s.replace("<tf_topic>/tf</tf_topic>", f"<tf_topic>{ns}/tf</tf_topic>")
    s = s.replace("<topic>joint_states</topic>", f"<topic>{ns}/joint_states</topic>")
    s, n_acc = re.subn(r"<max_linear_acceleration>[^<]*</max_linear_acceleration>",
                       f"<max_linear_acceleration>{A_MAX}</max_linear_acceleration><min_linear_acceleration>-{A_MAX}</min_linear_acceleration>", s)
    gt = (f'\n    <plugin filename="gz-sim-odometry-publisher-system" '
          f'name="gz::sim::systems::OdometryPublisher">\n'
          f'      <odom_frame>world</odom_frame>\n'
          f'      <robot_base_frame>base_footprint</robot_base_frame>\n'
          f'      <odom_topic>{ns}/gt_odom</odom_topic>\n'
          f'      <odom_publish_frequency>50</odom_publish_frequency>\n'
          f'      <dimensions>2</dimensions>\n'
          f'    </plugin>\n  </model>')
    s = s.replace("</model>", gt, 1) if s.count("</model>") == 1 else s
    # sanity checks: fail loudly rather than silently produce a shared-topic swarm
    assert f"{ns}/cmd_vel" in s, "cmd_vel topic not rewritten - model.sdf changed?"
    assert f"{ns}/gt_odom" in s, "ground-truth plugin not inserted"
    assert n_acc == 1, "max_linear_acceleration not found exactly once"
    assert "<sensor" not in s
    return s


def bridge_yaml(N):
    rows = ['- ros_topic_name: "clock"\n  gz_topic_name: "clock"\n'
            '  ros_type_name: "rosgraph_msgs/msg/Clock"\n  gz_type_name: "gz.msgs.Clock"\n'
            '  direction: GZ_TO_ROS\n']
    for i in range(N):
        ns = f"/burger_{i}"
        rows.append(f'- ros_topic_name: "{ns}/cmd_vel"\n  gz_topic_name: "{ns}/cmd_vel"\n'
                    '  ros_type_name: "geometry_msgs/msg/Twist"\n  gz_type_name: "gz.msgs.Twist"\n'
                    '  direction: ROS_TO_GZ\n')
        rows.append(f'- ros_topic_name: "{ns}/gt_odom"\n  gz_topic_name: "{ns}/gt_odom"\n'
                    '  ros_type_name: "nav_msgs/msg/Odometry"\n  gz_type_name: "gz.msgs.Odometry"\n'
                    '  direction: GZ_TO_ROS\n')
    return "".join(rows)


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    src_path = sys.argv[2] if len(sys.argv) > 2 else find_burger_sdf()
    src = open(src_path).read()
    os.makedirs(OUT, exist_ok=True)
    for i in range(N):
        with open(f"{OUT}/burger_{i}.sdf", "w") as f:
            f.write(make_sdf(src, i))
    with open(f"{OUT}/bridge.yaml", "w") as f:
        f.write(bridge_yaml(N))
    print(f"wrote {N} robot models + bridge.yaml to {OUT}  (A_MAX={A_MAX})")
