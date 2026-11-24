"""Maze represented as a 2D grid: 0 = open cell, 1 = wall."""
from __future__ import annotations

import random

Cell = tuple[int, int]  # (row, col)
OPEN, WALL = 0, 1
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))  # up, down, left, right


class Maze:
    def __init__(self, rows: int, cols: int):
        self.rows, self.cols = rows, cols
        self.grid = [[OPEN] * cols for _ in range(rows)]
        self.start: Cell = (0, 0)
        self.goal: Cell = (rows - 1, cols - 1)

    # ---- queries -------------------------------------------------------
    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.rows and 0 <= cell[1] < self.cols

    def is_wall(self, cell: Cell) -> bool:
        return self.grid[cell[0]][cell[1]] == WALL

    def neighbors(self, cell: Cell):
        """Open 4-connected neighbours of a cell."""
        r, c = cell
        for dr, dc in DIRECTIONS:
            nb = (r + dr, c + dc)
            if self.in_bounds(nb) and not self.is_wall(nb):
                yield nb

    # ---- editing -------------------------------------------------------
    def set_wall(self, cell: Cell, wall: bool) -> None:
        self.grid[cell[0]][cell[1]] = WALL if wall else OPEN

    def clear_walls(self) -> None:
        self.grid = [[OPEN] * self.cols for _ in range(self.rows)]

    # ---- generators ----------------------------------------------------
    @classmethod
    def generate(cls, rows: int, cols: int, seed: int | None = None, loops: float = 0.10) -> "Maze":
        """Perfect maze via randomized depth-first search, then knock out a
        fraction of inner walls so several routes exist and the *shortest* one
        actually matters. Dimensions are forced to odd numbers."""
        rows, cols = rows | 1, cols | 1
        rng = random.Random(seed)
        m = cls(rows, cols)
        m.grid = [[WALL] * cols for _ in range(rows)]
        m.start, m.goal = (1, 1), (rows - 2, cols - 2)

        stack = [m.start]
        m.grid[1][1] = OPEN
        while stack:
            r, c = stack[-1]
            options = [(r + dr * 2, c + dc * 2, dr, dc) for dr, dc in DIRECTIONS
                       if 0 < r + dr * 2 < rows - 1 and 0 < c + dc * 2 < cols - 1
                       and m.grid[r + dr * 2][c + dc * 2] == WALL]
            if not options:
                stack.pop()
                continue
            nr, nc, dr, dc = rng.choice(options)
            m.grid[r + dr][c + dc] = OPEN
            m.grid[nr][nc] = OPEN
            stack.append((nr, nc))

        # add loops: remove walls that sit between two open cells
        candidates = [(r, c) for r in range(1, rows - 1) for c in range(1, cols - 1)
                      if m.grid[r][c] == WALL and
                      ((m.grid[r - 1][c] == OPEN and m.grid[r + 1][c] == OPEN) or
                       (m.grid[r][c - 1] == OPEN and m.grid[r][c + 1] == OPEN))]
        rng.shuffle(candidates)
        for r, c in candidates[: int(len(candidates) * loops)]:
            m.grid[r][c] = OPEN
        return m

    @classmethod
    def random_obstacles(cls, rows: int, cols: int, density: float = 0.28, seed: int | None = None) -> "Maze":
        """Open field scattered with random obstacles (may be unsolvable)."""
        rng = random.Random(seed)
        m = cls(rows, cols)
        for r in range(rows):
            for c in range(cols):
                if rng.random() < density:
                    m.grid[r][c] = WALL
        m.grid[m.start[0]][m.start[1]] = OPEN
        m.grid[m.goal[0]][m.goal[1]] = OPEN
        return m

    @classmethod
    def from_grid(cls, grid, start, goal) -> "Maze":
        """Build a Maze from plain lists (e.g. parsed JSON)."""
        m = cls(len(grid), len(grid[0]))
        m.grid = [list(row) for row in grid]
        m.start, m.goal = tuple(start), tuple(goal)
        return m
