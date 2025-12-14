import cv2
import time
import config as cfg
from hand_engine import HandTracker
from utils import OneEuroFilter, calculate_distance, map_range
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

def main():
    # 1. Init Hardware
    cap = cv2.VideoCapture(cfg.CAMERA_ID)
    tracker = HandTracker()
    mouse = MouseController()
    keyboard = KeyboardController()

    # 2. Init Filters (Start at 0,0)
    x_filter = OneEuroFilter(time.time(), 0, min_cutoff=0.01, beta=0.5)
    y_filter = OneEuroFilter(time.time(), 0, min_cutoff=0.01, beta=0.5)
    
    dragging = False
    zooming = False
    prev_y = 0

    print(">> VIRT MOUSE ENGINE STARTED")
    print(">> [1 Finger] Move  |  [2 Fingers] Scroll  |  [3 Fingers] Zoom")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        
        if cfg.MIRROR_MODE:
            frame = cv2.flip(frame, 1)

        # Process Hand
        tracker.process(frame)
        lm = tracker.get_landmarks()
        h, w, _ = frame.shape
        current_time = time.time()

        if lm:
            # Detect States
            index_up = tracker.is_finger_up(lm, 8, 6)
            middle_up = tracker.is_finger_up(lm, 12, 10)
            ring_up = tracker.is_finger_up(lm, 16, 14)

            # Raw Coordinates
            raw_x = map_range(lm[8].x, 0, 1, 0, cfg.SCREEN_WIDTH)
            raw_y = map_range(lm[8].y, 0, 1, 0, cfg.SCREEN_HEIGHT)
            
            # Apply Smoothing
            smooth_x = x_filter(current_time, raw_x)
            smooth_y = y_filter(current_time, raw_y)

            # --- MODE SWITCHING ---

            # MODE 3: ZOOM (Index + Middle + Ring)
            if index_up and middle_up and ring_up:
                if not zooming:
                    keyboard.press(Key.ctrl) # Hold Ctrl
                    zooming = True
                
                # Vertical movement controls zoom
                zoom_delta = (prev_y - smooth_y) / 5
                if abs(zoom_delta) > 0.5:
                    mouse.scroll(0, int(zoom_delta * cfg.ZOOM_SPEED))
                
                cv2.putText(frame, "ZOOM MODE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, cfg.COLOR_ZOOM, 2)
                cv2.line(frame, (int(lm[8].x*w), int(lm[8].y*h)), (int(lm[16].x*w), int(lm[16].y*h)), cfg.COLOR_ZOOM, 3)

            # MODE 2: SCROLL (Index + Middle)
            elif index_up and middle_up:
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False

                scroll_delta = (prev_y - smooth_y) / 5
                if abs(scroll_delta) > 0.5:
                    mouse.scroll(0, int(scroll_delta * cfg.SCROLL_SPEED))

                cv2.putText(frame, "SCROLL MODE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, cfg.COLOR_SCROLL, 2)

            # MODE 1: CURSOR (Index Only)
            elif index_up:
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False

                # Move Mouse
                try: mouse.position = (smooth_x, smooth_y)
                except: pass

                # Check Click (Index tip near Thumb tip)
                dist = calculate_distance(lm[8], lm[4]) * w
                
                if dist < cfg.CLICK_THRESHOLD:
                    if not dragging:
                        mouse.press(Button.left)
                        dragging = True
                        cv2.circle(frame, (int(lm[8].x*w), int(lm[8].y*h)), 15, cfg.COLOR_CLICK, -1)
                else:
                    if dragging:
                        mouse.release(Button.left)
                        dragging = False

            # IDLE (No fingers / Fist)
            else:
                if zooming:
                    keyboard.release(Key.ctrl)
                    zooming = False

            prev_y = smooth_y

        cv2.imshow('Virt Mouse HUD', frame)
        
        # Press ESC to quit
        if cv2.waitKey(1) & 0xFF == 27:
            if zooming: keyboard.release(Key.ctrl)
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()