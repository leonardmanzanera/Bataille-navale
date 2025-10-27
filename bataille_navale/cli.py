"""Interface en ligne de commande pour Bataille Navale."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from .ai import BasicAI, HunterAI
from .game import Game
from .i18n_fr import tr
from .rules import DEFAULT_FLEET, CoordinateError, format_coordinate, parse_coordinate
from .stats import load_stats, save_stats
from .utils import configure_logging, create_rng, matrix_to_ascii

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m bataille_navale.cli")
    parser.add_argument("--seed", type=int, default=None, help="Graine aléatoire")
    parser.add_argument("--log-level", default="INFO", help="Niveau de logs")
    parser.add_argument("--ai-level", choices=["basique", "chasseur"], default="basique")
    parser.add_argument("--grid-size", type=int, default=10, choices=range(8, 13))
    return parser


def create_ai(level: str, rng) -> BasicAI:
    if level == "chasseur":
        return HunterAI(rng)
    return BasicAI(rng)


def render_grids(game: Game) -> str:
    player_matrix = game.player_state.grid.to_public_matrix(True)
    ai_matrix = game.ai_state.grid.to_public_matrix(False)
    lines = [tr("console_player_grid"), matrix_to_ascii(player_matrix)]
    lines.append("")
    lines.extend([tr("console_target_grid"), matrix_to_ascii(ai_matrix)])
    return "\n".join(lines)


def outcome_message(outcome) -> str:
    if outcome.result.name == "MISS":
        return tr("console_miss")
    if outcome.result.name == "HIT":
        return tr("console_hit")
    return tr("console_sunk", ship=outcome.ship_name or "")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    rng = create_rng(args.seed)
    game = Game(
        grid_size=args.grid_size,
        fleet=DEFAULT_FLEET,
        rng=rng,
        ai=create_ai(args.ai_level, rng),
        ai_level=args.ai_level,
    )
    game.reset()
    stats = load_stats()
    print(tr("console_welcome"))
    print(tr("console_instructions"))
    while True:
        print()
        print(render_grids(game))
        try:
            user_input = input(tr("console_player_turn")).strip()
        except EOFError:
            print()
            break
        if user_input.lower() in {"quit", "exit"}:
            print(tr("console_quit"))
            break
        try:
            coord = parse_coordinate(user_input, game.grid_size)
            outcome = game.player_fire(coord)
            print(outcome_message(outcome))
        except CoordinateError as exc:
            print(tr("console_invalid_input", detail=str(exc)))
            continue
        except ValueError as exc:
            print(tr("console_invalid_input", detail=str(exc)))
            continue
        winner = game.check_victory()
        if winner:
            break
        ai_outcome = game.ai_fire()
        result_text = outcome_message(ai_outcome)
        print(tr("console_ai_turn", coord=format_coordinate(ai_outcome.coordinate), result=result_text))
        winner = game.check_victory()
        if winner:
            break
    winner = game.check_victory()
    if winner == "player":
        print(tr("console_victory"))
    elif winner == "ai":
        print(tr("console_defeat"))
    if winner in {"player", "ai"}:
        stats.register_game(winner, game)
    save_stats(stats)
    summary = tr(
        "console_summary",
        shots=game.stats.player_shots,
        hits=game.stats.player_hits,
        accuracy=game.player_state.accuracy,
    )
    print(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
