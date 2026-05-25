# Brawl Stars Auto Dodge

Un script Python automatisé pour esquiver les attaques dans Brawl Stars sur mobile via Termux.

## Fonctionnalités

- ✅ Détection automatique des attaques entrantes
- ✅ Esquive intelligente en temps réel
- ✅ Support pour appareils Android via ADB
- ✅ Configuration personnalisable
- ✅ Logging et monitoring
- ✅ Compatible avec Termux

## Prérequis

- Python 3.8+
- Android SDK (ADB)
- Un appareil Android avec Brawl Stars installé
- Termux (optionnel, pour exécution sur appareil)

## Installation

```bash
git clone https://github.com/trollface33/Auto-dodge-brawl-stars-.git
cd Auto-dodge-brawl-stars-
pip install -r requirements.txt
```

## Configuration

1. Modifiez `config.json` avec vos paramètres
2. Connectez votre appareil via ADB
3. Lancez le script

```bash
python main.py
```

## Usage

```bash
python main.py --device <device_id> --sensitivity <level>
```

### Arguments disponibles

- `--device`: ID du device ADB (par défaut: emulator-5554)
- `--sensitivity`: Niveau de sensibilité 0.0-1.0 (par défaut: 0.7)
- `--config`: Chemin du fichier de config (par défaut: config.json)

## Structure du Projet

```
Auto-dodge-brawl-stars-/
├── main.py              # Script principal
├── dodge_detector.py    # Détecteur d'attaques par CV
├── dodge_controller.py  # Contrôleur d'esquive via ADB
├── config.json          # Configuration
├── requirements.txt     # Dépendances Python
├── README.md            # Ce fichier
└── .gitignore
```

## Configuration (config.json)

```json
{
  "device_id": "emulator-5554",
  "sensitivity": 0.7,
  "dodge_delay_ms": 50,
  "screen_width": 1080,
  "screen_height": 2340,
  "detection_method": "image_recognition",
  "log_level": "INFO",
  "enable_logging": true,
  "dodge_range": 150,
  "attack_detection_threshold": 0.85
}
```

### Paramètres

- **device_id**: ID du device Android
- **sensitivity**: Sensibilité de détection (0.0-1.0)
- **dodge_delay_ms**: Délai avant esquive (ms)
- **screen_width/height**: Dimensions de l'écran
- **dodge_range**: Distance max d'esquive (pixels)
- **attack_detection_threshold**: Seuil de confiance

## Sur Termux

```bash
pkg install python3 android-tools
pip install -r requirements.txt
python main.py
```

## Avertissement ⚠️

Ce script est à usage éducatif uniquement. Utilisation à vos risques et périls.

## Licence

MIT
