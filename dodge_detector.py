"""
Module de détection des attaques pour Brawl Stars Auto Dodge.

La détection est volontairement conservatrice : une couleur rouge/jaune seule
ne suffit pas. Il faut une forme suffisamment grande, située dans la zone de jeu
et proche du joueur. Un délai entre deux détections empêche les esquives en boucle.
"""

import logging
import time

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class DodgeDetector:
    """Détecte des menaces colorées proches du joueur."""

    def __init__(
        self,
        sensitivity=0.7,
        threshold=0.85,
        dodge_range=150,
        min_contour_area=80,
        cooldown_seconds=0.8,
    ):
        self.sensitivity = max(0.0, min(1.0, float(sensitivity)))
        self.threshold = max(0.0, min(1.0, float(threshold)))
        self.dodge_range = int(dodge_range)
        self.min_contour_area = int(min_contour_area)
        self.cooldown_seconds = float(cooldown_seconds)
        self.last_attack_position = None
        self.last_detection_time = 0.0

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

    def detect_incoming_attack(self, frame, player_position=None):
        """Retourne True seulement si une menace crédible est proche du joueur."""
        try:
            now = time.monotonic()
            if now - self.last_detection_time < self.cooldown_seconds:
                return False

            image = self._to_numpy(frame)
            height, width = image.shape[:2]
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Ignore les bords de l'écran, où se trouvent souvent les éléments HUD.
            x0, x1 = int(width * 0.08), int(width * 0.92)
            y0, y1 = int(height * 0.12), int(height * 0.90)
            roi = hsv[y0:y1, x0:x1]

            red1 = cv2.inRange(roi, np.array([0, 130, 110]), np.array([10, 255, 255]))
            red2 = cv2.inRange(roi, np.array([170, 130, 110]), np.array([180, 255, 255]))
            yellow = cv2.inRange(roi, np.array([15, 140, 120]), np.array([35, 255, 255]))
            mask = cv2.bitwise_or(cv2.bitwise_or(red1, red2), yellow)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.dilate(mask, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            player_x, player_y = player_position or (width // 2, height // 2)
            best = None

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < self.min_contour_area:
                    continue
                bx, by, bw, bh = cv2.boundingRect(contour)
                if bw < 6 or bh < 6:
                    continue
                moments = cv2.moments(contour)
                if moments["m00"] == 0:
                    continue
                cx = int(moments["m10"] / moments["m00"]) + x0
                cy = int(moments["m01"] / moments["m00"]) + y0
                distance = float(np.hypot(cx - player_x, cy - player_y))
                max_distance = max(width, height) * 0.42
                if distance > max_distance:
                    continue

                # Les grandes formes proches sont plus crédibles qu'une petite
                # tache de couleur. La sensibilité ne supprime jamais les filtres.
                score = min(1.0, area / 1200.0) * (1.0 - distance / max_distance)
                if best is None or score > best[0]:
                    best = (score, cx, cy)

            required_score = max(0.10, self.threshold * 0.25)
            if best is None or best[0] < required_score:
                return False

            self.last_attack_position = (best[1], best[2])
            self.last_detection_time = now
            logger.info(
                "Menace crédible détectée en (%d, %d), score=%.2f",
                best[1], best[2], best[0],
            )
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la détection : {e}")
            return False

    def calculate_dodge_position(self, frame, player_position):
        """Calcule une esquive opposée à la menace, sans position aléatoire."""
        image = self._to_numpy(frame)
        height, width = image.shape[:2]
        player_x, player_y = player_position
        attack = self.last_attack_position

        if attack is None:
            return (int(player_x), int(player_y))

        dx = player_x - attack[0]
        dy = player_y - attack[1]
        length = max(1.0, float(np.hypot(dx, dy)))
        dodge_x = player_x + (dx / length) * self.dodge_range
        dodge_y = player_y + (dy / length) * self.dodge_range

        dodge_x = max(50, min(int(round(dodge_x)), width - 50))
        dodge_y = max(50, min(int(round(dodge_y)), height - 50))
        return (dodge_x, dodge_y)
