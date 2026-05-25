# Brawl Stars Auto Dodge

Un script Python automatisé pour esquiver les attaques dans Brawl Stars sur mobile.

## Fonctionnalités

- ✅ Détection automatique des attaques entrantes
- ✅ Esquive intelligente en temps réel
- ✅ Support pour plusieurs appareils via ADB
- ✅ Configuration personnalisable
- ✅ Logging et monitoring

## Prérequis

- Python 3.8+
- Android SDK (ADB)
- Un appareil Android ou émulateur avec Brawl Stars installé

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

## Structure du Projet

```
Auto-dodge-brawl-stars-/
├── main.py
├── dodge_detector.py
├── dodge_controller.py
├── config.json
├── requirements.txt
└── README.md
```

## Avertissement

Ce script est à usage éducatif uniquement. Utilisation à vos risques et périls.