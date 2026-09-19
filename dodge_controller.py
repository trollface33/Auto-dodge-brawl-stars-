"""
Module de contrôle des mouvements d'esquive pour Brawl Stars via ADB USB.
"""

import io
import logging
import time

from adb_shell.adb_device import AdbDeviceUsb
from PIL import Image

logger = logging.getLogger(__name__)


class DodgeController:
    """Contrôle les mouvements d'esquive via ADB USB."""

    def __init__(self, device_id="", dodge_delay_ms=50):
        """
        Initialise le contrôleur.

        Args:
            device_id: Numéro de série affiché par `adb devices`.
            dodge_delay_ms: Délai avant l'esquive, en millisecondes.
        """
        self.device_id = device_id
        self.dodge_delay_ms = dodge_delay_ms / 1000.0
        self.device = None
        self.player_position = None
        self.is_connected = False

    def connect(self):
        """Établit une connexion avec le téléphone Android en USB."""
        try:
            if not self.device_id:
                logger.error(
                    "Aucun device_id configuré. Utilise le numéro affiché par `adb devices`."
                )
                return False

            # Pour un téléphone branché en USB, il faut utiliser AdbDeviceUsb.
            # Ne pas utiliser AdbDeviceTcp, qui sert aux appareils accessibles en réseau.
            self.device = AdbDeviceUsb(serial=self.device_id)
            self.device.connect()
            self.is_connected = True
            logger.info(f"Connecté au device USB : {self.device_id}")
            return True
        except Exception as e:
            self.is_connected = False
            logger.error(f"Erreur de connexion ADB USB : {e}")
            logger.error(
                "Vérifie `adb devices`, le débogage USB et l'autorisation sur le téléphone."
            )
            return False

    def disconnect(self):
        """Ferme la connexion avec le device."""
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                logger.error(f"Erreur de déconnexion : {e}")
            finally:
                self.device = None
                self.is_connected = False
                logger.info("Déconnecté du device")

    def get_screenshot(self):
        """Capture l'écran du device et retourne une image PIL."""
        try:
            if not self.is_connected or self.device is None:
                logger.warning("Device non connecté")
                return None

            result = self.device.shell("screencap -p")
            if isinstance(result, str):
                result = result.encode()
            return Image.open(io.BytesIO(result)).convert("RGB")
        except Exception as e:
            logger.error(f"Erreur lors de la capture : {e}")
            return None

    def tap(self, x, y):
        """Effectue un tap à la position (x, y)."""
        try:
            if not self.is_connected or self.device is None:
                logger.warning("Device non connecté")
                return False

            self.device.shell(f"input tap {int(x)} {int(y)}")
            logger.debug(f"Tap effectué à ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du tap : {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration_ms=500):
        """Effectue un swipe entre deux positions."""
        try:
            if not self.is_connected or self.device is None:
                logger.warning("Device non connecté")
                return False

            command = (
                f"input swipe {int(start_x)} {int(start_y)} "
                f"{int(end_x)} {int(end_y)} {int(duration_ms)}"
            )
            self.device.shell(command)
            logger.debug(
                f"Swipe effectué de ({start_x}, {start_y}) "
                f"à ({end_x}, {end_y})"
            )
            return True
        except Exception as e:
            logger.error(f"Erreur lors du swipe : {e}")
            return False

    def dodge(self, current_position, dodge_position):
        """Effectue une esquive vers la position indiquée."""
        try:
            time.sleep(self.dodge_delay_ms)
            return self.swipe(
                current_position[0],
                current_position[1],
                dodge_position[0],
                dodge_position[1],
                duration_ms=200,
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'esquive : {e}")
            return False

    def update_player_position(self, x, y):
        """Met à jour la position du joueur."""
        self.player_position = (x, y)
        logger.debug(f"Position du joueur mise à jour : {self.player_position}")

    def get_player_position(self):
        """Retourne la position actuelle du joueur."""
        return self.player_position if self.player_position else (0, 0)
