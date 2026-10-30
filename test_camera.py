# test_camera.py - confirm webcam + MediaPipe detect a hand before recording anyone.
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)   # 0 = default webcam
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

print("Press 'q' to quit. Show your hand to the camera.")
while True:
    ok, frame = cap.read()
    if not ok:
        print("Camera not readable"); break
    frame = cv2.flip(frame, 1)                      # mirror, feels natural
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    if result.multi_hand_landmarks:
        for hand_lm in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
        cv2.putText(frame, "HAND DETECTED", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("MediaPipe test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()