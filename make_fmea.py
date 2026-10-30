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
     7,   # O: measured ~90% episode-violation at 40% loss, lower at low loss
     6,   # D: hard to detect without a heartbeat monitor (motivates supervisor)
     "O from loss-sweep: violation rate rises to ~0.9 at 40% loss (study_results.csv)"),

    ("STOP gesture misclassified by recogniser",
     "Robot receives a non-STOP command and keeps driving",
     9,   # S: same dangerous outcome as a dropped STOP
     4,   # O: measured ~30% episode-violation at 0% loss (misclassification floor)
     7,   # D: very hard to detect - network is fine, robot 'correctly' obeys a wrong command
     "O from misclassification-only run: ~6/20 episodes at 0% loss (placeholder matrix)"),

    ("Fail-safe nuisance stop (supervisor over-triggers)",
     "Robot stops needlessly during brief dropout - swarm freezes, task delayed",
     3,   # S: low - safe failure, just inefficient
     6,   # O: high at short timeout (measured up to 100% at 0.1s timeout)
     2,   # D: easy to detect - robot stops with no STOP issued
     "O from design-rule sweep: nuisance rate up to 100% at 0.1s timeout (design_rule.csv)"),

    ("STOP delay exceeds robot braking time",
     "Even a correctly-received STOP cannot halt the robot within T_stop",
     7,   # S: high - robot overshoots stop point, but was commanded correctly
     3,   # O: only when T_stop set below stopping time (~0.73s from V_MAX)
     4,   # D: moderate - predictable from kinematics, measurable in testing
     "Stopping time ~0.73s at A_MAX=0.3 m/s^2; violations appear when T_stop<that"),

    ("Scaling amplification (one robot fails = swarm fails)",
     "Larger swarm has higher chance >=1 robot misses STOP",
     8,   # S: high - one runaway robot compromises the whole swarm's safety
     6,   # O: measured - baseline violation rises 30%->74% from N=8 to N=32
     5,   # D: moderate - visible in aggregate but no per-robot guarantee
     "O from N-sweep: 0%-loss violation 0.30 (N=8) -> 0.74 (N=32) (study_results.csv)"),
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