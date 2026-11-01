# misread_vs_window.py - confirmation-window trade-off from the measured data.
# The operator holds a gesture for ~1 s (one 'hold' = frames separated by <0.2 s).
# A recogniser that waits for W frames and takes the majority vote emits ONE command
# per hold, shared by every robot (one camera, one classifier, one broadcast).
# For each W we measure P(STOP hold is emitted as something else) and the added delay W/fps.
import csv, glob, json, math
from collections import Counter, defaultdict
from classifier import classify

GAP, FPS = 0.2, 30.0
WINDOWS = [1, 3, 5, 7, 10, 15, 20, 25]

def wilson(k, n):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + 1.96**2 / n; c = (p + 1.96**2 / (2*n)) / d
    h = 1.96 * math.sqrt(p*(1-p)/n + 1.96**2/(4*n*n)) / d
    return max(0.0, c - h), min(1.0, c + h)

holds = defaultdict(list)          # gesture -> list of prediction sequences
for path in sorted(glob.glob("data/gesture_recordings_cb/*.csv")):
    cur, last_t, last_g = [], None, None
    for r in csv.DictReader(open(path)):
        g = r["intended_gesture"]; t = float(r["timestamp"])
        if last_t is not None and (t - last_t > GAP or g != last_g):
            if cur: holds[last_g].append(cur)
            cur = []
        x = [float(r[f"{a}{i}"]) for i in range(21) for a in "xyz"]
        cur.append(classify(x, r.get("handedness", "Right")))
        last_t, last_g = t, g
    if cur: holds[last_g].append(cur)

out = {"n_holds": {g: len(v) for g, v in holds.items()}, "stop": []}
print("holds per gesture:", out["n_holds"])
print(f"{'W':>3} {'delay_ms':>8} {'STOP misread':>13} {'95% CI':>15} {'all-gesture err':>16}")
for W in WINDOWS:
    k = n = 0; ka = na = 0
    for g, hs in holds.items():
        for h in hs:
            if len(h) < W: continue
            emitted = Counter(h[:W]).most_common(1)[0][0]
            na += 1; ka += emitted != g
            if g == "STOP": n += 1; k += emitted != "STOP"
    lo, hi = wilson(k, n)
    out["stop"].append({"W": W, "delay_s": W / FPS, "k": k, "n": n, "p": k / n, "ci": [lo, hi], "all_err": ka / na})
    print(f"{W:>3} {1000*W/FPS:>8.0f} {k:>5}/{n:<4} {100*k/n:>5.2f}% {100*lo:>5.2f}-{100*hi:<5.2f}% {100*ka/na:>14.1f}%")
json.dump(out, open("data/misread_vs_window.json", "w"), indent=2)

# STOP-priority rule: emit STOP as soon as ANY of the first W frames reads STOP.
# Safety side: P(STOP hold never shows a STOP frame). Cost side: false STOPs on other gestures.
print("\nSTOP-priority (any STOP frame in first W):")
print(f"{'W':>3} {'missed STOP':>12} {'false STOP (other gestures)':>28}")
out["priority"] = []
for W in WINDOWS:
    k = n = fk = fn = 0
    for g, hs in holds.items():
        for h in hs:
            if len(h) < W: continue
            hit = "STOP" in h[:W]
            if g == "STOP": n += 1; k += not hit
            else: fn += 1; fk += hit
    out["priority"].append({"W": W, "missed": k / n, "k": k, "n": n, "false_stop": fk / fn})
    print(f"{W:>3} {k:>4}/{n:<4} {100*k/n:5.2f}%   {fk:>4}/{fn:<5} {100*fk/fn:5.1f}%")
json.dump(out, open("data/misread_vs_window.json", "w"), indent=2)
