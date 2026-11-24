"""A* search on a Maze.

f(n) = g(n) + h(n)
  g(n): cost of the cheapest known path from start to n (each move costs 1)
  h(n): heuristic estimate of the cost from n to the goal
"""
from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Callable, Iterator, Optional

from .heuristics import manhattan
from .maze import Cell, Maze

Heuristic = Callable[[Cell, Cell], float]


@dataclass
class Step:
    """One iteration of A*: the node just expanded and the neighbours it
    added to (or improved in) the open set. The last step has done=True."""
    current: Cell
    opened: list[Cell]
    done: bool = False
    path: Optional[list[Cell]] = None


@dataclass
class SearchResult:
    found: bool
    path: list[Cell]
    cost: int
    expanded: int
    visited: set[Cell] = field(default_factory=set)
    seconds: float = 0.0


def _reconstruct(parent: dict[Cell, Cell], cell: Cell) -> list[Cell]:
    path = [cell]
    while cell in parent:
        cell = parent[cell]
        path.append(cell)
    return path[::-1]


def astar_steps(maze: Maze, heuristic: Heuristic = manhattan) -> Iterator[Step]:
    """Run A* one expansion at a time (generator), so a UI can animate it."""
    start, goal = maze.start, maze.goal
    g: dict[Cell, float] = {start: 0}
    parent: dict[Cell, Cell] = {}
    closed: set[Cell] = set()
    tie = itertools.count()  # keeps heap ordering stable
    h0 = heuristic(start, goal)
    heap = [(h0, h0, next(tie), start)]  # (f, h, tie, cell): ties prefer smaller h

    while heap:
        _, _, _, current = heapq.heappop(heap)
        if current in closed:
            continue  # stale heap entry
        closed.add(current)

        if current == goal:
            yield Step(current, [], True, _reconstruct(parent, current))
            return

        opened = []
        for nb in maze.neighbors(current):
            new_g = g[current] + 1
            if nb not in closed and new_g < g.get(nb, float("inf")):
                g[nb] = new_g
                parent[nb] = current
                h = heuristic(nb, goal)
                heapq.heappush(heap, (new_g + h, h, next(tie), nb))
                opened.append(nb)
        yield Step(current, opened)

    yield Step(start, [], True, None)  # open set exhausted: no path


def solve(maze: Maze, heuristic: Heuristic = manhattan) -> SearchResult:
    """Run A* to completion and summarise the result."""
    t0 = time.perf_counter()
    expanded, visited, path = 0, set(), None
    for step in astar_steps(maze, heuristic):
        if not step.done or step.path is not None:
            expanded += 1
            visited.add(step.current)
        if step.done:
            path = step.path
    return SearchResult(
        found=path is not None,
        path=path or [],
        cost=len(path) - 1 if path else -1,
        expanded=expanded,
        visited=visited,
        seconds=time.perf_counter() - t0,
    )
