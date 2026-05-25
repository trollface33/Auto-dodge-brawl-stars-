"""
Module de détection des attaques pour Brawl Stars Auto Dodge
"""

import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class DodgeDetector:
    """Détecte les attaques entrantes et calcule les positions d'esquive"""
    
    def __init__(self, sensitivity=0.7, threshold=0.85):
        """
        Initialise le détecteur d'esquive
        
        Args:
            sensitivity: Niveau de sensibilité (0.0 à 1.0)
            threshold: Seuil de détection (0.0 à 1.0)
        """
        self.sensitivity = sensitivity
        self.threshold = threshold
        self.last_attack_position = None
        
    def detect_incoming_attack(self, frame):
        """
        Détecte si une attaque arrive
        
        Args:
            frame: Image capturée de l'écran (numpy array ou PIL Image)
            
        Returns:
            bool: True si une attaque est détectée
        """
        try:
            # Convertir en numpy array si nécessaire
            if isinstance(frame, Image.Image):
                frame = np.array(frame)
            
            # Convertir en BGR si nécessaire
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            # Détecter les projectiles (couleurs vives)
            attack_detected = self._detect_projectiles(frame)
            
            logger.debug(f"Attaque détectée: {attack_detected}")
            return attack_detected
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection: {e}")
            return False
    
    def _detect_projectiles(self, frame):
        """
        Détecte les projectiles basés sur les couleurs
        
        Args:
            frame: Image en BGR
            
        Returns:
            bool: True si des projectiles sont détectés
        """
        # Convertir en HSV pour meilleure détection des couleurs
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Définir les plages de couleurs pour les projectiles (rouge, jaune, etc.)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Détecter les jaunes/oranges
        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Combiner les masques
        mask_combined = cv2.bitwise_or(mask_red, mask_yellow)
        
        # Appliquer une dilatation pour améliorer la détection
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_dilated = cv2.dilate(mask_combined, kernel, iterations=2)
        
        # Compter les pixels détectés
        pixels_detected = cv2.countNonZero(mask_dilated)
        frame_area = frame.shape[0] * frame.shape[1]
        detection_ratio = pixels_detected / frame_area
        
        # Si suffisamment de pixels détectés, considérer comme attaque
        return detection_ratio > (0.01 * (1 - self.sensitivity))
    
    def calculate_dodge_position(self, frame, player_position):
        """
        Calcule la meilleure position pour esquiver
        
        Args:
            frame: Image de l'écran
            player_position: Position actuelle du joueur (x, y)
            
        Returns:
            tuple: Position d'esquive (x, y)
        """
        center_x = frame.shape[1] // 2
        center_y = frame.shape[0] // 2
        
        # Esquiver vers une position aléatoire proche
        dodge_range = 150
        dodge_x = player_position[0] + np.random.randint(-dodge_range, dodge_range)
        dodge_y = player_position[1] + np.random.randint(-dodge_range, dodge_range)
        
        # S'assurer que la position est dans les limites de l'écran
        dodge_x = max(50, min(dodge_x, frame.shape[1] - 50))
        dodge_y = max(50, min(dodge_y, frame.shape[0] - 50))
        
        return (dodge_x, dodge_y)
