import cv2
import os
import math
import urllib.request

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

_HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

# Standard 21-connection skeleton for drawing (same topology as the old
# mp.solutions.hands.HAND_CONNECTIONS).
_HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # Index
    (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
    (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (0, 17),                               # Palm base
]


def _default_model_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _default_model_path():
    return os.path.join(_default_model_dir(), "models", "hand_landmarker.task")


def _download_model(dst):
    """Download the official hand_landmarker.task model to dst."""
    dst_dir = os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    print("[HandTracker] Downloading hand_landmarker.task model ...")
    temp_path = dst + ".part"
    try:
        urllib.request.urlretrieve(_HAND_LANDMARKER_URL, temp_path)
        os.replace(temp_path, dst)
        print("[HandTracker] Model saved to %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1e6))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def ensure_hand_landmarker_model(model_asset_path=None):
    """Return a path to a usable hand_landmarker.task model, downloading if needed."""
    candidates = []
    if model_asset_path:
        candidates.append(model_asset_path)
    env_path = os.environ.get("HAND_LANDMARKER_MODEL")
    if env_path:
        candidates.append(env_path)
    candidates.append(_default_model_path())

    for cand in candidates:
        if cand and os.path.isfile(cand) and os.path.getsize(cand) > 0:
            return cand

    # Nothing found locally -> download the official model.
    try:
        _download_model(_default_model_path())
        if os.path.isfile(_default_model_path()) and os.path.getsize(_default_model_path()) > 0:
            return _default_model_path()
    except Exception as e:
        raise RuntimeError(
            "Hand landmarker model is missing and could not be downloaded "
            "(%s). Download it from %s and place it at %s"
            % (e, _HAND_LANDMARKER_URL, _default_model_path())
        ) from e

    raise RuntimeError(
        "Hand landmarker model is missing. Place it at %s "
        "or set the HAND_LANDMARKER_MODEL environment variable." % _default_model_path()
    )


class HandDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5, model_asset_path=None):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        model_path = ensure_hand_landmarker_model(model_asset_path)
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=maxHands,
            min_hand_detection_confidence=float(detectionCon),
            min_hand_presence_confidence=float(detectionCon),
            min_tracking_confidence=float(trackCon),
        )
        self.hands = vision.HandLandmarker.create_from_options(options)

        self.tipIds = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        self.jointIds = [2, 6, 10, 14, 18]  # Thumb MCP, Index PIP, Middle PIP, Ring PIP, Pinky PIP

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        results = self.hands.detect(mp_image)

        allHands = []
        h, w, c = img.shape
        num_hands = len(results.hand_landmarks) if results.hand_landmarks else 0

        for i in range(num_hands):
            hand_landmarks = results.hand_landmarks[i]
            myHand = {}
            lmList = []
            xList = []
            yList = []
            for lm in hand_landmarks:
                px, py = int(lm.x * w), int(lm.y * h)
                lmList.append([px, py])
                xList.append(px)
                yList.append(py)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            boxW, boxH = xmax - xmin, ymax - ymin
            bbox = xmin, ymin, boxW, boxH
            cx, cy = bbox[0] + (boxW // 2), bbox[1] + (boxH // 2)

            if i < len(results.handedness) and results.handedness[i]:
                hand_type = results.handedness[i][0].category_name
            else:
                hand_type = "Right"

            myHand["lmList"] = lmList
            myHand["bbox"] = bbox
            myHand["center"] = (cx, cy)
            myHand["type"] = hand_type

            if draw:
                # Draw skeleton connections and landmark points directly with OpenCV
                # (mediapipe 1.x no longer ships solutions.drawing_utils).
                for conn in _HAND_CONNECTIONS:
                    pt1 = lmList[conn[0]]
                    pt2 = lmList[conn[1]]
                    cv2.line(img, pt1, pt2, (0, 255, 0), 2)

            allHands.append(myHand)

        if draw:
            for myHand in allHands:
                for i, (px, py) in enumerate(myHand["lmList"]):
                    cv2.circle(img, (px, py), 3, (255, 0, 0), cv2.FILLED)
                    cv2.putText(img, str(i), (px, py - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        return allHands, img

    def fingersUp(self, myHand):
        fingers = []
        lmList = myHand["lmList"]
        handType = myHand["type"]

        # Thumb: Distance-based detection with fallback angle
        thumb_tip = lmList[4]  # Tip (4)
        thumb_mcp = lmList[2]  # MCP (2)
        dx = thumb_tip[0] - thumb_mcp[0]  # X difference
        dy = thumb_tip[1] - thumb_mcp[1]  # Y difference
        distance = math.sqrt(dx**2 + dy**2)

        # Angle calculation as fallback
        thumb_ip = lmList[3]  # IP (3)
        x1, y1 = thumb_mcp
        x2, y2 = thumb_ip
        x3, y3 = thumb_tip
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        if angle < 0:
            angle += 360

        # Thumb up if distance is significant or angle indicates extension
        if handType == "Right":
            if dx < -30 or (45 < angle < 135 and distance > 30):  # Left extension or angle
                fingers.append(1)
            else:
                fingers.append(0)
        else:  # Left hand
            if dx > 30 or (45 < angle < 135 and distance > 30):  # Right extension or angle
                fingers.append(1)
            else:
                fingers.append(0)

        # Other fingers: Check if tip is above DIP joint
        dipIds = [5, 9, 13, 17]  # DIP joints for Index, Middle, Ring, Pinky
        for id in range(1, 5):  # Index, Middle, Ring, Pinky
            tip_y = lmList[self.tipIds[id]][1]
            dip_y = lmList[dipIds[id - 1]][1]
            if tip_y < dip_y - 20:  # Tip above DIP with threshold
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers