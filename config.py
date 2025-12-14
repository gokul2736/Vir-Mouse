# config.py

# --- CAMERA ---
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIRROR_MODE = True

# --- INTERACTION BOX ---
ACTIVE_AREA_MARGIN = 150  # Keep hand inside this box!

# --- PHYSICS ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
# INCREASED SMOOTHING: High min_cutoff = "Sticky" cursor (stable).
FILTER_MIN_CUTOFF = 0.1  # Previously 0.5. 0.1 makes it very smooth.
FILTER_BETA = 0.1        # Response speed.

# --- GESTURES ---
CLICK_THRESHOLD = 40
SCROLL_SPEED = 5
ZOOM_SPEED = 3

# --- COLORS (BGR) ---
COLOR_INDEX = (0, 255, 0)      # Green (Active)
COLOR_PAUSE = (0, 0, 255)      # Red (Paused/Fist)
COLOR_CLICK = (0, 255, 255)    # Yellow
COLOR_BOX = (255, 255, 255)    # White
# The missing variables caused your error:
COLOR_ZOOM = (255, 0, 255)     # Magenta 
COLOR_SCROLL = (255, 255, 0)   # Cyan