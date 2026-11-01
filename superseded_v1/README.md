# Superseded (v1 model) — do not use for the paper

These results came from the first dependability model, which had two flaws:
1. Gesture misclassification was drawn separately for every robot. In the real system there is one
   camera, one classifier and one broadcast, so a misread hits the whole swarm or none of it.
   The v1 "swarm-size effect at 0% loss" (12.5% -> 34.5%) was an artefact of this.
2. STOP was sent once. RAIST rebroadcasts at >30 Hz with latching, so one dropped packet cannot
   make a robot miss the STOP; only long loss bursts can.

All paper results now come from `sim_v2.py` (`run_study_v2.py`, `design_rule_v2.py`,
`misread_vs_window.py`, `make_figures_v2.py`, `make_numbers_sheet.py`). Kept here for the record.
