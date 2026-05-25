"""
Module de contrôle des mouvements d'esquive pour Brawl Stars
"""

import logging
import time
from adb_shell.adb_device import AdbDeviceTcp
from PIL import Image
import io

logger = logging.getLogger(__name__)


class DodgeController:
    """Contrôle les mouvements d'esquive via ADB"""
    
    def __init__(self, device_id="emulator-5554", dodge_delay_ms=50):
        """
        Initialise le contrôleur d'esquive
        
        Args:
            device_id: ID du device ADB
            dodge_delay_ms: Délai avant esquive en millisecondes
        """
        self.device_id = device_id
        self.dodge_delay_ms = dodge_delay_ms / 1000.0  # Convertir en secondes
        self.device = None
        self.player_position = None
        self.is_connected = False
        
    def connect(self):
        """Établit la connexion avec le device ADB"""
        try:
            # Se connecter au device
            host, port = self.device_id.split(":")[-1], 5037
            self.device = AdbDeviceTcp(self.device_id)
            self.device.connect()
            self.is_connected = True
            logger.info(f"Connecté au device: {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion ADB: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion avec le device"""
        if self.device:
            try:
                self.device.close()
                self.is_connected = False
                logger.info("Déconnecté du device")
            except Exception as e:
                logger.error(f"Erreur de déconnexion: {e}")
    
    def get_screenshot(self):
        """
        Capture l'écran du device
        
        Returns:
            PIL.Image: Capture d'écran
        """
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return None
            
            # Utiliser screencap
            result = self.device.shell("screencap -p")
            image = Image.open(io.BytesIO(result))
            return image
        except Exception as e:
            logger.error(f"Erreur lors de la capture: {e}")
            return None
    
    def tap(self, x, y):
        """
        Effectue un tap à la position (x, y)
        
        Args:
            x: Coordonnée X
            y: Coordonnée Y
        """
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return False
            
            self.device.shell(f"input tap {x} {y}")
            logger.debug(f"Tap effectué à ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du tap: {e}")
            return False
    
    def swipe(self, start_x, start_y, end_x, end_y, duration_ms=500):
        """
        Effectue un swipe du point de départ au point d'arrivée
        
        Args:
            start_x: X initial
            start_y: Y initial
            end_x: X final
            end_y: Y final
            duration_ms: Durée du swipe en millisecondes
        """
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return False
            
            self.device.shell(f"input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}")
            logger.debug(f"Swipe effectué de ({start_x}, {start_y}) à ({end_x}, {end_y})")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du swipe: {e}")
            return False
    
    def dodge(self, current_position, dodge_position):
        """
        Effectue une esquive vers la position spécifiée
        
        Args:
            current_position: Position actuelle (x, y)
            dodge_position: Position d'esquive cible (x, y)
        """
        try:
            # Attendre le délai configuré
            time.sleep(self.dodge_delay_ms)
            
            # Effectuer un swipe rapide vers la position d'esquive
            self.swipe(
                current_position[0],
                current_position[1],
                dodge_position[0],
                dodge_position[1],
                duration_ms=200
            )
            
            logger.info(f"Esquive effectuée vers {dodge_position}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'esquive: {e}")
            return False
    
    def update_player_position(self, x, y):
        """
        Met à jour la position du joueur
        
        Args:
            x: Coordonnée X
            y: Coordonnée Y
        """
        self.player_position = (x, y)
        logger.debug(f"Position du joueur mise à jour: {self.player_position}")
    
    def get_player_position(self):
        """
        Récupère la position actuelle du joueur
        
        Returns:
            tuple: Position (x, y)
        """
        return self.player_position if self.player_position else (0, 0)
