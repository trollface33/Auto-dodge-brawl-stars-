"""
Contrôle des mouvements via l'exécutable ADB officiel.

Cette version utilise adb.exe plutôt qu'une connexion libusb directe. Elle est
compatible avec un téléphone Android branché en USB sous Windows et avec WSL,
à condition que le chemin vers adb.exe soit accessible.
"""

import io
import logging
import os
import shutil
import subprocess
import time

from PIL import Image

logger = logging.getLogger(__name__)


class DodgeController:
    """Contrôle les mouvements d'esquive via adb.exe."""

    def __init__(self, device_id="", dodge_delay_ms=50):
        self.device_id = device_id
        self.dodge_delay_ms = dodge_delay_ms / 1000.0
        self.device = None
        self.player_position = None
        self.is_connected = False
        self.adb_path = self._find_adb()

    @staticmethod
    def _find_adb():
        """Trouve adb dans le PATH ou dans les emplacements Windows courants."""
        adb = shutil.which("adb")
        if adb:
            return adb

        candidates = [
            os.environ.get("ADB_PATH"),
            r"C:\platform-tools\adb.exe",
            r"C:\Android\platform-tools\adb.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

        return None

    def _run_adb(self, *args, capture_output=True):
        """Exécute adb avec le device sélectionné."""
        if not self.adb_path:
            raise FileNotFoundError(
                "adb.exe introuvable. Ajoute C:\\platform-tools au PATH "
                "ou définis la variable ADB_PATH."
            )

        command = [self.adb_path, "-s", self.device_id, *args]
        return subprocess.run(
            command,
            capture_output=capture_output,
            check=True,
        )

    def connect(self):
        """Vérifie la connexion au téléphone via adb.exe."""
        try:
            if not self.device_id:
                logger.error(
                    "Aucun device_id configuré. Utilise le numéro affiché par `adb devices`."
                )
                return False

            if not self.adb_path:
                logger.error(
                    "adb.exe est introuvable. Vérifie C:\\platform-tools ou le PATH."
                )
                return False

            result = self._run_adb("get-state")
            state = result.stdout.decode(errors="replace").strip()
            if state != "device":
                logger.error(f"État ADB inattendu pour {self.device_id}: {state or 'inconnu'}")
                return False

            self.is_connected = True
            logger.info(f"Connecté au device via ADB : {self.device_id}")
            return True
        except subprocess.CalledProcessError as e:
            error = e.stderr.decode(errors="replace").strip()
            logger.error(f"Erreur ADB : {error or e}")
            return False
        except Exception as e:
            logger.error(f"Erreur de connexion ADB : {e}")
            return False

    def disconnect(self):
        """Ferme la connexion logique au device."""
        self.is_connected = False
        self.device = None
        logger.info("Déconnecté du device")

    def get_screenshot(self):
        """Capture l'écran du device et retourne une image PIL."""
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return None

            result = self._run_adb("exec-out", "screencap", "-p")
            return Image.open(io.BytesIO(result.stdout)).convert("RGB")
        except Exception as e:
            logger.error(f"Erreur lors de la capture : {e}")
            return None

    def tap(self, x, y):
        """Effectue un tap à la position (x, y)."""
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return False
            self._run_adb("shell", "input", "tap", str(int(x)), str(int(y)))
            return True
        except Exception as e:
            logger.error(f"Erreur lors du tap : {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration_ms=500):
        """Effectue un swipe entre deux positions."""
        try:
            if not self.is_connected:
                logger.warning("Device non connecté")
                return False

            self._run_adb(
                "shell",
                "input",
                "swipe",
                str(int(start_x)),
                str(int(start_y)),
                str(int(end_x)),
                str(int(end_y)),
                str(int(duration_ms)),
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
        self.player_position = (x, y)
        logger.debug(f"Position du joueur mise à jour : {self.player_position}")

    def get_player_position(self):
        return self.player_position if self.player_position else (0, 0)
