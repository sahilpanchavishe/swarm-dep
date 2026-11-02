# make_stop_primary.py - STOP misread from the DEDICATED, HELD-OUT STOP dataset (data/gesture_recordings_stop).
# This is the primary value fed to the dependability model. The original dataset (misread_vs_window.json) is the
# supplementary estimate (the rule thresholds were tuned on it, so it is not a clean out-of-sample test).
# Writes data/stop_misread_primary.json
import csv, glob, json, math
from collections import Counter, defaultdict
from classifier import classify
GAP = 0.2; WINDOWS = [1, 3, 5, 7, 10, 15, 20, 25]
def wilson(k, n):
    p = k / n; d = 1 + 1.96**2 / n; c = (p + 1.96**2 / (2*n)) / d
    h = 1.96 * math.sqrt(p*(1-p)/n + 1.96**2/(4*n*n)) / d
    return max(0.0, c - h), min(1.0, c + h)
holds = []                                  # (gesture, participant, condition, [frame predictions])
for path in sorted(glob.glob("data/gesture_recordings_stop/*.csv")):
    cur, last_t, last_g, meta = [], None, None, None
    for r in csv.DictReader(open(path)):
        g = r["intended_gesture"]; t = float(r["timestamp"])
        if last_t is not None and (t - last_t > GAP or g != last_g) and cur:
            holds.append((last_g, *meta, cur)); cur = []
        x = [float(r[f"{a}{i}"]) for i in range(21) for a in "xyz"]
        cur.append(classify(x, r.get("handedness", "Right")))
        last_t, last_g, meta = t, g, (r["participant"], r["condition"])
    if cur: holds.append((last_g, *meta, cur))
emit = lambda h, W: Counter(h[:W]).most_common(1)[0][0]
out = {"source": "data/gesture_recordings_stop (held-out; second person confirmed each pose)",
       "n_holds": dict(Counter(h[0] for h in holds)), "participants": sorted({h[1] for h in holds}),
       "stop": [], "priority": [], "errors": [], "per_condition": {}, "per_participant": {}}
for W in WINDOWS:
    s = [h for h in holds if h[0] == "STOP" and len(h[3]) >= W]
    k = sum(emit(h[3], W) != "STOP" for h in s); lo, hi = wilson(k, len(s))
    out["stop"].append({"W": W, "delay_s": W / 30.0, "k": k, "n": len(s), "p": k / len(s), "ci": [lo, hi]})
    fs = {}
    for o in ("LINE", "CLUSTER"):
        oh = [h for h in holds if h[0] == o and len(h[3]) >= W]
        fs[o] = [sum(emit(h[3], W) == "STOP" for h in oh), len(oh)]
    pri_k = sum("STOP" not in h[3][:W] for h in s)
    out["priority"].append({"W": W, "missed": pri_k / len(s), "k": pri_k, "n": len(s), "false_stop": fs})
for h in holds:
    if h[0] == "STOP" and emit(h[3], 1) != "STOP":
        out["errors"].append({"participant": h[1], "condition": h[2], "read_as": emit(h[3], 1), "frames": dict(Counter(h[3]))})
for key, idx in (("per_condition", 2), ("per_participant", 1)):
    agg = defaultdict(lambda: [0, 0])
    for h in holds:
        if h[0] == "STOP": agg[h[idx]][1] += 1; agg[h[idx]][0] += emit(h[3], 1) != "STOP"
    out[key] = dict(agg)
out["sensitivity_p"] = {"primary": out["stop"][0]["p"], "original_dataset": 2 / 157, "primary_upper95": out["stop"][0]["ci"][1]}
json.dump(out, open("data/stop_misread_primary.json", "w"), indent=2)
e = out["stop"][0]; print(f"primary STOP misread (W=1): {e['k']}/{e['n']} = {100*e['p']:.2f}%  95% CI {100*e['ci'][0]:.2f}-{100*e['ci'][1]:.2f}%")
