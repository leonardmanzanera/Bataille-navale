"""Gestion des statistiques persistantes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .game import Game
from .storage import ensure_app_support, stats_path


@dataclass
class Stats:
    """Structure de données des statistiques globales."""

    version: int = 1
    games_played: int = 0
    wins: int = 0
    shots_fired: int = 0
    hits: int = 0
    sunk_ships: int = 0
    by_ai_level: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def register_game(self, winner: str, game: Game) -> None:
        """Met à jour les stats suite à une partie."""

        self.games_played += 1
        if winner == "player":
            self.wins += 1
        self.shots_fired += game.stats.player_shots
        self.hits += game.stats.player_hits
        self.sunk_ships += sum(1 for ship in game.ai_state.grid.ships if ship.is_sunk)
        bucket = self.by_ai_level.setdefault(game.ai_level, {"played": 0, "wins": 0})
        bucket["played"] += 1
        if winner == "player":
            bucket["wins"] += 1

    def accuracy(self) -> float:
        """Retourne la précision globale."""

        return (self.hits / self.shots_fired * 100.0) if self.shots_fired else 0.0

    def to_dict(self) -> Dict[str, object]:
        """Transformation en dictionnaire sérialisable."""

        return {
            "version": self.version,
            "games_played": self.games_played,
            "wins": self.wins,
            "shots_fired": self.shots_fired,
            "hits": self.hits,
            "sunk_ships": self.sunk_ships,
            "by_ai_level": self.by_ai_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Stats":
        """Crée une instance depuis un dictionnaire."""

        stats = cls()
        stats.version = int(data.get("version", 1))
        stats.games_played = int(data.get("games_played", 0))
        stats.wins = int(data.get("wins", 0))
        stats.shots_fired = int(data.get("shots_fired", 0))
        stats.hits = int(data.get("hits", 0))
        stats.sunk_ships = int(data.get("sunk_ships", 0))
        stats.by_ai_level = {
            key: {"played": int(value.get("played", 0)), "wins": int(value.get("wins", 0))}
            for key, value in (data.get("by_ai_level", {}) or {}).items()  # type: ignore[assignment]
        }
        return stats


def load_stats(path: Path | None = None) -> Stats:
    """Charge les statistiques depuis le disque."""

    target = path or stats_path()
    if not target.exists():
        ensure_app_support()
        return Stats()
    data = json.loads(target.read_text())
    return Stats.from_dict(data)


def save_stats(stats: Stats, path: Path | None = None) -> Path:
    """Écrit les statistiques sur le disque."""

    target = path or stats_path()
    ensure_app_support()
    target.write_text(json.dumps(stats.to_dict(), indent=2, ensure_ascii=False))
    return target
