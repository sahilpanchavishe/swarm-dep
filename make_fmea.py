# make_fmea.py - FMEA for the gesture-commanded swarm (corrected model, sim_v2).
# S, O, D on 1-10 scales; RPN = S*O*D. S and D are engineering judgements (rationale given).
# O is anchored to measured/simulated rates at a stated REFERENCE condition. The reference
# Wi-Fi condition is a placeholder until the burst statistics are measured on the real router.
import csv, json
REF = {"burst_s": "0.3", "loss": "0.1", "N": "8"}     # <- replace with measured Wi-Fi values
mw = json.load(open("data/misread_vs_window.json"))
pm = mw["stop"][0]; pr = [e for e in mw["priority"] if e["W"] == 1][0]
R = {(r["common"], r["burst_s"], r["loss"], r["N"]): r for r in csv.DictReader(open("data/study_v2.csv"))}
ref = R[("0.0", REF["burst_s"], REF["loss"], REF["N"])]
ref32 = R[("0.0", REF["burst_s"], REF["loss"], "32")]
pl = float(ref["p_loss_violation"])

def occ(p):   # occurrence scale used throughout (per STOP event)
    for thr, o in [(0.5, 9), (0.2, 8), (0.1, 7), (0.05, 6), (0.02, 5), (0.01, 4), (0.002, 3), (0.0005, 2)]:
        if p >= thr: return o
    return 1

rows = [
 ("Loss burst covers the STOP window (latching keeps robot driving)",
  "Robot misses every STOP rebroadcast within its slack and keeps moving", 9, occ(pl), 4,
  f"P={100*pl:.1f}% of N=8 episodes at ref ({REF['burst_s']} s bursts, {float(REF['loss'])*100:.0f}% loss); detectable by heartbeat loss"),
 ("STOP misread by recogniser (shared by whole swarm)",
  "All robots receive a motion command instead of STOP", 9, occ(pm["p"]), 9,
  f"{pm['k']}/{pm['n']} STOP holds misread ({100*pm['p']:.2f}%, CI {100*pm['ci'][0]:.1f}-{100*pm['ci'][1]:.1f}%); packets arrive normally so no network monitor or timeout can detect it"),
 ("Swarm-size amplification of loss bursts",
  "More robots, more chances one is inside a long burst", 8, occ(float(ref32["p_loss_violation"])), 5,
  f"loss-driven violation {100*pl:.1f}% (N=8) -> {100*float(ref32['p_loss_violation']):.1f}% (N=32) at ref, independent channels; smaller if bursts are shared"),
 ("Spurious STOP (other gesture read as STOP)",
  "Swarm halts when the operator meant a formation command - availability loss, safe side", 3, occ(pr["false_stop"]), 2,
  f"false STOP {100*pr['false_stop']:.1f}% of non-STOP holds; mostly CLUSTER (OK-sign) read as open palm"),
 ("Fail-safe nuisance stop (heartbeat timeout fires in a harmless burst)",
  "Robot stops needlessly; swarm availability drops", 3, 8, 2,
  "under bursty loss, timeouts short enough to be safe also fire in ordinary bursts (design_rule_v2.csv)"),
 ("STOP received too late for braking",
  "Correct STOP but robot cannot stop within T_stop", 7, 2, 4,
  "braking 0.73 s at A_MAX=0.3 m/s^2 (Gazebo 0.75 s); only if T_stop is set below recognition delay + braking"),
]
table = [{"failure_mode": m, "effect": e, "S": s, "O": o, "D": d, "RPN": s*o*d, "rationale": r}
         for m, e, s, o, d, r in rows]
table.sort(key=lambda r: r["RPN"], reverse=True)
with open("data/fmea_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
print(f"reference condition: {REF}")
for r in table: print(f"{r['RPN']:>4}  S{r['S']} O{r['O']} D{r['D']}  {r['failure_mode']}")
