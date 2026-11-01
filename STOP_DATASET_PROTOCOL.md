# Dedicated STOP dataset (tightens the safety-critical number)

Why: the STOP misread rate (1.27%) rests on 2 holds, both P08 in dim light, read as LINE on every
frame. 95% CI is 0.35-4.5%. If those 2 were a labelling slip the true rate may be ~0; if not, it is
a real pose problem. Either way the paper needs more STOP holds.

Target: >= 60 STOP holds per person x 8 people (~480 holds), plus 20 holds each of LINE and CLUSTER
(the two gestures STOP gets confused with) so false-STOP rates are measured on the same day.

Protocol
1. In `record_gestures.py` set the output folder to `data/gesture_recordings_stop` (both lines).
2. Same three conditions (near_bright, far_bright, near_dim), counterbalanced with the same Latin
   square as before. Same poses: STOP = open palm, all five fingers spread.
3. A second person watches and confirms the pose is an open palm BEFORE the operator presses `r`.
   If the pose was wrong, note the hold number and re-record it - this removes labelling slips.
4. Each `r` press = one hold (30 frames). 20 STOP presses per condition per person.
5. Consent: same consent form; new participants must sign before recording.

Analysis: `python misread_vs_window.py` after pointing its glob at the new folder (or both folders).
Report k/n and the Wilson 95% CI. If k = 0 of ~480, the 95% upper bound is ~0.8%.
