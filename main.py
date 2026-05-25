"""
Script principal pour Brawl Stars Auto Dodge
"""

import json
import logging
import argparse
import time
from dodge_detector import DodgeDetector
from dodge_controller import DodgeController

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file="config.json"):
    """Charge la configuration depuis un fichier JSON"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration chargée depuis {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"Fichier de configuration {config_file} non trouvé")
        return {}


def main():
    """Fonction principale"""
    
    # Argumenter la ligne de commande
    parser = argparse.ArgumentParser(description="Brawl Stars Auto Dodge")
    parser.add_argument("--device", type=str, help="ID du device ADB")
    parser.add_argument("--sensitivity", type=float, help="Sensibilité (0.0-1.0)")
    parser.add_argument("--config", type=str, default="config.json", help="Fichier de configuration")
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    # Mettre à jour avec les arguments ligne de commande
    if args.device:
        config["device_id"] = args.device
    if args.sensitivity:
        config["sensitivity"] = args.sensitivity
    
    # Initialiser le logging
    if config.get("enable_logging"):
        logging.getLogger().setLevel(getattr(logging, config.get("log_level", "INFO")))
    
    logger.info("=== Brawl Stars Auto Dodge ===")
    logger.info(f"Device: {config.get('device_id')}")
    logger.info(f"Sensibilité: {config.get('sensitivity')}")
    
    # Initialiser les modules
    detector = DodgeDetector(
        sensitivity=config.get("sensitivity", 0.7),
        threshold=config.get("attack_detection_threshold", 0.85)
    )
    
    controller = DodgeController(
        device_id=config.get("device_id", "emulator-5554"),
        dodge_delay_ms=config.get("dodge_delay_ms", 50)
    )
    
    # Connexion au device
    logger.info("Connexion au device...")
    if not controller.connect():
        logger.error("Impossible de se connecter au device")
        return
    
    logger.info("Connexion établie. Démarrage de la détection...")
    
    # Boucle principale
    try:
        frame_count = 0
        dodge_count = 0
        start_time = time.time()
        
        while True:
            # Capturer l'écran
            screenshot = controller.get_screenshot()
            if screenshot is None:
                logger.warning("Impossible de capturer l'écran")
                time.sleep(1)
                continue
            
            frame_count += 1
            
            # Déterminer la position du joueur (centre de l'écran pour simplifier)
            screen_width = screenshot.width
            screen_height = screenshot.height
            player_position = (screen_width // 2, screen_height // 2)
            controller.update_player_position(player_position[0], player_position[1])
            
            # Détecte une attaque
            if detector.detect_incoming_attack(screenshot):
                logger.info("Attaque détectée! Esquive en cours...")
                
                # Calculer la position d'esquive
                dodge_position = detector.calculate_dodge_position(screenshot, player_position)
                
                # Effectuer l'esquive
                if controller.dodge(player_position, dodge_position):
                    dodge_count += 1
                    logger.info(f"Esquive réussie! (Total: {dodge_count})")
            
            # Afficher les statistiques toutes les 100 frames
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                logger.info(f"Stats - FPS: {fps:.1f}, Esquives: {dodge_count}, Frames: {frame_count}")
            
            # Petit délai pour éviter une utilisation CPU excessive
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
    finally:
        # Déconnexion
        controller.disconnect()
        elapsed = time.time() - start_time
        logger.info(f"=== Session terminée ===")
        logger.info(f"Durée: {elapsed:.1f}s | Esquives: {dodge_count} | Frames: {frame_count}")


if __name__ == "__main__":
    main()
