# Trace-driven dependability study (measured Wi-Fi loss traces replayed through sim_v2 model)

Script: run_trace_study.py -> data/trace_study.csv. Each robot replays one measured receiver trace (R2 or R4, one session) from a random
offset; 30 Hz rebroadcast with latching; shared STOP misread added in closed form (p = 1.27%, misread_vs_window.json). 500 episodes per cell
(95% CI up to +-4%). Robots are independent draws from one receiver's trace (measured cross-receiver overlap is small).

N=8 robots, total P(some robot still moving at the 1.0 s deadline after a true STOP):
| Channel (receiver, session) | RAIST latching only | with fail-safe timeout 0.234 s | fail-safe trips / min / robot |
|---|---|---|---|
| R2 quiet | 2.3% | 1.3% | 0.7 |
| R2 busy | 1.5% | 1.3% | 1.0 |
| R2 far (9 s outage inside) | 11.5% | 1.3% | 1.0 |
| R4 quiet | 3.6% | 1.3% | 0.7 |
| R4 busy | 4.0% | 1.3% | 2.8 |
| R4 far (8 m, other room) | 53.4% | 1.3% | 27.4 |

Reading: (1) with the fail-safe, loss-driven violations were 0 of 500 in every cell; the remaining 1.3% is the shared misread, which no timeout can catch.
(2) The price is availability: at 8 m through a wall the fail-safe fires ~27 times/min/robot, i.e. the swarm is effectively unusable there. Safety is bought with
availability, so range/link-quality monitoring (or relay) is needed.
(3) Without the fail-safe, risk grows with swarm size (any robot missing the window counts) and is dominated by the range-limited channel.
Caveats: one day, one sender-hosted hotspot, two Mac receivers, 10 min each; sim and per-window closed form agree within sampling error (sim slightly lower);
p_misread rests on 2 events (STOP dataset pending).
