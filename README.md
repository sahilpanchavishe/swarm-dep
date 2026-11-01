# Swarm Dependability Study — Project Status & Handoff

**All numbers for the paper: see `data/paper_numbers.md` (regenerate with `python make_numbers_sheet.py`).**

**Paper (working title):** *Data-Driven Dependability of Gesture-Commanded Decentralized Swarms: Recognition Errors, Packet Loss, and a Fail-Safe Design Rule*
**Target journal:** Sādhanā (Springer, SCIE, Q3)
**Team:** Group 13, COEP Technological University, Pune
**Repo:** github.com/sahilpanchavishe/swarm-dep

---

## 1. The novelty (state it exactly this way)

The contribution is the **measured gesture channel**: real per-gesture confusion, hand-lost
behaviour, and latency recorded from participants, fed into a safety analysis of a
decentralized gesture-commanded swarm, and turned into a fail-safe timeout design rule.

Methods are **borrowed** — FMEA (Winfield), search-based failure testing (Wei & Timmis),
confusion-matrix-to-safety (Badithela). Novelty = the **integration + measured data**, NOT a
new method. Never call it a "novel framework" — that invites those three as counter-citations.

---

## 2. Key results (all from the CLEAN counterbalanced dataset)

- **Gesture recognition:** 84.1% per command (temporal vote, 15 frames; 83.4% per frame). 8 participants, counterbalanced, 3 conditions.
  Strong: LINE 96%, STOP 99%, SPLIT 93%, WAIT 93%, CLUSTER 75%. Weak: CIRCLE 47% (fist vs thumbs-up)
  (fist vs thumbs-up confusion — a real recognition ambiguity, reported as a limitation).
- **Per-condition robustness (now valid — confound fixed):** far 87.2%, near 84.5%, dim 80.7% (per command; dim vs far p<0.001).
  Dim lighting degrades recognition, especially subtle gestures (CLUSTER, WAIT); distance is fine.
- **Dependability (corrected model `sim_v2.py`, 1 Nov 2026):** one shared misread per STOP hold,
  STOP rebroadcast at 30 Hz with latching (as RAIST), Gilbert-Elliott burst loss.
  - 0% loss: violation = P(STOP misread) = 1.27% for every swarm size (no N effect).
  - Short independent drops: rebroadcast defeats them (stays at 1.27% up to 40% loss).
  - Long bursts break it and swarm size returns: 0.3 s bursts, 10% loss -> 27.7% / 49.9% / 72.6%
    for N = 8 / 16 / 32 (closed-form Markov result matches simulation).
  - The answer depends on the real burst statistics -> measure them on the actual Wi-Fi.
- **Fail-safe timeout:** analytic bound timeout <= T_stop - t_rec - v_max/a_max = 0.23 s removes
  loss-driven violations; the shared misread (1.27%) remains. Cost: nuisance stops of 18-38% per
  robot per 3 s at 10% bursty loss -> under bursty Wi-Fi the fail-safe buys safety with availability.
- **Confirmation window:** waiting 33 -> 833 ms does not change STOP misreads (both misread holds are
  pose-level: P08, dim, read as LINE on every frame). Don't delay STOP for voting.
- **Peer relay of STOP (`run_relay_study.py`):** robots that hold STOP rebroadcast it to neighbours.
  If bursts are path fading, relay removes every loss-driven violation and safety no longer depends on
  swarm size (0.3 s bursts, 10% loss, N=32: 75.6% -> 1.3%). If bursts are the robot's own receiver
  going deaf, relay gives nothing. At a 50/50 split: 72.7% -> 46.4%. Relay never fixes the shared misread.
- **FMEA:** regenerated on `sim_v2` at a stated reference Wi-Fi condition (placeholder until measured).
- **Superseded:** v1 results (N-effect at 0% loss, 0.4-0.5 s timeout) are in `superseded_v1/` with the reason.

---

## 3. The confound — found and fixed (important for the paper)

Last night's first recordings were confounded: all participants recorded conditions in the
SAME order (near→far→dim), so accuracy rose with recording order (practice), not condition —
dim implausibly scored HIGHEST. See `analyze_confound.py` (keep this; it justifies the re-record).

**Fixed by re-recording with counterbalanced order** (Latin square — see `data/gesture_recordings_cb/`).
Now dim correctly scores lowest. The clean counterbalanced data is the canonical dataset for
all results above. The old confounded data (`data/gesture_recordings/`) is kept only as record.

---

## 4. What's NOT done (remaining work)

- [ ] **Novelty check** (Scopus + IEEE Xplore) — do FIRST, protects against desk rejection.
      Queries: "human-swarm interaction" AND (dependability OR "fault tolerance");
      "gesture" AND swarm AND (safety OR failure); "confusion matrix" AND safety AND robot;
      "packet loss" AND swarm AND (command OR gesture).
- [ ] **Confirm consent forms** signed by all participants — blocker for releasing the dataset.
- [ ] **Write the paper** — biggest remaining chunk. Split across the 4 of you (section 6).
- [ ] **Repo cleanup** — delete throwaway `log_robot_*.csv`.

---

## 5. File map

| File | What it does |
|---|---|
| `robot.py` | TurtleBot3 kinematic model (+ deceleration) |
| `controller.py` | Decentralized potential-field controller |
| `formations.py` | Target shapes (circle/line/cluster/split) |
| `protocol.py`, `op_sender.py`, `robot_node.py` | Real UDP command channel |
| `run_validation.py`, `analyze_latency.py` | Measure + summarize latency |
| `channel_model.py` | Loads measured latency + confusion matrix; injects faults |
| `safety.py` | STOP-within-T_stop safety requirement |
| `run_episode.py` | One fault-injected episode + safety check |
| `run_study.py` | Full sweep (loss × swarm size) → study_results.csv |
| `make_figure.py` | Headline figure: violation rate vs packet loss |
| `run_episode_supervised.py`, `make_design_rule.py` | Fail-safe supervisor + design-rule figure |
| `make_fmea.py` | FMEA table |
| `record_gestures.py` | Captures landmarks from participants (writes to gesture_recordings_cb/) |
| `classifier.py` | Rule-based gesture classifier (fit to measured poses) |
| `build_confusion.py` | Runs classifier over dataset → confusion_matrix.csv |
| `diagnose_poses.py` | Shows actual finger patterns per gesture (debugging) |
| `analyze_confound.py` | Demonstrates the recording-order confound (proof for the paper) |
| `per_condition_accuracy.py`, `per_condition_cb.py` | Per-condition accuracy (old / clean data) |

**Environments:** `venv` (Python 3.12, sim code) and `venv311` (Python 3.11 + MediaPipe
0.10.21 — NOT 1.2.0, a fake package). Recording/classifier need venv311.

---

## 6. Suggested 4-person task split (no git conflicts — different files/sections)

- **Person A (sim):** owns robot/controller/run_episode; any sim refinements; seed counts.
- **Person B (data):** classifier, confusion matrix, per-condition results; consent forms.
- **Person C (analysis + related work):** FMEA; Scopus/IEEE novelty check; Related Work section
  built on Winfield / Wei-Timmis / Badithela (+ the Robotica gesture-swarm paper, and the
  uncertainty-aware-gesture HRI paper — distinguish from both).
- **Person D (writing lead):** paper structure, Methods, Results, figures; assemble all pieces;
  verify every reference before submission.

Everyone: understand the whole pipeline — any of you may field a reviewer question on any part.

---

## 7. Hard rules carried from the build

- Never report a number as "measured" that was assumed.
- Report n and confidence intervals (now 200 seeds); state what samples can't conclude.
- Random-search only — say optimizer-based search (CMA-ES) is future work.
- Cite RAIST; check Sādhanā's conference-extension policy before submitting.
- Classifier thresholds (1.05, 0.55) are tuned, not derived — verified robust via sensitivity
  (if that check was run); note as a limitation.
- CIRCLE↔WAIT (fist vs thumbs-up) confusion is a real limitation — note choosing more distinct
  poses would improve recognition.
