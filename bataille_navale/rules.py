"""Règles et utilitaires pour le placement et les coordonnées."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .model import Coordinate, Orientation, Ship

COORD_RE = re.compile(r"^\s*([A-Za-z])\s*(\d{1,2})\s*$")


@dataclass(frozen=True)
class ShipSpec:
    """Spécification d'un navire (nom et taille)."""

    name: str
    length: int


DEFAULT_FLEET: Sequence[ShipSpec] = (
    ShipSpec("Porte-avions", 5),
    ShipSpec("Cuirassé", 4),
    ShipSpec("Croiseur", 3),
    ShipSpec("Sous-marin", 3),
    ShipSpec("Destroyer", 2),
)


class CoordinateError(ValueError):
    """Erreur levée lors du parsing de coordonnées."""


def parse_coordinate(text: str, size: int) -> Coordinate:
    """Convertit une chaîne telle que ``B7`` en :class:`Coordinate`."""

    match = COORD_RE.match(text)
    if not match:
        raise CoordinateError("Format invalide")
    column_letter, row_text = match.groups()
    column = ord(column_letter.upper()) - ord("A")
    if not 0 <= column < size:
        raise CoordinateError("Colonne hors limites")
    row = int(row_text) - 1
    if not 0 <= row < size:
        raise CoordinateError("Ligne hors limites")
    return Coordinate(row=row, column=column)


def format_coordinate(coord: Coordinate) -> str:
    """Retourne la représentation textuelle d'une coordonnée."""

    return f"{chr(coord.column + ord('A'))}{coord.row + 1}"


def iter_all_coordinates(size: int) -> Iterable[Coordinate]:
    """Itère sur toutes les coordonnées d'une grille."""

    for row in range(size):
        for column in range(size):
            yield Coordinate(row, column)


def ship_cells(anchor: Coordinate, orientation: Orientation, length: int) -> List[Coordinate]:
    """Retourne la liste des cellules pour un navire."""

    cells: List[Coordinate] = []
    for offset in range(length):
        if orientation is Orientation.HORIZONTAL:
            cells.append(Coordinate(anchor.row, anchor.column + offset))
        else:
            cells.append(Coordinate(anchor.row + offset, anchor.column))
    return cells


def build_ship(spec: ShipSpec, anchor: Coordinate, orientation: Orientation) -> Ship:
    """Crée une instance de :class:`Ship` à partir d'une spécification."""

    return Ship(spec.name, spec.length, tuple(ship_cells(anchor, orientation, spec.length)))


def place_fleet_randomly(size: int, specs: Sequence[ShipSpec], rng: random.Random) -> List[Ship]:
    """Place aléatoirement les navires sans chevauchement."""

    from .model import Grid  # import tardif pour éviter les cycles

    grid = Grid(size=size)
    for spec in specs:
        placed = False
        while not placed:
            orientation = rng.choice([Orientation.HORIZONTAL, Orientation.VERTICAL])
            if orientation is Orientation.HORIZONTAL:
                row = rng.randrange(size)
                column = rng.randrange(size - spec.length + 1)
            else:
                row = rng.randrange(size - spec.length + 1)
                column = rng.randrange(size)
            candidate = build_ship(spec, Coordinate(row, column), orientation)
            if grid.can_place_ship(candidate.cells):
                grid.place_ship(candidate)
                placed = True
    return grid.ships
