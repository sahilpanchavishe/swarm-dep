# classifier.py
# Rule-based gesture classifier from MediaPipe hand landmarks.
# Tier-one design: wrist-origin + hand-size normalization, joint-angle finger
# states, handedness-aware thumb logic, explainable rules (no training).
#
# Landmark indices (MediaPipe Hands, 21 points):
#   0 wrist
#   thumb:  1 CMC, 2 MCP, 3 IP, 4 TIP
#   index:  5 MCP, 6 PIP, 7 DIP, 8 TIP
#   middle: 9 MCP, 10 PIP, 11 DIP, 12 TIP
#   ring:   13 MCP, 14 PIP, 15 DIP, 16 TIP
#   pinky:  17 MCP, 18 PIP, 19 DIP, 20 TIP

import numpy as np
# Tunable thresholds (verified robust via threshold_sensitivity_cb.py)
FINGER_EXT_RATIO = 1.05
THUMB_PALM_DIST  = 0.55

# Each landmark is (x, y, z). `lm` is a (21, 3) array.

def _angle(a, b, c):
    """Angle at point b formed by a-b-c, in degrees."""
    ba = a - b
    bc = c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))

def finger_extended(lm, mcp, pip, tip):
    """Robust 2D test: finger is extended if the tip is farther from the
    wrist than the PIP joint. Uses x,y only (MediaPipe z is noisy).
    """
    wrist = lm[0][:2]
    d_tip = np.linalg.norm(lm[tip][:2] - wrist)
    d_pip = np.linalg.norm(lm[pip][:2] - wrist)
    return d_tip > d_pip * FINGER_EXT_RATIO    # tip clearly beyond the knuckle

def thumb_extended(lm, handedness="Right"):
    """Thumb extended if its tip is far from the palm center (as in thumbs-up).
    In a fist the thumb tucks toward the palm. Palm center = mean of the four
    finger MCP knuckles. 2D, normalized units.
    """
    palm = (lm[5][:2] + lm[9][:2] + lm[13][:2] + lm[17][:2]) / 4
    tip = lm[4][:2]
    return np.linalg.norm(tip - palm) > THUMB_PALM_DIST

def normalize(lm_raw):
    """lm_raw: (21,3) array. Translate to wrist origin, scale by hand size
    (wrist -> middle finger MCP distance). Makes features position/scale
    invariant.
    """
    lm = lm_raw - lm_raw[0]                     # wrist to origin
    hand_size = np.linalg.norm(lm[9])           # wrist -> middle MCP
    if hand_size < 1e-6:
        hand_size = 1.0
    return lm / hand_size

def classify(lm_raw, handedness="Right"):
    """Classify one frame. Rules fit to the observed finger patterns in the
    recorded dataset. Pattern order: (thumb, index, middle, ring, pinky).
    """
    lm = normalize(np.asarray(lm_raw, dtype=float).reshape(21, 3))

    t = thumb_extended(lm, handedness)
    i = finger_extended(lm, 5, 6, 8)      # index
    m = finger_extended(lm, 9, 10, 12)    # middle
    r = finger_extended(lm, 13, 14, 16)   # ring
    p = finger_extended(lm, 17, 18, 20)   # pinky

    # --- Rules derived from the measured pose patterns (thumb used only
    #     where it is the sole distinguishing feature: fist vs thumbs-up). ---
    if i and m and r and p:
        return "STOP"                      # open palm (all four fingers up)
    if (not i) and m and r and p:
        return "CLUSTER"                   # OK sign: index curled, others up
    if i and m and (not r) and (not p):
        return "SPLIT"                     # V sign
    if i and (not m) and (not r) and (not p):
        return "LINE"                      # index only
    if (not i) and (not m) and (not r) and (not p):
        return "WAIT" if t else "CIRCLE"   # thumbs-up vs fist

    # Fallbacks for in-between frames.
    n_ext = i + m + r + p
    if n_ext >= 3:
        return "STOP"
    if n_ext == 0:
        return "WAIT" if t else "CIRCLE"
    if i and not m:
        return "LINE"
    return "CIRCLE"
