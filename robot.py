# robot.py
# Differential-drive (unicycle) kinematic model for one TurtleBot3 Burger.
# All specs are real TurtleBot3 Burger values from the ROBOTIS e-Manual.

import numpy as np

# --- Physical constants (TurtleBot3 Burger, ROBOTIS e-Manual) ---
V_MAX = 0.22        # max linear speed [m/s]
W_MAX = 2.84        # max angular speed [rad/s]
A_MAX = 0.3        # max linear acceleration [m/s^2]
ALPHA_MAX = 3.0    # max angular acceleration [rad/s^2]
WHEEL_RADIUS = 0.033   # [m]
WHEEL_SEP = 0.160      # axle length between wheels [m]
ROBOT_RADIUS = 0.105   # footprint radius [m], for separation checks

class Robot:
    def __init__(self, x, y, theta, robot_id):
        self.x = x
        self.y = y
        self.theta = theta
        self.id = robot_id
        self.v = 0.0      # current actual linear speed [m/s]
        self.w = 0.0      # current actual angular speed [rad/s]

    def step(self, v_cmd, w_cmd, dt):
        """Advance one timestep. The robot cannot change speed instantly;
        actual speed ramps toward the commanded speed, limited by A_MAX /
        ALPHA_MAX. This gives the robot realistic stopping distance.
        """
        # Clamp the COMMAND to physical speed limits.
        v_cmd = np.clip(v_cmd, -V_MAX, V_MAX)
        w_cmd = np.clip(w_cmd, -W_MAX, W_MAX)

        # Ramp actual linear speed toward the command, limited by max accel.
        dv_max = A_MAX * dt
        dv = np.clip(v_cmd - self.v, -dv_max, dv_max)
        self.v += dv

        # Ramp actual angular speed toward the command.
        dw_max = ALPHA_MAX * dt
        dw = np.clip(w_cmd - self.w, -dw_max, dw_max)
        self.w += dw

        # Move using the ACTUAL (ramped) speeds.
        self.x += self.v * np.cos(self.theta) * dt
        self.y += self.v * np.sin(self.theta) * dt
        self.theta += self.w * dt
        self.theta = (self.theta + np.pi) % (2 * np.pi) - np.pi

    def wheel_speeds(self, v, w):
        """Convert (v, w) to left/right wheel angular speeds [rad/s].
        This is what a real differential-drive controller computes.
        Not needed for motion, but lets you report realistic actuation.
        """
        v = np.clip(v, -V_MAX, V_MAX)
        w = np.clip(w, -W_MAX, W_MAX)
        w_left  = (v - w * WHEEL_SEP / 2) / WHEEL_RADIUS
        w_right = (v + w * WHEEL_SEP / 2) / WHEEL_RADIUS
        return w_left, w_right