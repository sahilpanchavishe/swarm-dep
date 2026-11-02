# record_stop.py - dedicated STOP-dataset recorder (safer than record_gestures.py).
# Usage:  python record_stop.py P01 near_bright
#   keys: 1=STOP 3=LINE 4=CLUSTER | r = record one hold (30 frames) | u = UNDO last hold | q = save & quit
# Differences from record_gestures.py: participant/condition on the command line (no editing),
# writes to data/gesture_recordings_stop/, saves after EVERY hold (a crash loses nothing),
# never overwrites an existing file, shows hold counts, and 'u' removes a mislabelled hold.
import sys, os, csv, time
import cv2, mediapipe as mp
if len(sys.argv) != 3: sys.exit("usage: python record_stop.py P01 near_bright")
PARTICIPANT, CONDITION = sys.argv[1], sys.argv[2]
FRAMES = 30
GEST = {ord('1'): "STOP", ord('3'): "LINE", ord('4'): "CLUSTER"}
os.makedirs("data/gesture_recordings_stop", exist_ok=True)
out = f"data/gesture_recordings_stop/{PARTICIPANT}_{CONDITION}.csv"
if os.path.exists(out): out = out.replace(".csv", f"_{time.strftime('%H%M%S')}.csv")
header = ["participant", "condition", "intended_gesture", "handedness", "timestamp"] + \
         [f"{a}{i}" for i in range(21) for a in "xyz"]
holds = []                 # list of (gesture, [rows])
mph = mp.solutions.hands; draw = mp.solutions.drawing_utils
hands = mph.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0); cur = None; left = 0; buf = []
def save():
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header)
        for _, rs in holds: w.writerows(rs)
def count(g): return sum(1 for h in holds if h[0] == g)
print(f"{PARTICIPANT}/{CONDITION} -> {out}\nSECOND PERSON must confirm the pose BEFORE 'r' is pressed. 'u' undoes the last hold.")
while True:
    ok, fr = cap.read()
    if not ok: continue
    fr = cv2.flip(fr, 1); res = hands.process(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    lm = None; hd = "NA"
    if res.multi_hand_landmarks:
        h = res.multi_hand_landmarks[0]; draw.draw_landmarks(fr, h, mph.HAND_CONNECTIONS)
        lm = [v for p in h.landmark for v in (p.x, p.y, p.z)]
        if res.multi_handedness: hd = res.multi_handedness[0].classification[0].label
    if left > 0 and lm and cur:
        buf.append([PARTICIPANT, CONDITION, cur, hd, time.time()] + lm); left -= 1
        if left == 0:
            holds.append((cur, buf)); buf = []; save()
            print(f"  hold saved: {cur}  (STOP={count('STOP')} LINE={count('LINE')} CLUSTER={count('CLUSTER')})")
    cv2.putText(fr, f"Gesture: {cur or '(press 1/3/4)'}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 255, 0), 2)
    cv2.putText(fr, f"{PARTICIPANT}/{CONDITION}  STOP={count('STOP')}/20  LINE={count('LINE')}  CLUSTER={count('CLUSTER')}",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 0), 2)
    if left > 0: cv2.putText(fr, f"RECORDING ({left})", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 255), 3)
    cv2.imshow("STOP recorder", fr); k = cv2.waitKey(1) & 0xFF
    if k == ord('q'): break
    elif k in GEST: cur = GEST[k]; print("  gesture:", cur)
    elif k == ord('r') and cur and left == 0: left = FRAMES; buf = []
    elif k == ord('u') and holds:
        g, _ = holds.pop(); save(); print(f"  UNDID last hold ({g}); remember to redo it")
cap.release(); cv2.destroyAllWindows(); save(); print("saved", out, "holds:", len(holds))
