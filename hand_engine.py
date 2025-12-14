import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            model_complexity=0, # 0 = Lite (Fastest), 1 = Full
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.results = None

    def process(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)
        return self.results

    def get_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            return self.results.multi_hand_landmarks[0].landmark
        return None

    def is_finger_up(self, landmarks, finger_tip_idx, finger_pip_idx):
        # Returns True if the finger tip is higher (lower Y) than the knuckle
        return landmarks[finger_tip_idx].y < landmarks[finger_pip_idx].y