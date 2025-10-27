"""Contrôleur de haut niveau pour orchestrer logique et vues."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .ai import BasicAI, HunterAI
from .game import Game, ShotOutcome
from .model import Coordinate, Orientation
from .rules import DEFAULT_FLEET, ShipSpec
from .stats import Stats, load_stats, save_stats
from .storage import load_game, save_game

LOGGER = logging.getLogger(__name__)


@dataclass
class Settings:
    """Paramètres configurables de la partie."""

    grid_size: int = 10
    fleet: Sequence[ShipSpec] = DEFAULT_FLEET
    ai_level: str = "basique"


class GameController:
    """Relie la logique du jeu aux interfaces utilisateur."""

    def __init__(self, settings: Settings | None = None, seed: int | None = None) -> None:
        self.settings = settings or Settings()
        self.rng = random.Random()
        if seed is not None:
            self.rng.seed(seed)
        self.stats: Stats = load_stats()
        self.manual_mode = True
        self.game: Game = self._create_game()
        self.game.randomize_ai()

    def _create_ai(self, level: str) -> BasicAI:
        if level == "chasseur":
            return HunterAI(self.rng)
        return BasicAI(self.rng)

    def _create_game(self) -> Game:
        ai = self._create_ai(self.settings.ai_level)
        return Game(
            grid_size=self.settings.grid_size,
            fleet=self.settings.fleet,
            rng=self.rng,
            ai=ai,
            ai_level=self.settings.ai_level,
        )

    def new_game(self, manual: bool = True) -> None:
        """Démarre une nouvelle partie."""

        self.manual_mode = manual
        self.game = self._create_game()
        if manual:
            self.game.begin_manual_placement()
            self.game.randomize_ai()
        else:
            self.game.reset()
        LOGGER.info("Nouvelle partie (manuel=%s)", manual)

    def auto_place_player(self) -> None:
        """Place automatiquement la flotte du joueur."""

        self.game.reset()
        self.manual_mode = False

    def place_ship(self, name: str, coord: Coordinate, orientation: Orientation) -> None:
        """Place un navire lors du placement manuel."""

        self.game.place_player_ship(name, coord, orientation)

    def player_ready(self) -> bool:
        """Indique si tous les navires sont placés."""

        return self.game.all_player_ships_placed()

    def player_shot(self, coord: Coordinate) -> tuple[ShotOutcome, str | None]:
        """Tir du joueur, retourne l'issue."""

        outcome = self.game.player_fire(coord)
        LOGGER.debug("Tir joueur %s -> %s", coord, outcome.result)
        winner = self.game.check_victory()
        if winner:
            self._finalize_game(winner)
        return outcome, winner

    def ai_shot(self) -> tuple[ShotOutcome, str | None]:
        """Laisse l'IA jouer son tour."""

        outcome = self.game.ai_fire()
        LOGGER.debug("Tir IA %s -> %s", outcome.coordinate, outcome.result)
        winner = self.game.check_victory()
        if winner:
            self._finalize_game(winner)
        return outcome, winner

    def _finalize_game(self, winner: str) -> None:
        LOGGER.info("Fin de partie : %s", winner)
        self.stats.register_game(winner, self.game)
        save_stats(self.stats)

    def save(self, path: Path | None = None) -> Path:
        """Sauvegarde la partie en cours."""

        saved_path = save_game(self.game, path)
        LOGGER.info("Sauvegarde effectuée : %s", saved_path)
        return saved_path

    def load(self, path: Path) -> None:
        """Charge une partie sauvegardée."""

        def factory(level: str) -> BasicAI:
            self.settings.ai_level = level
            return self._create_ai(level)

        loaded = load_game(path, factory)
        self.game = loaded
        self.settings.grid_size = loaded.grid_size
        self.settings.fleet = loaded.fleet
        self.rng = loaded.rng
        self.manual_mode = False
        LOGGER.info("Partie chargée depuis %s", path)

    def update_settings(
        self,
        grid_size: int,
        fleet: Sequence[ShipSpec],
        ai_level: str,
    ) -> None:
        """Met à jour les paramètres et prépare une nouvelle partie."""

        self.settings = Settings(grid_size=grid_size, fleet=fleet, ai_level=ai_level)
        self.new_game(manual=self.manual_mode)

    def remaining_player_ships(self) -> int:
        return len(self.game.player_state.grid.remaining_ships())

    def remaining_ai_ships(self) -> int:
        return len(self.game.ai_state.grid.remaining_ships())

    def available_ship_names(self) -> List[str]:
        placed = {ship.name for ship in self.game.player_state.grid.ships}
        return [spec.name for spec in self.settings.fleet if spec.name not in placed]

    def iter_player_ships(self) -> Iterable[str]:
        for ship in self.game.player_state.grid.ships:
            yield ship.name
