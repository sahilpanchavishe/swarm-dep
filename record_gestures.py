# record_gestures.py
# Captures raw MediaPipe hand landmarks + metadata for the gesture dataset.
# Stores ONLY landmark coordinates (no images), one row per frame.
#
# HOW TO USE (read this):
#   1. Set PARTICIPANT and CONDITION below for the current person/setup.
#   2. Run it. A window shows the webcam + skeleton.
#   3. Press a NUMBER KEY to pick the gesture the person will perform:
#        1=STOP  2=CIRCLE  3=LINE  4=CLUSTER  5=SPLIT  6=WAIT
#      The chosen gesture shows top-left.
#   4. Person holds that gesture. Press 'r' to RECORD ~30 frames of it.
#      Screen flashes "RECORDING". Do this a few times per gesture.
#   5. Repeat for each gesture. Press 'q' to finish and save.
#   6. For the next CONDITION or PERSON: change the variables, run again.

import cv2
import mediapipe as mp
import csv
import os
import time

# ---- SET THESE PER SESSION ----
PARTICIPANT = "P08"          # change for each person: P01, P02, ...
CONDITION = "near_dim"   # e.g. near/far, bright/dim, left/right hand
FRAMES_PER_RECORD = 30       # frames captured per 'r' press
# --------------------------------

GESTURES = {ord('1'): "STOP", ord('2'): "CIRCLE", ord('3'): "LINE",
            ord('4'): "CLUSTER", ord('5'): "SPLIT", ord('6'): "WAIT"}

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

os.makedirs("data/gesture_recordings", exist_ok=True)
out_path = f"data/gesture_recordings/{PARTICIPANT}_{CONDITION}.csv"

# CSV header: metadata + handedness + 63 landmark coords (x0,y0,z0,...,x20,y20,z20)
header = ["participant", "condition", "intended_gesture", "handedness", "timestamp"]
for i in range(21):
    header += [f"x{i}", f"y{i}", f"z{i}"]

rows = []
cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)

current_gesture = None
recording = 0   # frames left to record in current burst

print(f"Recording for {PARTICIPANT} / {CONDITION}")
print("Keys: 1=STOP 2=CIRCLE 3=LINE 4=CLUSTER 5=SPLIT 6=WAIT | r=record burst | q=quit")

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    hand_present = False
    landmarks = None
    handedness = "NA"
    if result.multi_hand_landmarks:
        hand_present = True
        hand_lm = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
        landmarks = []
        for lm in hand_lm.landmark:
            landmarks += [lm.x, lm.y, lm.z]
        if result.multi_handedness:
            handedness = result.multi_handedness[0].classification[0].label  # "Left"/"Right"

    # If recording a burst and a hand is present, log this frame.
    if recording > 0 and hand_present and current_gesture:
        row = [PARTICIPANT, CONDITION, current_gesture, handedness, time.time()] + landmarks
        rows.append(row)
        recording -= 1

    # --- On-screen status ---
    g = current_gesture or "(none - press 1-6)"
    cv2.putText(frame, f"Gesture: {g}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(frame, f"{PARTICIPANT} / {CONDITION}  logged={len(rows)}", (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    if recording > 0:
        cv2.putText(frame, f"RECORDING ({recording})", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

    cv2.imshow("Gesture recorder", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key in GESTURES:
        current_gesture = GESTURES[key]
        print(f"  gesture set to {current_gesture}")
    elif key == ord('r'):
        if current_gesture:
            recording = FRAMES_PER_RECORD
            print(f"  recording {FRAMES_PER_RECORD} frames of {current_gesture}")
        else:
            print("  pick a gesture first (1-6)")

cap.release()
cv2.destroyAllWindows()

# Save.
with open(out_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)
print(f"\nSaved {len(rows)} frames to {out_path}")