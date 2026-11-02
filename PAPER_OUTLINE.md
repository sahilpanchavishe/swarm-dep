# Paper outline (status 2 Nov 2026) - target: Sādhanā

**Working title:** Data-driven dependability of gesture-commanded decentralized swarms: recognition errors, measured packet loss, and a fail-safe design rule
(the title may change; the claim below must not).

## 0. The claim, and the framing discipline
**One-sentence thesis:** For a gesture-commanded swarm, whether STOP is safe is decided by two *shared* failure sources that ordinary accuracy
numbers hide - a single misread of the operator's gesture, and bursty (not random) wireless loss - and measuring both lets us say where the safety budget
actually goes and what a fail-safe costs.

**Contributions (in this order):**
1. A measured, honest breakdown of what makes STOP fail: held-out STOP misread 3/481 = 0.62% (95% CI 0.21-1.82%), and measured Wi-Fi burst statistics.
2. A corrected dependability model (shared misread, 30 Hz rebroadcast with latching, burst loss; closed form + replay of measured traces) showing loss-driven violations
   grow with swarm size and range while the misread is a swarm-wide floor.
3. The safety-vs-availability trade-off of a fail-safe timeout (bound 0.234 s) using the measured traces, and when peer relay helps (path fading yes, receiver deafness no).
4. Evidence that classifier accuracy does not predict STOP safety (14 models), plus open code and anonymised landmark data.

**Do NOT present** a single rule (a timeout, a confidence threshold) as *the* contribution - a peer already warned this reads as "a basic remote-control system".
The timeout is a derived consequence of the analysis, and the paper says so. The result that carries it: at 8 m through a wall the fail-safe removes every loss-driven violation but
trips ~27 times/min/robot - safety is bought with availability.

## 1. Sections, owners, planning word targets
(Targets are for planning, ~7,000-8,000 words total with a ~250-word results-bearing abstract; check the current Springer/Sādhanā instructions PDF before submission.
Owners are proposals - swap freely; each owner also checks every number in their section against `data/paper_numbers.md`.)

| # | Section | Words | Owner (proposed) | Source material |
|---|---|---|---|---|
| - | Abstract + keywords (6-7) | 250 | Writing lead (Person D) - write LAST | `paper_numbers.md` |
| 1 | Introduction: motivation (disaster response, agriculture, education; low-cost, India relevance), gap, contributions | 700 | Person D | this file section 0 |
| 2 | Related work: HSI for swarms; gesture control (RAIST, Robotica 2026, uncertainty-aware gesture HRI); swarm safety/dependability (Winfield, Wei-Timmis, Badithela); wireless loss models | 900 | Vivek | `novelty-check` Project doc, `SUBMISSION_CHECKLIST.md` reference fixes |
| 3 | System and safety requirement: pipeline, vocabulary (6 gestures), requirement "all robots at rest within T_STOP = 1.0 s", V_MAX 0.22 m/s, A_MAX 0.3 m/s^2 (0.733 s braking) | 700 | Yash | `classifier.py`, `sim_v2.py`, `safety.py` |
| 4 | Data and measurements: gesture dataset (8 people, 3 conditions, counterbalanced); dedicated STOP dataset (protocol, second-person pose check); Wi-Fi measurement setup (sender-hosted hotspot, 2 Mac receivers; R1/R3 excluded and why); classifier set-up | 1,200 | Sahil | `STOP_DATASET_PROTOCOL.md`, `wifi-measurement-2026-11-02.md`, `data/wifi_runs/notes.txt` |
| 5 | Dependability model: shared misread; rebroadcast + latching; Gilbert-Elliott; closed form; trace replay; fail-safe bound; peer relay | 1,100 | Yash | `sim_v2.py`, `run_trace_study.py`, `reprice_totals.py` |
| 6 | Results (6.1 recognition; 6.2 classifier comparison; 6.3 STOP misread; 6.4 measured Wi-Fi; 6.5 violation vs loss/burst/N; 6.6 trace replay + fail-safe trade-off; 6.7 relay; 6.8 Gazebo validation) | 1,500 | Yash (6.4-6.8) + Sahil (6.1-6.3) | figures below |
| 7 | Discussion: design implications (range/link monitoring, fail-safe, pose vocabulary, relay conditions) and limitations | 700 | Person D | limitations list below |
| 8 | Conclusions | 250 | Person D | |
| - | References (author-year), Data availability, Ethics statement, Acknowledgements | - | Vivek (refs) / as agreed (ethics) | `SUBMISSION_CHECKLIST.md` |

## 2. Figures and tables (all regenerable)
- Fig 1 pipeline + safety timeline (redraw; do not reuse RAIST figures).
- Fig 2 violation vs loss/burst/swarm size - `figures/v2_violation_vs_loss_burst.png`.
- Fig 3 confirmation window: STOP misread flat for both datasets - `figures/v2_confirmation_window.png`.
- Fig 4 fail-safe timeout: violations vs nuisance stops - `figures/v2_failsafe_timeout.png`.
- Fig 5 peer relay vs broadcast - `figures/v2_peer_relay.png`.
- Fig 6 measured Wi-Fi: burst-length distribution and per-session loss (TO MAKE from `data/wifi_runs`, `wifi/analysis/analyze_wifi.py`).
- Fig 7 trace-replay: violation and fail-safe trips per minute by channel (TO MAKE from `data/trace_study.csv`).
- Fig 8 Gazebo braking validation - `figures/gz_*.png`.
- Tab A classifier comparison (14 models; `CLASSIFIER_COMPARISON.md`); Tab B per-condition recognition; Tab C FMEA (`data/fmea_table.csv`); Tab D STOP misread both datasets.

## 3. Key numbers (only these; source: `data/paper_numbers.md`, `TRACE_STUDY_RESULTS.md`)
- Recognition 84.1% per command (voted), per-condition far 87.2 / near 84.5 / dim 80.7%.
- STOP misread: dedicated held-out 3/481 = 0.62% (0.21-1.82%); original 2/157 = 1.27% (0.35-4.53%). The three new errors: P04 near_dim -> CIRCLE, P06 far_bright -> LINE, P08 near_bright -> CLUSTER.
- Wi-Fi (one day, one hotspot): loss 2.0-2.7% quiet, 3.7-9.0% busy, 7.5% / 42% far; longest outages 0.4-1.2 s nearby, 5-9 s far.
- Trace replay N=8: latching only 0.8-3.4% nearby, 11% (R2 far), 53% (R4 far, 8 m); with fail-safe 0.62% everywhere; trips/min/robot 0.7-2.8 nearby, 27.4 at R4 far.
- Fail-safe bound 0.234 s = T_STOP - 0.033 - V_MAX/A_MAX. Gazebo stop 0.750 s vs kinematic 0.733 s.

## 4. Must-resolve before writing results (do not skip)
1. **Three different STOP-misread numbers exist** (1.56% in the classifier table, 1.27% original W=1, 0.62% dedicated). They are different evaluations
   (cross-model LOPO with 15-frame vote vs W=1 vs a new held-out set). Pick the dedicated 0.62% as the model input, use 1.56% only inside the classifier table, and define each in Methods.
2. **Held-out argument:** the rule thresholds were tuned on the original data, so only the dedicated set is out-of-sample. Never tune on it.
3. **Pooling:** the dedicated set had a second-person pose check, the original did not (CLUSTER read as STOP: 16/167 vs 45/186). Report separately, do not pool silently.
4. **Wi-Fi limits stated plainly:** sender-hosted Windows hotspot, sender radio also a client of an iPhone hotspot, two Mac receivers, 3 x 10 min, one day; R1 (20% reception even at 2-3 m) and R3 (0 packets) excluded for receiver-side reasons; R2's single 9 s outage coincides with a sender clock jump and is unexplained.
5. **Closed form vs simulation:** they agree within sampling error for most cells but differ by up to ~5 points for 1 s bursts (e.g. 42.6% vs 47.3%); explain (grid/timing) or restrict the closed-form claim.
6. **Robots independent in the trace replay;** measured overlap of losses between side-by-side receivers is small (14% / 11% quiet) but not zero.

## 5. Where reviewers will push (answer in the Discussion, not by hope)
- Simulation only, no hardware swarm (one Gazebo run). - 8 participants, team-adjacent. - One Wi-Fi setup. - Relay airtime/collisions not modelled.
- Fist-vs-thumbs-up (CIRCLE 47%) and OK-sign-as-STOP are properties of the chosen vocabulary. - Vocabulary grew vs RAIST (4 -> 6 gestures; fist = CIRCLE, thumbs-up = WAIT, OK = CLUSTER): explain why.
- RAIST reports 95.0% in the abstract and 96.25% in Table 2: note it neutrally in one line. - Overlap with RAIST: cite it, write everything fresh, redraw figures.
- ST-GCN (56% accuracy) overfit on a small dataset: mention only as a cautionary note; no ProtoGCN/SkeletonAgent claims.

## 6. Still to do (owners)
| Task | Owner |
|---|---|
| Read the Robotica 2026 gesture-HSI paper and the Sens. Actuators A 2024 uncertainty-aware paper fully; write 3 lines each on how we differ | Vivek |
| Fix the RAIST reference errors (list in `SUBMISSION_CHECKLIST.md`) and verify every reference | Vivek |
| Make Fig 6 and Fig 7 | Sahil (6), Yash (7) |
| Decide authorship and corresponding author; repo visibility; ethics and data-availability statements | team |
| Write sections 3, 5, 6.4-6.8 first (numbers are locked) | Yash |
| Write sections 4, 6.1-6.3 | Sahil |
| Related work and references | Vivek |
| Introduction, discussion, conclusion, abstract; assemble and read end to end | Person D (name to be agreed) |
| Final check: every number in the text against `data/paper_numbers.md`; regenerate with `make_numbers_sheet.py` after any data change | all |
