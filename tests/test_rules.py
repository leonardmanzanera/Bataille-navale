from __future__ import annotations

import random

import pytest

from bataille_navale.model import Coordinate
from bataille_navale.rules import DEFAULT_FLEET, CoordinateError, parse_coordinate, place_fleet_randomly


def test_parse_coordinate_valid() -> None:
    coord = parse_coordinate("B7", 10)
    assert coord == Coordinate(row=6, column=1)


def test_parse_coordinate_invalid_letter() -> None:
    with pytest.raises(CoordinateError):
        parse_coordinate("Z1", 10)


def test_random_placement_no_overlap() -> None:
    rng = random.Random(123)
    ships = place_fleet_randomly(10, DEFAULT_FLEET, rng)
    occupied = set()
    for ship in ships:
        for cell in ship.cells:
            assert cell not in occupied
            occupied.add(cell)
