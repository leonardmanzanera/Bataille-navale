"""Modèle de données principal du jeu Bataille Navale."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, List, Sequence, Set, Tuple

CoordinateTuple = Tuple[int, int]


@dataclass(frozen=True)
class Coordinate:
    """Coordonnée d'une case de la grille (lignes et colonnes démarrent à zéro)."""

    row: int
    column: int

    def to_tuple(self) -> CoordinateTuple:
        """Retourne la coordonnée sous forme de tuple immuable."""

        return (self.row, self.column)


class Orientation(Enum):
    """Orientation d'un navire."""

    HORIZONTAL = auto()
    VERTICAL = auto()


class ShotResult(Enum):
    """Résultat d'un tir."""

    MISS = "manque"
    HIT = "touche"
    SUNK = "coule"

    def __str__(self) -> str:
        return self.value


@dataclass
class Ship:
    """Représentation d'un navire placé sur la grille."""

    name: str
    length: int
    cells: Tuple[Coordinate, ...]
    hits: Set[Coordinate] = field(default_factory=set)

    def register_hit(self, coord: Coordinate) -> None:
        """Enregistre un impact sur le navire."""

        if coord not in self.cells:
            raise ValueError("La coordonnée ne correspond pas au navire.")
        self.hits.add(coord)

    @property
    def is_sunk(self) -> bool:
        """Indique si le navire est coulé."""

        return len(self.hits) == len(self.cells)


@dataclass
class ShotOutcome:
    """Détail complet d'un tir."""

    coordinate: Coordinate
    result: ShotResult
    ship_name: str | None = None
    sunk_cells: Tuple[Coordinate, ...] = ()


@dataclass
class Grid:
    """Grille de jeu contenant les navires et l'historique des tirs."""

    size: int
    ships: List[Ship] = field(default_factory=list)
    _occupancy: Dict[Coordinate, Ship] = field(default_factory=dict, init=False)
    _shots: Dict[Coordinate, ShotResult] = field(default_factory=dict, init=False)

    def can_place_ship(self, cells: Sequence[Coordinate]) -> bool:
        """Vérifie que *cells* sont libres et dans la grille."""

        for coord in cells:
            if not self.contains(coord):
                return False
            if coord in self._occupancy:
                return False
        return True

    def place_ship(self, ship: Ship) -> None:
        """Place un navire sur la grille."""

        if not self.can_place_ship(ship.cells):
            raise ValueError("Placement invalide")
        self.ships.append(ship)
        for coord in ship.cells:
            self._occupancy[coord] = ship

    def contains(self, coord: Coordinate) -> bool:
        """Indique si la coordonnée appartient à la grille."""

        return 0 <= coord.row < self.size and 0 <= coord.column < self.size

    def receive_shot(self, coord: Coordinate) -> ShotOutcome:
        """Applique un tir sur la grille."""

        if not self.contains(coord):
            raise ValueError("Tir hors grille")
        if coord in self._shots:
            raise ValueError("Tir déjà effectué")
        ship = self._occupancy.get(coord)
        if ship is None:
            self._shots[coord] = ShotResult.MISS
            return ShotOutcome(coord, ShotResult.MISS)
        ship.register_hit(coord)
        result = ShotResult.SUNK if ship.is_sunk else ShotResult.HIT
        self._shots[coord] = result
        sunk_cells: Tuple[Coordinate, ...] = ship.cells if ship.is_sunk else ()
        return ShotOutcome(coord, result, ship.name, sunk_cells)

    def shot_result(self, coord: Coordinate) -> ShotResult | None:
        """Retourne le résultat déjà enregistré pour la coordonnée."""

        return self._shots.get(coord)

    def remaining_ships(self) -> List[Ship]:
        """Retourne les navires non coulés."""

        return [ship for ship in self.ships if not ship.is_sunk]

    def all_coordinates(self) -> Iterable[Coordinate]:
        """Itère sur toutes les coordonnées de la grille."""

        for row in range(self.size):
            for column in range(self.size):
                yield Coordinate(row, column)

    def to_public_matrix(self, reveal_ships: bool) -> List[List[str]]:
        """Construit une représentation textuelle de la grille."""

        matrix = [["~" for _ in range(self.size)] for _ in range(self.size)]
        for coord, result in self._shots.items():
            if result == ShotResult.MISS:
                matrix[coord.row][coord.column] = "·"
            elif result == ShotResult.HIT:
                matrix[coord.row][coord.column] = "×"
            elif result == ShotResult.SUNK:
                matrix[coord.row][coord.column] = "#"
        if reveal_ships:
            for ship in self.ships:
                for coord in ship.cells:
                    if matrix[coord.row][coord.column] == "~":
                        matrix[coord.row][coord.column] = "■"
        return matrix

    def occupied_cells(self) -> Set[Coordinate]:
        """Retourne l'ensemble des cellules contenant un navire."""

        return set(self._occupancy.keys())

    def shots(self) -> Dict[Coordinate, ShotResult]:
        """Retourne une copie de l'historique des tirs."""

        return dict(self._shots)


    def load_shot(self, outcome: ShotOutcome) -> None:
        """Injecte un tir préexistant (chargement)."""

        self._shots[outcome.coordinate] = outcome.result

