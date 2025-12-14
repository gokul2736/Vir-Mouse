import cv2
import mediapipe as mp
import collections

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            model_complexity=0,
            max_num_hands=1,
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        self.results = None
        # This "deque" stores the last 5 frames to stop flickering
        self.gesture_buffer = collections.deque(maxlen=5)

    def process(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)
        return self.results

    def get_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            return self.results.multi_hand_landmarks[0].landmark
        return None

    def is_finger_up(self, lm, tip_idx, pip_idx, wrist_idx):
        # Finger is UP if tip is higher (smaller Y) than the knuckle
        return lm[tip_idx].y < lm[pip_idx].y

    def get_stable_gesture(self, lm):
        # 1. Check fingers
        index = self.is_finger_up(lm, 8, 6, 0)
        middle = self.is_finger_up(lm, 12, 10, 0)
        ring = self.is_finger_up(lm, 16, 14, 0)
        pinky = self.is_finger_up(lm, 20, 18, 0)
        
        # Check Thumb (Simple check: is tip far from knuckle?)
        thumb_out = abs(lm[4].x - lm[2].x) > 0.04

        current_state = "IDLE"

        # 0. FIST -> PAUSE (All fingers down)
        if not index and not middle and not ring and not pinky:
            current_state = "PAUSE"

        # 1. ZOOM: L-Shape (Index Up + Thumb Out + Others Down)
        elif index and thumb_out and not middle and not ring:
            current_state = "ZOOM"

        # 2. SCROLL: Peace Sign (Index + Middle Up)
        elif index and middle and not ring:
            current_state = "SCROLL"

        # 3. MOVE: Index Only
        elif index and not middle:
            current_state = "MOVE"

        # --- STABILITY BUFFER ---
        # We wait until the gesture is detected for 3 frames before switching
        self.gesture_buffer.append(current_state)
        most_common = collections.Counter(self.gesture_buffer).most_common(1)
        if most_common[0][1] >= 3: 
            return most_common[0][0]
        else:
            return self.gesture_buffer[-1]