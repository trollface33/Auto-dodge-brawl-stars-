"""
Script principal pour Brawl Stars Auto Dodge.
"""

import argparse
import json
import logging
import time

from dodge_controller import DodgeController
from dodge_detector import DodgeDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_file="config.json"):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Configuration chargée depuis {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Configuration invalide ({config_file}) : {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Brawl Stars Auto Dodge")
    parser.add_argument("--device", type=str, help="ID du device ADB")
    parser.add_argument("--sensitivity", type=float, help="Sensibilité (0.0-1.0)")
    parser.add_argument("--config", default="config.json", help="Fichier de configuration")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.device:
        config["device_id"] = args.device
    if args.sensitivity is not None:
        config["sensitivity"] = args.sensitivity

    if config.get("enable_logging"):
        logging.getLogger().setLevel(getattr(logging, config.get("log_level", "INFO"), logging.INFO))

    detector = DodgeDetector(
        sensitivity=config.get("sensitivity", 0.7),
        threshold=config.get("attack_detection_threshold", 0.85),
        dodge_range=config.get("dodge_range", 150),
        min_contour_area=config.get("min_contour_area", 80),
        cooldown_seconds=config.get("detection_cooldown_seconds", 0.8),
    )
    controller = DodgeController(
        device_id=config.get("device_id", ""),
        dodge_delay_ms=config.get("dodge_delay_ms", 50),
    )

    logger.info("=== Brawl Stars Auto Dodge ===")
    logger.info(f"Device: {config.get('device_id')}")
    logger.info(f"Sensibilité: {config.get('sensitivity')}")

    if not controller.connect():
        logger.error("Impossible de se connecter au device")
        return

    logger.info("Connexion établie. Démarrage de la détection...")
    frame_count = 0
    dodge_count = 0
    start_time = time.time()

    try:
        while True:
            screenshot = controller.get_screenshot()
            if screenshot is None:
                time.sleep(1)
                continue

            frame_count += 1
            player_position = (screenshot.width // 2, screenshot.height // 2)
            controller.update_player_position(*player_position)

            if detector.detect_incoming_attack(screenshot, player_position):
                dodge_position = detector.calculate_dodge_position(screenshot, player_position)
                logger.info(f"Esquive contrôlée vers {dodge_position}")
                if controller.dodge(player_position, dodge_position):
                    dodge_count += 1

            if frame_count % 100 == 0:
                elapsed = max(0.001, time.time() - start_time)
                logger.info(
                    f"Stats - FPS: {frame_count / elapsed:.1f}, "
                    f"Esquives: {dodge_count}, Frames: {frame_count}"
                )
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
    finally:
        controller.disconnect()
        logger.info(
            f"=== Session terminée === Durée: {time.time() - start_time:.1f}s | "
            f"Esquives: {dodge_count} | Frames: {frame_count}"
        )


if __name__ == "__main__":
    main()
