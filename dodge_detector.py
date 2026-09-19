"""
Détection conservatrice des projectiles en mouvement vers le joueur.
"""

import logging
import time

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class DodgeDetector:
    """Détecte les menaces mobiles et choisit une esquive opposée."""

    def __init__(
        self,
        sensitivity=0.7,
        threshold=0.85,
        dodge_range=280,
        min_contour_area=50,
        cooldown_seconds=0.35,
        min_motion_pixels=3,
        max_tracking_jump=220,
    ):
        self.sensitivity = max(0.0, min(1.0, float(sensitivity)))
        self.threshold = max(0.0, min(1.0, float(threshold)))
        self.dodge_range = int(dodge_range)
        self.min_contour_area = int(min_contour_area)
        self.cooldown_seconds = float(cooldown_seconds)
        self.min_motion_pixels = float(min_motion_pixels)
        self.max_tracking_jump = float(max_tracking_jump)
        self.last_attack_position = None
        self.last_detection_time = 0.0
        self.previous_candidates = []

    @staticmethod
    def _to_numpy(frame):
        if isinstance(frame, Image.Image):
            frame = np.array(frame)
        if not isinstance(frame, np.ndarray):
            raise TypeError(f"Type d'image non supporté : {type(frame).__name__}")
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if frame.ndim != 3:
            raise ValueError(f"Dimensions d'image invalides : {frame.shape}")
        if frame.shape[2] == 4:
            return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        if frame.shape[2] == 3:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        raise ValueError(f"Nombre de canaux non supporté : {frame.shape[2]}")

    def _find_candidates(self, image, player_position):
        height, width = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        x0, x1 = int(width * 0.08), int(width * 0.92)
        y0, y1 = int(height * 0.10), int(height * 0.92)
        roi = hsv[y0:y1, x0:x1]

        red1 = cv2.inRange(roi, np.array([0, 130, 110]), np.array([10, 255, 255]))
        red2 = cv2.inRange(roi, np.array([170, 130, 110]), np.array([180, 255, 255]))
        yellow = cv2.inRange(roi, np.array([15, 140, 120]), np.array([35, 255, 255]))
        mask = cv2.bitwise_or(cv2.bitwise_or(red1, red2), yellow)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        player_x, player_y = player_position
        candidates = []
        max_distance = max(width, height) * 0.48
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_contour_area:
                continue
            _, _, bw, bh = cv2.boundingRect(contour)
            if bw < 5 or bh < 5:
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                continue
            cx = int(moments["m10"] / moments["m00"]) + x0
            cy = int(moments["m01"] / moments["m00"]) + y0
            distance = float(np.hypot(cx - player_x, cy - player_y))
            if distance <= max_distance:
                candidates.append({"position": (cx, cy), "distance": distance, "area": area})
        return candidates

    def detect_incoming_attack(self, frame, player_position=None):
        """Détecte uniquement une forme colorée qui se rapproche entre deux images."""
        try:
            now = time.monotonic()
            image = self._to_numpy(frame)
            height, width = image.shape[:2]
            player = player_position or (width // 2, height // 2)
            candidates = self._find_candidates(image, player)

            best = None
            for current in candidates:
                cx, cy = current["position"]
                nearest = None
                nearest_distance = self.max_tracking_jump
                for previous in self.previous_candidates:
                    px, py = previous["position"]
                    jump = float(np.hypot(cx - px, cy - py))
                    if jump < nearest_distance:
                        nearest = previous
                        nearest_distance = jump

                # Sans position précédente, impossible de distinguer un décor
                # fixe d'un projectile : on attend l'image suivante.
                if nearest is None:
                    continue

                motion_x = cx - nearest["position"][0]
                motion_y = cy - nearest["position"][1]
                motion = float(np.hypot(motion_x, motion_y))
                approaching = nearest["distance"] - current["distance"]
                if motion < self.min_motion_pixels or approaching < self.min_motion_pixels:
                    continue

                # Le vecteur de mouvement doit pointer globalement vers le joueur.
                to_player = np.array([player[0] - cx, player[1] - cy], dtype=float)
                movement = np.array([motion_x, motion_y], dtype=float)
                alignment = float(np.dot(movement, to_player)) / max(
                    1.0, np.linalg.norm(movement) * np.linalg.norm(to_player)
                )
                if alignment < 0.35:
                    continue

                score = min(1.0, current["area"] / 900.0) * min(1.0, approaching / 20.0)
                if best is None or score > best[0]:
                    best = (score, cx, cy)

            self.previous_candidates = candidates
            if now - self.last_detection_time < self.cooldown_seconds:
                return False

            required_score = max(0.05, self.threshold * 0.12)
            if best is None or best[0] < required_score:
                return False

            self.last_attack_position = (best[1], best[2])
            self.last_detection_time = now
            logger.info(
                "Projectile en mouvement vers le joueur en (%d, %d), score=%.2f",
                best[1], best[2], best[0],
            )
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la détection : {e}")
            return False

    def calculate_dodge_position(self, frame, player_position):
        """Esquive latéralement à l'opposé de la provenance du projectile."""
        image = self._to_numpy(frame)
        height, width = image.shape[:2]
        player_x, player_y = player_position
        attack = self.last_attack_position
        if attack is None:
            return (int(player_x), int(player_y))

        dx = player_x - attack[0]
        dy = player_y - attack[1]
        if abs(dx) >= abs(dy):
            # Projectile à droite => dx négatif => déplacement à gauche.
            dodge_x = player_x + (self.dodge_range if dx > 0 else -self.dodge_range)
            dodge_y = player_y
        else:
            dodge_x = player_x
            dodge_y = player_y + (self.dodge_range if dy > 0 else -self.dodge_range)

        dodge_x = max(50, min(int(dodge_x), width - 50))
        dodge_y = max(50, min(int(dodge_y), height - 50))
        return (dodge_x, dodge_y)
