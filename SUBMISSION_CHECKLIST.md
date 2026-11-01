# Sādhanā submission checklist (status 1 Nov 2026)

## Done (verified from data, see data/paper_numbers.md)
- [x] Novelty: OpenAlex (19 queries + citation tracking) and IEEE Xplore (8 queries). No paper combines a measured gesture channel + STOP-safety analysis of a decentralized swarm + fail-safe rule. Details: Project doc `novelty-check-2026-11-01.md`.
- [x] Every paper number regenerated from data in one file (`make_numbers_sheet.py` -> `data/paper_numbers.md`). Use only these numbers.
- [x] Closed-form check: baseline violation = 1-(1-p)^N with measured p = 1.32% gives 10.1/19.2/34.6% vs simulated 12.5/22.0/34.5% (all inside 95% CIs). Report it: it shows the sim is consistent and the N-effect is not a sim artefact.
- [x] Recognition reported per command (15-frame vote) everywhere: 84.1%; per-frame 83.4% only as secondary.
- [x] FMEA occurrence scores updated to final data (old rationale quoted the placeholder matrix). Ranking: dropped STOP 378, scaling 200, misread STOP 189, braking 84, nuisance 36.
- [x] Gazebo summary fixed: a parked robot's wheel jitter (0.012 m/s, <1 mm) was counted as "moving". Now uses >1 cm displacement. Result unchanged: robots 1 and 5 violate.

## Must do before submission (humans)
- [ ] **Consent.** Confirm every person in BOTH recording sessions (31 Oct night, 1 Nov counterbalanced) signed/initialled consent. Without it you cannot publish or release the dataset.
- [ ] **Ethics statement.** Ask COEP whether the gesture study needs formal approval or an exemption letter. Springer journals require a statement on human participants and informed consent.
- [ ] **Repo visibility.** The GitHub repo is PUBLIC now and holds participant data. Either make it private until acceptance, or keep it public deliberately and cite it as the data availability link (anonymised P01-P08 only - already true).
- [ ] **Overlap with RAIST 2026.** Cite it as prior work; write all text fresh (Springer runs a similarity check). Do not reuse RAIST figures (hand-landmark photo, workflow, star topology) unless redrawn and cited.
- [ ] **Gesture mapping changed since RAIST.** RAIST: fist = WAIT, 4 gestures. This study: fist = CIRCLE, thumbs-up = WAIT, OK-sign = CLUSTER, 6 gestures. State this explicitly or a reviewer comparing the two papers will flag it.
- [ ] **Correct the RAIST reference errors in the new bibliography:**
  - Suresh & Martínez: IFAC-PapersOnLine 51(34):83-88, 2019 (arXiv 1804.08676, not 1803.01104)
  - Kakish, Vedartham & Berman: arXiv 2102.02439 (not 2103.06847)
  - JAIC quadcopter paper: Wijaya R S, Prayoga S, Fatekha R A, Mubarak M T 2025 "A Real-Time Hand Gesture Control of a Quadcopter Swarm Implemented in the Gazebo Simulation Environment", J. Appl. Inform. Comput. 9(3):979-988
  - Alonso-Mora et al. 2015 full title "...and its application to an interactive display", ICRA pp. 5948-5953
  - Şiean et al. 2023 has 5 authors; IJACSA 14(4)
  - Wameed & Alkamachi: OpenAlex lists 2023 and title "Hand Gestures Robotic Control Based on Computer Vision" - check the year
  - RAIST abstract says 95.0%, its Table 2 gives 96.25% - do not repeat either number; cite RAIST for the system only
- [ ] **Read two papers fully:** Robotica 2026 gesture-HSI formation (closest competitor) and "Uncertainty-aware hand gesture recognition for safety-critical and emergency HRI" (Sens. Actuators A 2024).
- [ ] **Authorship and corresponding author** agreed (RAIST had 5 authors, faculty corresponding).
- [ ] Optional: same queries in Scopus via COEP login.

## Journal format (from a 2026 Sādhanā article + IAS rules)
- Submit via Editorial Manager (editorialmanager.com/sadh). Use the current Springer instructions PDF on the journal's submission-guidelines page for template details.
- References: author-year, e.g. `Kolling A, Walker P, Chakraborty N, Sycara K and Lewis M 2016 Human interaction with robot swarms: a survey. IEEE Trans. Hum.-Mach. Syst. 46: 9-26`
- Abstract informative with results (recent papers ~250 words); about 6-7 keywords; numbered sections ending in Conclusion(s).
- Scope wants breadth across groups and relevance to India: frame as low-cost dependability for human-commanded robot teams (disaster response, agriculture, education).
- Recent acceptance timeline seen: received Nov 2025 -> accepted Aug 2026 (~9 months).

## Limitations to state in the paper
- Simulation study (kinematic + one Gazebo validation run), no hardware.
- Latency measured on localhost (processing + stack floor), not field Wi-Fi.
- 8 participants; frames within a hold are correlated, so statistics use voted command instances (n = 2,098).
- Fist vs thumbs-up confusion (CIRCLE 47%): choose more distinct poses in a deployed system.
- Gazebo plots: zig-zags are 20 Hz logging vs 50 Hz odometry; small post-stop speed jitter is contact noise.
- Formation screenshots show robots placed at slot positions, not driven there.
