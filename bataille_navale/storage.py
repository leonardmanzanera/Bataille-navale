"""Gestion des sauvegardes et du stockage applicatif."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .ai import AIBase
from .game import Game

APP_DIR = Path.home() / "Library" / "Application Support" / "BatailleNavale"
SAVE_SUFFIX = ".bn-save.json"
STATS_FILE = "stats.json"


def ensure_app_support() -> Path:
    """Crée le dossier d'application si nécessaire."""

    APP_DIR.mkdir(parents=True, exist_ok=True)
    return APP_DIR


def default_save_path() -> Path:
    """Chemin par défaut pour la sauvegarde."""

    return ensure_app_support() / f"last{SAVE_SUFFIX}"


def save_game(game: Game, path: Path | None = None) -> Path:
    """Enregistre l'état courant de la partie."""

    target = path or default_save_path()
    data = game.serialize()
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return target


def load_game(path: Path, ai_factory: Callable[[str], AIBase]) -> Game:
    """Charge une partie à partir d'un fichier JSON."""

    data = json.loads(path.read_text())
    ai = ai_factory(str(data.get('ai_level', 'basique')))
    return Game.from_serialized(data, ai)


def stats_path() -> Path:
    """Retourne le chemin du fichier de statistiques."""

    return ensure_app_support() / STATS_FILE
