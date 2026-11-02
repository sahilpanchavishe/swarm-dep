# analyze_stop_dataset.py - STOP misread from the dedicated STOP recordings (does NOT overwrite any existing json).
# Usage:  python3 analyze_stop_dataset.py                       -> new data only (data/gesture_recordings_stop)
#         python3 analyze_stop_dataset.py --old                 -> also pool with the original data (gesture_recordings_cb)
# A "hold" = consecutive frames of one gesture separated by < 0.2 s (one press of 'r' in record_stop.py).
# The recogniser emits the majority vote of the first W frames (W=1 is the reference used so far: 2/157 = 1.27%).
import csv, glob, math, sys
from collections import Counter, defaultdict
from classifier import classify
GAP = 0.2; WINDOWS = [1, 3, 5, 10]
def wilson(k, n):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + 1.96**2 / n; c = (p + 1.96**2 / (2*n)) / d
    h = 1.96 * math.sqrt(p*(1-p)/n + 1.96**2/(4*n*n)) / d
    return max(0.0, c - h), min(1.0, c + h)
def read_holds(pattern, tag):
    out = []
    for path in sorted(glob.glob(pattern)):
        cur, last_t, last_g, meta = [], None, None, None
        for r in csv.DictReader(open(path)):
            g = r["intended_gesture"]; t = float(r["timestamp"])
            if last_t is not None and (t - last_t > GAP or g != last_g) and cur:
                out.append((last_g, meta, cur, tag)); cur = []
            x = [float(r[f"{a}{i}"]) for i in range(21) for a in "xyz"]
            cur.append(classify(x, r.get("handedness", "Right")))
            last_t, last_g, meta = t, g, (r["participant"], r["condition"])
        if cur: out.append((last_g, meta, cur, tag))
    return out
holds = read_holds("data/gesture_recordings_stop/*.csv", "new")
if "--old" in sys.argv: holds += read_holds("data/gesture_recordings_cb/*.csv", "old")
if not holds: sys.exit("no recordings found: run from the repo root and check data/gesture_recordings_stop/")
def emitted(h, W): return Counter(h[:W]).most_common(1)[0][0]
print("holds per gesture:", dict(Counter(g for g, *_ in holds)))
print("participants:", sorted({m[0] for _, m, _, _ in holds}))
print(f"\n{'W':>3}  {'STOP misread k/n':>18} {'rate':>7} {'95% Wilson CI':>16}   false-STOP on LINE / CLUSTER holds")
for W in WINDOWS:
    s = [h for g, m, h, t in holds if g == "STOP" and len(h) >= W]
    k = sum(emitted(h, W) != "STOP" for h in s); lo, hi = wilson(k, len(s))
    fs = []
    for other in ("LINE", "CLUSTER"):
        o = [h for g, m, h, t in holds if g == other and len(h) >= W]
        fs.append(f"{other} {sum(emitted(h, W) == 'STOP' for h in o)}/{len(o)}")
    print(f"{W:>3}  {k:>8}/{len(s):<9} {100*k/len(s):6.2f}% {100*lo:6.2f}-{100*hi:<6.2f}%   " + "  ".join(fs))
W = 1
print("\nSTOP holds misread at W=1 (what they were read as):")
for g, m, h, t in holds:
    if g == "STOP" and len(h) >= W and emitted(h, W) != "STOP":
        print(f"  {t} {m[0]} {m[1]}: read as {emitted(h, W)}  (frames: {dict(Counter(h))})")
print("\nPer participant / condition at W=1 (k misread / n STOP holds):")
by = defaultdict(lambda: [0, 0])
for g, m, h, t in holds:
    if g == "STOP" and len(h) >= W:
        for key in (("participant", m[0]), ("condition", m[1])):
            by[key][1] += 1; by[key][0] += emitted(h, W) != "STOP"
for key in sorted(by): print(f"  {key[0]:12} {key[1]:12} {by[key][0]}/{by[key][1]}")
n = sum(v[1] for k_, v in by.items() if k_[0] == "participant")
print(f"\nIf 0 misreads in {n} STOP holds the 95% upper bound would be about {100*wilson(0, n)[1]:.2f}%.")
