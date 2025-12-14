import cv2
import time
import numpy as np
import config as cfg
from hand_engine import HandTracker
from utils import OneEuroFilter, calculate_distance
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

def main():
    cap = cv2.VideoCapture(cfg.CAMERA_ID)
    tracker = HandTracker()
    mouse = MouseController()
    keyboard = KeyboardController()

    # Heavy smoothing filters
    x_filter = OneEuroFilter(time.time(), 0, min_cutoff=cfg.FILTER_MIN_CUTOFF, beta=cfg.FILTER_BETA)
    y_filter = OneEuroFilter(time.time(), 0, min_cutoff=cfg.FILTER_MIN_CUTOFF, beta=cfg.FILTER_BETA)
    
    dragging = False
    zooming = False
    prev_y = 0
    active_gesture = "IDLE"

    print(">> VIRT MOUSE STABLE MODE")
    print(">> [FIST] = PAUSE MOUSE")
    print(">> [INDEX] = MOVE")
    print(">> [L-SHAPE] = ZOOM")
    print(">> [PEACE] = SCROLL")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        
        if cfg.MIRROR_MODE:
            frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape
        
        # 1. Draw Active Area (White Box)
        cv2.rectangle(frame, (cfg.ACTIVE_AREA_MARGIN, cfg.ACTIVE_AREA_MARGIN), 
                      (w - cfg.ACTIVE_AREA_MARGIN, h - cfg.ACTIVE_AREA_MARGIN), 
                      cfg.COLOR_BOX, 2)

        tracker.process(frame)
        lm = tracker.get_landmarks()
        current_time = time.time()

        if lm:
            # 2. Get STABILIZED Gesture (No flickering!)
            active_gesture = tracker.get_stable_gesture(lm)

            # 3. Calculate Position (Inside Box -> Full Screen)
            raw_x = np.interp(lm[8].x * w, (cfg.ACTIVE_AREA_MARGIN, w - cfg.ACTIVE_AREA_MARGIN), (0, cfg.SCREEN_WIDTH))
            raw_y = np.interp(lm[8].y * h, (cfg.ACTIVE_AREA_MARGIN, h - cfg.ACTIVE_AREA_MARGIN), (0, cfg.SCREEN_HEIGHT))
            
            smooth_x = x_filter(current_time, raw_x)
            smooth_y = y_filter(current_time, raw_y)

            # Visual Feedback: Draw point on Index Finger
            color = cfg.COLOR_INDEX
            if active_gesture == "PAUSE": color = cfg.COLOR_PAUSE
            elif active_gesture == "ZOOM": color = cfg.COLOR_ZOOM
            
            cv2.circle(frame, (int(lm[8].x * w), int(lm[8].y * h)), 8, color, -1)
            cv2.putText(frame, f"MODE: {active_gesture}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # --- EXECUTION LOGIC ---

            # A. PAUSE MODE (Fist)
            if active_gesture == "PAUSE":
                # Do nothing. Mouse is frozen.
                if dragging: 
                    mouse.release(Button.left)
                    dragging = False
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False

            # B. ZOOM MODE (L-Shape)
            elif active_gesture == "ZOOM":
                if not zooming:
                    keyboard.press(Key.ctrl)
                    zooming = True
                
                zoom_delta = (prev_y - smooth_y) / 5
                if abs(zoom_delta) > 0.2:
                    mouse.scroll(0, int(zoom_delta * cfg.ZOOM_SPEED))

            # C. SCROLL MODE (Peace Sign)
            elif active_gesture == "SCROLL":
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False
                
                scroll_delta = (prev_y - smooth_y) / 5
                if abs(scroll_delta) > 0.2:
                    mouse.scroll(0, int(scroll_delta * cfg.SCROLL_SPEED))

            # D. MOVE MODE (Index Only)
            elif active_gesture == "MOVE":
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False

                # Move Mouse
                try: mouse.position = (smooth_x, smooth_y)
                except: pass

                # CLICKS (Distances)
                dist_index_thumb = calculate_distance(lm[8], lm[4]) * w
                dist_middle_thumb = calculate_distance(lm[12], lm[4]) * w

                # Left Click (Index + Thumb)
                if dist_index_thumb < cfg.CLICK_THRESHOLD:
                    if not dragging:
                        mouse.press(Button.left)
                        dragging = True
                        cv2.circle(frame, (int(lm[8].x*w), int(lm[8].y*h)), 15, cfg.COLOR_CLICK, 2)
                else:
                    if dragging:
                        mouse.release(Button.left)
                        dragging = False

                # Right Click (Middle + Thumb)
                if dist_middle_thumb < cfg.CLICK_THRESHOLD:
                    mouse.click(Button.right, 1)
                    time.sleep(0.3)

            # Update Previous Y for scrolling/zooming calculation
            prev_y = smooth_y

        cv2.imshow('Virt Mouse HUD', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            if zooming: keyboard.release(Key.ctrl)
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()