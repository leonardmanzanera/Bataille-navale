from __future__ import annotations

import random

from bataille_navale.ai import AIContext, HunterAI
from bataille_navale.model import Coordinate, ShotOutcome, ShotResult


def test_hunter_ai_prioritises_neighbors() -> None:
    rng = random.Random(0)
    ai = HunterAI(rng)
    ai.reset(5, [])
    available = [Coordinate(r, c) for r in range(5) for c in range(5)]
    first = ai.next_shot(AIContext(tuple(available)))
    ai.register_result(ShotOutcome(first, ShotResult.MISS))
    hit = Coordinate(2, 2)
    ai.register_result(ShotOutcome(hit, ShotResult.HIT, "Test"))
    next_shot = ai.next_shot(AIContext(tuple(available)))
    assert next_shot in {
        Coordinate(1, 2),
        Coordinate(3, 2),
        Coordinate(2, 1),
        Coordinate(2, 3),
    }
    ai.register_result(ShotOutcome(next_shot, ShotResult.SUNK, "Test", (hit, next_shot)))
    assert not ai.targets
    following = ai.next_shot(AIContext(tuple(available)))
    assert following not in {hit, next_shot}
