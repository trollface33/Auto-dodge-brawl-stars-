"""
Module de détection des attaques pour Brawl Stars Auto Dodge.
"""

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class DodgeDetector:
    """Détecte les attaques entrantes et calcule les positions d'esquive."""

    def __init__(self, sensitivity=0.7, threshold=0.85):
        self.sensitivity = sensitivity
        self.threshold = threshold
        self.last_attack_position = None

    @staticmethod
    def _to_numpy(frame):
        """Convertit une image PIL ou NumPy en tableau compatible OpenCV BGR."""
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
            # Les captures ADB sont converties en RGB par le contrôleur.
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        raise ValueError(f"Nombre de canaux non supporté : {frame.shape[2]}")

    def detect_incoming_attack(self, frame):
        """Détecte si une attaque arrive."""
        try:
            frame = self._to_numpy(frame)
            attack_detected = self._detect_projectiles(frame)
            logger.debug(f"Attaque détectée : {attack_detected}")
            return attack_detected
        except Exception as e:
            logger.error(f"Erreur lors de la détection : {e}")
            return False

    def _detect_projectiles(self, frame):
        """Détecte les projectiles selon leurs couleurs."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        mask_combined = cv2.bitwise_or(mask_red, mask_yellow)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_dilated = cv2.dilate(mask_combined, kernel, iterations=2)

        pixels_detected = cv2.countNonZero(mask_dilated)
        frame_area = frame.shape[0] * frame.shape[1]
        detection_ratio = pixels_detected / frame_area

        return detection_ratio > (0.01 * (1 - self.sensitivity))

    def calculate_dodge_position(self, frame, player_position):
        """Calcule une position d'esquive dans les limites de l'écran."""
        frame = self._to_numpy(frame)
        height, width = frame.shape[:2]
        dodge_range = 150

        dodge_x = player_position[0] + np.random.randint(-dodge_range, dodge_range + 1)
        dodge_y = player_position[1] + np.random.randint(-dodge_range, dodge_range + 1)

        dodge_x = max(50, min(int(dodge_x), width - 50))
        dodge_y = max(50, min(int(dodge_y), height - 50))
        return (dodge_x, dodge_y)
