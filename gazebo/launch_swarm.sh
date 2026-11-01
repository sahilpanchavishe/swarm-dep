#!/usr/bin/env bash
# launch_swarm.sh - start Gazebo (headless physics) + N namespaced TurtleBot3 Burgers
# + the ROS<->Gazebo bridge. Optional GUI for screenshots.
#
# Usage (from repo root):   bash gazebo/launch_swarm.sh 8          # with GUI
#                           bash gazebo/launch_swarm.sh 8 nogui    # data runs only
# Leave this terminal open. Ctrl+C stops everything.
set -e
N=${1:-8}
MODE=${2:-gui}
SPACING=0.5                      # lateral spacing between robots [m]

source /opt/ros/jazzy/setup.bash
cd "$(dirname "$0")/.."
SHARE=$(ros2 pkg prefix turtlebot3_gazebo)/share/turtlebot3_gazebo
WORLD_FILE=$SHARE/worlds/empty_world.world
WORLD=$(grep -oP '<world name="\K[^"]+' "$WORLD_FILE")
export GZ_SIM_RESOURCE_PATH=$SHARE/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}

pkill -f "gz sim" 2>/dev/null || true
pkill -f parameter_bridge 2>/dev/null || true
sleep 1

python3 gazebo/make_swarm_models.py "$N"

trap 'echo stopping...; kill $(jobs -p) 2>/dev/null; pkill -f "gz sim"; exit 0' INT TERM

# Physics server runs headless: its timing does not depend on the GPU/rendering.
gz sim -r -s -v2 "$WORLD_FILE" > /tmp/gz_server.log 2>&1 &
sleep 5

for ((i=0; i<N; i++)); do
  y=$(python3 -c "print(round(($i-($N-1)/2)*$SPACING,3))")
  ros2 run ros_gz_sim create -world "$WORLD" -file /tmp/swarm_models/burger_$i.sdf \
       -name burger_$i -x 0 -y "$y" -z 0.01 -Y 0 > /dev/null 2>&1
  echo "spawned burger_$i at y=$y"
done

ros2 run ros_gz_bridge parameter_bridge --ros-args \
     -p config_file:=/tmp/swarm_models/bridge.yaml > /tmp/gz_bridge.log 2>&1 &

if [ "$MODE" != "nogui" ]; then
  gz sim -g -v2 > /tmp/gz_gui.log 2>&1 &
fi

echo "READY: $N robots in world '$WORLD'. Now run gazebo/gz_stop_scenario.py in another terminal."
wait
