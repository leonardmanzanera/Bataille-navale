from __future__ import annotations

import random

from bataille_navale.ai import BasicAI
from bataille_navale.game import Game
from bataille_navale.stats import Stats, load_stats, save_stats


def test_stats_register_and_persistence(tmp_path) -> None:
    rng = random.Random(11)
    game = Game(grid_size=8, rng=rng, ai=BasicAI(rng), ai_level="basique")
    game.reset()
    target = next(iter(game.player_state.grid.all_coordinates()))
    game.player_fire(target)
    stats = Stats()
    stats.register_game("player", game)
    path = tmp_path / "stats.json"
    save_stats(stats, path)
    loaded = load_stats(path)
    assert loaded.games_played == 1
    assert loaded.wins == 1
    assert "basique" in loaded.by_ai_level
    assert loaded.shots_fired == game.stats.player_shots
