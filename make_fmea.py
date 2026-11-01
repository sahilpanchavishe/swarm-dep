# make_fmea.py
# Failure Mode and Effects Analysis for the gesture-commanded swarm.
# Severity (S), Occurrence (O), Detection (D) each 1-10; RPN = S*O*D.
# Occurrence values are anchored to this study's MEASURED results.
# S and D are engineering judgments with stated rationale - adjust as you see fit.

import csv

# Each row: (failure_mode, effect, S, O, D, rationale)
rows = [
    ("STOP packet dropped (latching keeps robot driving)",
     "Robot ignores emergency STOP, keeps moving - collision/runaway risk",
     9,   # S: near-worst; a runaway robot in an HSI setting is dangerous
     7,   # O: measured 98% episode-violation at 40% loss (N=8), 60% at 10% loss
     6,   # D: hard to detect without a heartbeat monitor (motivates supervisor)
     "O from loss-sweep (N=8, 200 seeds): violation 60% at 10% loss, 98% at 40% loss (study_results.csv)"),

    ("STOP gesture misclassified by recogniser",
     "Robot receives a non-STOP command and keeps driving",
     9,   # S: same dangerous outcome as a dropped STOP
     3,   # O: per-robot STOP misread 1.32%; 12.5% episode-violation at 0% loss, N=8
     7,   # D: very hard to detect - network is fine, robot 'correctly' obeys a wrong command
     "O from measured confusion matrix: P(STOP misread)=1.32% per robot -> 12.5% of N=8 episodes at 0% loss"),

    ("Fail-safe nuisance stop (supervisor over-triggers)",
     "Robot stops needlessly during brief dropout - swarm freezes, task delayed",
     3,   # S: low - safe failure, just inefficient
     6,   # O: 100% at 0.1 s timeout, 15.8% at 0.3 s, 3.7% at recommended 0.4 s
     2,   # D: easy to detect - robot stops with no STOP issued
     "O from design-rule sweep (20% loss): nuisance 99.8% at 0.1 s, 15.8% at 0.3 s, 3.7% at 0.4 s (design_rule.csv)"),

    ("STOP delay exceeds robot braking time",
     "Even a correctly-received STOP cannot halt the robot within T_stop",
     7,   # S: high - robot overshoots stop point, but was commanded correctly
     3,   # O: only when T_stop set below stopping time (~0.73s from V_MAX)
     4,   # D: moderate - predictable from kinematics, measurable in testing
     "Stopping time 0.73 s at A_MAX=0.3 m/s^2 (Gazebo: 0.75 s); violations appear when T_stop is set below this"),

    ("Scaling amplification (one robot fails = swarm fails)",
     "Larger swarm has higher chance >=1 robot misses STOP",
     8,   # S: high - one runaway robot compromises the whole swarm's safety
     5,   # O: measured - baseline violation 12.5% (N=8) -> 34.5% (N=32), p<0.001
     5,   # D: moderate - visible in aggregate but no per-robot guarantee
     "O from N-sweep: 0%-loss violation 12.5% (N=8), 22.0% (N=16), 34.5% (N=32); matches 1-(1-p)^N (study_results.csv)"),
]

# Compute RPN and sort by it (most urgent first).
table = []
for mode, effect, s, o, d, rationale in rows:
    rpn = s * o * d
    table.append({"failure_mode": mode, "effect": effect,
                  "S": s, "O": o, "D": d, "RPN": rpn, "rationale": rationale})
table.sort(key=lambda r: r["RPN"], reverse=True)

# Save and print.
with open("data/fmea_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["failure_mode", "effect", "S", "O", "D", "RPN", "rationale"])
    w.writeheader()
    w.writerows(table)

print(f"{'Failure mode':<48} S  O  D  RPN")
print("-" * 70)
for r in table:
    print(f"{r['failure_mode'][:46]:<48}{r['S']:>2} {r['O']:>2} {r['D']:>2} {r['RPN']:>4}")
print("\nSaved data/fmea_table.csv")