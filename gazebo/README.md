# Gazebo validation (TurtleBot3 Burger, ROS 2 Jazzy, Gazebo Harmonic)

Purpose: replay the STOP-under-command-loss scenario on physics-simulated
TurtleBot3 Burgers, with the SAME fault realisation as `run_episode.py`
(same N, loss, burst, seed -> same robots miss the STOP), and compare the
measured stopping behaviour with the kinematic model.

Run from the repo root on the Ubuntu/WSL machine:

1. `bash gazebo/launch_swarm.sh 8`            (terminal 1, leave open)
2. `python3 gazebo/gz_stop_scenario.py --N 8 --loss 0.2 --seed 0`   (terminal 2)
3. `python3 gazebo/plot_gazebo_run.py data/gazebo_runs/run_N8_loss0.2_seed0.csv`

What to report honestly in the paper: Gazebo is a second simulator, not
hardware. The physics server runs headless and uses sim time, so results do not
depend on GUI rendering speed. Models are modified from the stock Burger (see
`make_swarm_models.py` header).
