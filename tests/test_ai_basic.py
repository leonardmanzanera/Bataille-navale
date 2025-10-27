from __future__ import annotations

import random

from bataille_navale.ai import AIContext, BasicAI
from bataille_navale.model import Coordinate


def test_basic_ai_never_repeats() -> None:
    rng = random.Random(42)
    ai = BasicAI(rng)
    ai.reset(3, [])
    available = [Coordinate(r, c) for r in range(3) for c in range(3)]
    seen = set()
    for _ in range(9):
        coord = ai.next_shot(AIContext(tuple(available)))
        assert coord not in seen
        seen.add(coord)
