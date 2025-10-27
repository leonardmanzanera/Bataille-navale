"""Logique centrale du jeu Bataille Navale."""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Set

from .ai import AIBase, AIContext, BasicAI
from .model import Coordinate, Grid, Orientation, Ship, ShotOutcome, ShotResult
from .rules import DEFAULT_FLEET, ShipSpec, build_ship, place_fleet_randomly


@dataclass
class PlayerState:
    """État d'un joueur (humain ou IA)."""

    grid: Grid
    shots: Dict[Coordinate, ShotOutcome] = field(default_factory=dict)

    def register_shot(self, outcome: ShotOutcome) -> None:
        """Enregistre un tir effectué par le joueur."""

        self.shots[outcome.coordinate] = outcome

    @property
    def shots_count(self) -> int:
        return len(self.shots)

    @property
    def hits_count(self) -> int:
        return sum(1 for outcome in self.shots.values() if outcome.result is not ShotResult.MISS)

    @property
    def accuracy(self) -> float:
        return (self.hits_count / self.shots_count * 100.0) if self.shots_count else 0.0


@dataclass
class GameStats:
    """Statistiques collectées pour une partie."""

    player_shots: int = 0
    player_hits: int = 0
    ai_shots: int = 0
    ai_hits: int = 0


class Game:
    """Gère l'enchaînement d'une partie entre le joueur et l'IA."""

    def __init__(
        self,
        grid_size: int = 10,
        fleet: Sequence[ShipSpec] | None = None,
        rng: random.Random | None = None,
        ai: AIBase | None = None,
        ai_level: str = "basique",
    ) -> None:
        self.grid_size = grid_size
        self.fleet = list(fleet or DEFAULT_FLEET)
        self.rng = rng or random.Random()
        self.ai = ai or BasicAI(self.rng)
        self.ai_level = ai_level
        self.ai.reset(grid_size, self.fleet)
        self.player_state = PlayerState(Grid(grid_size))
        self.ai_state = PlayerState(Grid(grid_size))
        self.turn: str = "player"
        self.stats = GameStats()
        self.specs_by_name: Dict[str, ShipSpec] = {spec.name: spec for spec in self.fleet}

    def reset(self) -> None:
        """Relance une partie avec placements aléatoires."""

        self.player_state = PlayerState(Grid(self.grid_size))
        self.ai_state = PlayerState(Grid(self.grid_size))
        self._auto_place_player()
        self._auto_place_ai()
        self.turn = "player"
        self.stats = GameStats()
        self.ai.reset(self.grid_size, self.fleet)

    def _auto_place_player(self) -> None:
        ships = place_fleet_randomly(self.grid_size, self.fleet, self.rng)
        for ship in ships:
            self.player_state.grid.place_ship(ship)

    def _auto_place_ai(self) -> None:
        ships = place_fleet_randomly(self.grid_size, self.fleet, self.rng)
        for ship in ships:
            self.ai_state.grid.place_ship(ship)

    def begin_manual_placement(self) -> None:
        """Vide la grille joueur pour un placement manuel."""

        self.player_state = PlayerState(Grid(self.grid_size))

    def place_player_ship(self, name: str, anchor: Coordinate, orientation: Orientation) -> None:
        """Place un navire du joueur manuellement."""

        spec = self.specs_by_name.get(name)
        if spec is None:
            raise ValueError("Navire inconnu")
        if any(ship.name == name for ship in self.player_state.grid.ships):
            raise ValueError("Navire déjà placé")
        ship = build_ship(spec, anchor, orientation)
        self.player_state.grid.place_ship(ship)

    def randomize_ai(self) -> None:
        """Replace la flotte de l'IA."""

        self.ai_state = PlayerState(Grid(self.grid_size))
        self._auto_place_ai()
        self.ai.reset(self.grid_size, self.fleet)

    def all_player_ships_placed(self) -> bool:
        return len(self.player_state.grid.ships) == len(self.fleet)

    def player_fire(self, coord: Coordinate) -> ShotOutcome:
        """Effectue un tir du joueur sur la grille de l'IA."""

        if coord in self.player_state.shots:
            raise ValueError("Tir déjà effectué")
        outcome = self.ai_state.grid.receive_shot(coord)
        self.player_state.register_shot(outcome)
        self.stats.player_shots = self.player_state.shots_count
        self.stats.player_hits = self.player_state.hits_count
        self.turn = "ai"
        return outcome

    def ai_fire(self) -> ShotOutcome:
        """Effectue un tir de l'IA sur la grille du joueur."""

        context = AIContext(
            tuple(
                coord
                for coord in self.player_state.grid.all_coordinates()
                if coord not in self.ai_state.shots
            )
        )
        target = self.ai.next_shot(context)
        outcome = self.player_state.grid.receive_shot(target)
        self.ai_state.register_shot(outcome)
        self.ai.register_result(outcome)
        self.stats.ai_shots = self.ai_state.shots_count
        self.stats.ai_hits = self.ai_state.hits_count
        self.turn = "player"
        return outcome

    def check_victory(self) -> Optional[str]:
        """Détermine si un joueur a gagné."""

        if not self.ai_state.grid.remaining_ships():
            return "player"
        if not self.player_state.grid.remaining_ships():
            return "ai"
        return None

    def serialize(self) -> Dict[str, object]:
        """Export JSON compatible avec :mod:`storage`."""

        from .rules import format_coordinate

        def ships_payload(state: PlayerState) -> List[Dict[str, object]]:
            payload: List[Dict[str, object]] = []
            for ship in state.grid.ships:
                payload.append(
                    {
                        "name": ship.name,
                        "cells": [format_coordinate(cell) for cell in ship.cells],
                        "hits": [format_coordinate(hit) for hit in ship.hits],
                    }
                )
            return payload

        def shots_payload(state: PlayerState) -> List[str]:
            return [format_coordinate(coord) for coord in state.shots]

        return {
            "version": 1,
            "grid_size": self.grid_size,
            "fleet": [asdict(spec) for spec in self.fleet],
            "player": {
                "ships": ships_payload(self.player_state),
                "shots": shots_payload(self.player_state),
            },
            "ai": {
                "ships": ships_payload(self.ai_state),
                "shots": shots_payload(self.ai_state),
            },
            "turn": self.turn,
            "ai_level": self.ai_level,
            "rng_state": repr(self.rng.getstate()),
        }

    @classmethod
    def from_serialized(
        cls,
        payload: Dict[str, object],
        ai: AIBase,
    ) -> "Game":
        """Reconstruit une partie à partir d'une sauvegarde."""

        from .rules import parse_coordinate

        grid_size = int(payload["grid_size"])
        fleet = [ShipSpec(**spec) for spec in payload["fleet"]]  # type: ignore[arg-type]
        game = cls(grid_size=grid_size, fleet=fleet, ai=ai, ai_level=str(payload["ai_level"]))
        rng_state_text = payload.get("rng_state", "")
        if rng_state_text:
            try:
                state = eval(rng_state_text, {"__builtins__": {}})  # noqa: S307
                game.rng.setstate(state)
            except Exception:
                pass
        game.player_state = PlayerState(Grid(grid_size))
        game.ai_state = PlayerState(Grid(grid_size))
        ship_hits: Dict[str, Set[Coordinate]] = {}
        for side_key, state in (("player", game.player_state), ("ai", game.ai_state)):
            side_payload = payload[side_key]  # type: ignore[index]
            ship_hits.clear()
            for ship_info in side_payload["ships"]:  # type: ignore[index]
                cells = [parse_coordinate(cell, grid_size) for cell in ship_info["cells"]]  # type: ignore[index]
                spec = ShipSpec(str(ship_info["name"]), len(cells))
                ship = Ship(spec.name, spec.length, tuple(cells))
                hits = {parse_coordinate(hit, grid_size) for hit in ship_info["hits"]}  # type: ignore[index]
                ship_hits[ship.name] = hits.copy()
                state.grid.place_ship(ship)
            for shot_label in side_payload["shots"]:  # type: ignore[index]
                coord = parse_coordinate(shot_label, grid_size)
                ship = next((s for s in state.grid.ships if coord in s.cells), None)
                if ship and coord in ship_hits.get(ship.name, set()):
                    ship.hits.add(coord)
                    remaining_hits = ship_hits[ship.name]
                    remaining_hits.discard(coord)
                    result = ShotResult.SUNK if len(ship.hits) == ship.length and not remaining_hits else ShotResult.HIT
                    sunk_cells = tuple(ship.cells) if result is ShotResult.SUNK else ()
                    outcome = ShotOutcome(coord, result, ship.name, sunk_cells)
                else:
                    result = ShotResult.MISS
                    outcome = ShotOutcome(coord, result)
                state.grid.load_shot(outcome)
                state.register_shot(outcome)
        game.turn = str(payload.get("turn", "player"))
        game.ai.load_memory(game.ai_state.shots.keys())
        game.stats.player_shots = game.player_state.shots_count
        game.stats.player_hits = game.player_state.hits_count
        game.stats.ai_shots = game.ai_state.shots_count
        game.stats.ai_hits = game.ai_state.hits_count
        return game
