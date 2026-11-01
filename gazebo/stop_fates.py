# stop_fates.py
# Decides, per robot, whether the true STOP is received or missed.
# This is a line-for-line copy of the sampling order in run_episode.py, so for
# the same (N, loss_rate, burst_len, seed) the Gazebo run and the kinematic run
# see EXACTLY the same set of robots missing the STOP. That lets us compare
# the two simulators on identical fault realisations.

import numpy as np
from channel_model import corrupt_gesture, packet_lost


def decide_fates(N, loss_rate, burst_len, seed, latch=True, misclassify=True):
    """Return list of 'STOP' (robot halts), 'DRIVE' (missed STOP, keeps driving
    under latching) or 'WAIT' (packet lost, non-latching fail-safe)."""
    rng = np.random.default_rng(seed)
    burst_remaining = [0] * N
    fates = []
    for i in range(N):
        if burst_remaining[i] > 0:
            lost = True
            burst_remaining[i] -= 1
        else:
            lost = packet_lost(loss_rate, rng)
            if lost and burst_len > 1:
                burst_remaining[i] = int(rng.integers(0, burst_len))
        if lost:
            fates.append("DRIVE" if latch else "WAIT")
        else:
            received = corrupt_gesture("STOP", rng) if misclassify else "STOP"
            fates.append("STOP" if received == "STOP" else "DRIVE")
    return fates
