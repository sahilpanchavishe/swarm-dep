# Trace-driven dependability study (measured Wi-Fi loss traces replayed through the sim_v2 model)

Script: `run_trace_study.py` -> `data/trace_study.csv`. Each robot replays one measured receiver trace (R2 or R4, one session) from a random
offset; 30 Hz rebroadcast with latching; shared STOP misread added exactly (p = 0.62%, dedicated held-out STOP dataset, 3/481, 95% CI 0.21-1.82%;
`data/stop_misread_primary.json`). 500 episodes per cell (95% CI up to +-4%). Robots are independent draws from one receiver's trace
(measured cross-receiver overlap is small). Totals are repriced from the channel-only column with `reprice_totals.py` when p changes.

N=8 robots, total P(some robot still moving at the 1.0 s deadline after a true STOP):
| Channel (receiver, session) | RAIST latching only | with fail-safe timeout 0.234 s | fail-safe trips / min / robot |
|---|---|---|---|
| R2 quiet | 1.6% | 0.62% | 0.7 |
| R2 busy | 0.8% | 0.62% | 1.0 |
| R2 far (9 s outage inside) | 11.0% | 0.62% | 1.0 |
| R4 quiet | 3.0% | 0.62% | 0.7 |
| R4 busy | 3.4% | 0.62% | 2.8 |
| R4 far (8 m, other room) | 53.1% | 0.62% | 27.4 |

Reading: (1) with the fail-safe, loss-driven violations were 0 of 500 in every cell; what remains (0.62%; 1.27% with the original-dataset rate; 1.82% at the
upper CI bound) is the shared misread, which no timeout can catch because no packet is missing. (2) The price is availability: at 8 m through a wall the
fail-safe fires ~27 times/min/robot, so the swarm is effectively unusable there; safety is bought with availability, so range / link-quality
monitoring (or relay) is needed. (3) Without the fail-safe, risk grows with swarm size and is dominated by the range-limited channel.
Caveats: one day, one sender-hosted hotspot (sender radio also a client of an iPhone hotspot), two Mac receivers, 10 min each; R2's single 9 s outage is
unexplained (sender clock jump just before it); sim and per-window closed form agree within sampling error.
