"""Implémentations de l'IA pour Bataille Navale."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, List, Sequence, Set

from .model import Coordinate, ShotOutcome, ShotResult
from .rules import ShipSpec


@dataclass
class AIContext:
    """Informations minimales pour piloter l'IA."""

    available: Sequence[Coordinate]


class AIBase:
    """Interface d'une IA de tir."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.grid_size: int = 10
        self._shots: Set[Coordinate] = set()

    def reset(self, grid_size: int, fleet: Sequence[ShipSpec]) -> None:  # noqa: ARG002
        """Réinitialise l'IA pour une nouvelle partie."""

        self.grid_size = grid_size
        self._shots.clear()

    def next_shot(self, context: AIContext) -> Coordinate:
        """Retourne la prochaine coordonnée à viser."""

        raise NotImplementedError

    def register_result(self, outcome: ShotOutcome) -> None:
        """Informe l'IA du résultat de son tir précédent."""

        self._shots.add(outcome.coordinate)


    def load_memory(self, shots: Iterable[Coordinate]) -> None:
        """Recharge l'historique des tirs."""

        self._shots = set(shots)

    def remaining_targets(self, context: AIContext) -> List[Coordinate]:
        """Filtre les coordonnées disponibles non encore utilisées."""

        return [coord for coord in context.available if coord not in self._shots]


class BasicAI(AIBase):
    """IA basique : tir aléatoire sans répétition."""

    def next_shot(self, context: AIContext) -> Coordinate:  # noqa: D401
        options = self.remaining_targets(context)
        if not options:
            raise RuntimeError("Plus de coups disponibles")
        choice = self.rng.choice(options)
        self._shots.add(choice)
        return choice

    def register_result(self, outcome: ShotOutcome) -> None:  # noqa: D401
        super().register_result(outcome)


class HunterAI(BasicAI):
    """IA chasseur qui poursuit les navires touchés."""

    def __init__(self, rng: random.Random | None = None) -> None:
        super().__init__(rng)
        self.targets: Deque[Coordinate] = deque()
        self.hit_streak: List[Coordinate] = []

    def reset(self, grid_size: int, fleet: Sequence[ShipSpec]) -> None:  # noqa: D401
        super().reset(grid_size, fleet)
        self.targets.clear()
        self.hit_streak.clear()

    def _neighbors(self, coord: Coordinate) -> List[Coordinate]:
        candidates = [
            Coordinate(coord.row - 1, coord.column),
            Coordinate(coord.row + 1, coord.column),
            Coordinate(coord.row, coord.column - 1),
            Coordinate(coord.row, coord.column + 1),
        ]
        valid: List[Coordinate] = []
        for candidate in candidates:
            if 0 <= candidate.row < self.grid_size and 0 <= candidate.column < self.grid_size:
                valid.append(candidate)
        return valid

    def next_shot(self, context: AIContext) -> Coordinate:  # noqa: D401
        available = self.remaining_targets(context)
        filtered_targets = [coord for coord in self.targets if coord in available]
        self.targets = deque(filtered_targets)
        if self.targets:
            choice = self.targets.popleft()
            self._shots.add(choice)
            return choice
        return super().next_shot(AIContext(available))

    def register_result(self, outcome: ShotOutcome) -> None:  # noqa: D401
        super().register_result(outcome)
        if outcome.result is ShotResult.MISS:
            return
        if outcome.result is ShotResult.SUNK:
            self.hit_streak.clear()
            self.targets.clear()
            return
        self.hit_streak.append(outcome.coordinate)
        for neighbor in self._neighbors(outcome.coordinate):
            if neighbor in self._shots or neighbor in self.targets:
                continue
            self.targets.append(neighbor)
