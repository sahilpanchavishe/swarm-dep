# safety.py
# The explicit safety requirement for the study.
# Requirement: when the operator issues a true STOP, every robot must come
# to rest within T_STOP seconds. A run that violates this is a FAILURE.

T_STOP = 1.0          # [s] max allowed time from true STOP to all robots stopped
V_STOPPED = 0.01      # [m/s] below this speed a robot counts as "stopped"

def check_stop_obeyed(stop_issued_time, robot_stop_times):
    """
    stop_issued_time : sim time when the operator issued the true STOP
    robot_stop_times : list of sim times when each robot actually stopped
                       (None if a robot never stopped)
    Returns (violated: bool, worst_delay: float).
    """
    worst_delay = 0.0
    violated = False
    for t_stop in robot_stop_times:
        if t_stop is None:
            return True, float("inf")      # a robot never stopped = clear violation
        delay = t_stop - stop_issued_time
        worst_delay = max(worst_delay, delay)
        if delay > T_STOP:
            violated = True
    return violated, worst_delay