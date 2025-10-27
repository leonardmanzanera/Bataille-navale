from __future__ import annotations

import pytest

from bataille_navale.model import Coordinate, Grid, Ship, ShotResult


def test_grid_prevents_overlap() -> None:
    grid = Grid(size=10)
    ship1 = Ship("Test", 3, (Coordinate(0, 0), Coordinate(0, 1), Coordinate(0, 2)))
    grid.place_ship(ship1)
    ship2 = Ship("Test2", 3, (Coordinate(0, 2), Coordinate(0, 3), Coordinate(0, 4)))
    with pytest.raises(ValueError):
        grid.place_ship(ship2)


def test_receive_shot_and_sinking() -> None:
    grid = Grid(size=5)
    ship = Ship("Patrol", 2, (Coordinate(1, 1), Coordinate(1, 2)))
    grid.place_ship(ship)
    outcome1 = grid.receive_shot(Coordinate(1, 1))
    assert outcome1.result is ShotResult.HIT
    outcome2 = grid.receive_shot(Coordinate(1, 2))
    assert outcome2.result is ShotResult.SUNK
    assert ship.is_sunk
    with pytest.raises(ValueError):
        grid.receive_shot(Coordinate(1, 1))
