"""Fonctions utilitaires communes."""

from __future__ import annotations

import argparse
import logging
import random
from typing import Iterable, List

from .model import Coordinate
from .rules import format_coordinate


def configure_logging(level: str) -> None:
    """Configure le logging global."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="[%(levelname)s] %(message)s",
    )


def create_rng(seed: int | None) -> random.Random:
    """Retourne un générateur pseudo-aléatoire éventuellement déterministe."""

    rng = random.Random()
    if seed is not None:
        rng.seed(seed)
    return rng


def matrix_to_ascii(matrix: List[List[str]], header: bool = True) -> str:
    """Transforme une matrice de symboles en tableau ASCII."""

    if not matrix:
        return ""
    size = len(matrix)
    lines: List[str] = []
    if header:
        letters = " ".join(chr(ord("A") + idx) for idx in range(size))
        lines.append(f"   {letters}")
    for idx, row in enumerate(matrix, start=1):
        row_text = " ".join(row)
        lines.append(f"{idx:>2} {row_text}")
    return "\n".join(lines)


def coordinates_to_labels(coords: Iterable[Coordinate]) -> List[str]:
    """Convertit une séquence de coordonnées en labels lisibles."""

    return [format_coordinate(coord) for coord in coords]


class CLIArgumentParser(argparse.ArgumentParser):
    """Analyseur personnalisé empêchant la sortie du processus."""

    def error(self, message: str) -> None:  # type: ignore[override]
        raise ValueError(message)
