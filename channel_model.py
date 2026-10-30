# channel_model.py
# Loads the measured channel data (latency + confusion matrix) and provides
# fault-injection functions. All numbers come from files in data/, so the
# study uses real measurements, not hardcoded guesses.

import json
import numpy as np

COMMANDS = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]

# --- Load measured latency distribution ---
with open("data/latency_summary.json") as f:
    LAT = json.load(f)

def sample_latency(rng):
    """Return a plausible latency [ms] drawn from the measured distribution.
    We model it as a normal around the measured mean/std, clipped to the
    measured min/max. (A simple, defensible first model.)
    """
    val = rng.normal(LAT["mean_ms"], LAT["std_ms"])
    return float(np.clip(val, LAT["min_ms"], LAT["max_ms"]))

# --- Load confusion matrix ---
def load_confusion():
    """Read data/confusion_matrix.csv into a dict:
    confusion[intended] = list of probabilities over COMMANDS order.
    """
    confusion = {}
    with open("data/confusion_matrix.csv") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or line.startswith("intended") or not line:
                continue
            parts = line.split(",")
            intended = parts[0]
            probs = [float(p) for p in parts[1:]]
            confusion[intended] = probs
    return confusion

CONFUSION = load_confusion()

def corrupt_gesture(intended, rng):
    """Given the gesture the operator INTENDED, return what the recogniser
    actually outputs, sampled from the measured confusion matrix.
    Most of the time it's correct; sometimes it's a misclassification.
    """
    probs = CONFUSION[intended]
    return rng.choice(COMMANDS, p=probs)

def packet_lost(loss_rate, rng):
    """Return True if this packet is dropped, given a loss probability."""
    return rng.random() < loss_rate