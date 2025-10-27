from __future__ import annotations

import random

from bataille_navale.ai import BasicAI
from bataille_navale.game import Game
from bataille_navale.storage import load_game, save_game


def test_save_and_load_roundtrip(tmp_path) -> None:
    rng = random.Random(9)
    ai = BasicAI(rng)
    game = Game(grid_size=8, rng=rng, ai=ai, ai_level="basique")
    game.reset()
    first_coord = next(iter(game.player_state.grid.all_coordinates()))
    game.player_fire(first_coord)
    path = tmp_path / "sample.bn-save.json"
    save_game(game, path)
    loaded = load_game(path, lambda level: BasicAI(random.Random(9)))
    assert loaded.grid_size == game.grid_size
    assert loaded.ai_level == game.ai_level
    assert loaded.player_state.shots_count == game.player_state.shots_count
