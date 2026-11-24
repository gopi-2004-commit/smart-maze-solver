"""Heuristic functions h(cell, goal) for A* on a 4-connected grid.

A heuristic is *admissible* if it never overestimates the true remaining cost.
Admissible heuristics guarantee that A* returns a shortest path.
"""
import math

Cell = tuple[int, int]


def manhattan(a: Cell, b: Cell) -> float:
    """|dx| + |dy|. Exact on an empty 4-connected grid, so it is the tightest
    admissible choice here and expands the fewest nodes."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Cell, b: Cell) -> float:
    """Straight-line distance. Admissible but weaker than Manhattan."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def chebyshev(a: Cell, b: Cell) -> float:
    """max(|dx|, |dy|). Admissible but even weaker (meant for 8-way movement)."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def zero(a: Cell, b: Cell) -> float:
    """h = 0 turns A* into Dijkstra's algorithm (no guidance at all)."""
    return 0.0


HEURISTICS = {
    "Manhattan": manhattan,
    "Euclidean": euclidean,
    "Chebyshev": chebyshev,
    "Dijkstra (h=0)": zero,
}
