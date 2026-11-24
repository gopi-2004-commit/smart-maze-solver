"""Terminal front end: solve a maze and print it as ASCII art."""
from backend import HEURISTICS, Maze, solve


def render(maze: Maze, result) -> str:
    path = set(result.path)
    lines = []
    for r in range(maze.rows):
        row = []
        for c in range(maze.cols):
            cell = (r, c)
            if cell == maze.start:
                row.append("S")
            elif cell == maze.goal:
                row.append("G")
            elif maze.is_wall(cell):
                row.append("█")
            elif cell in path:
                row.append("●")
            elif cell in result.visited:
                row.append("·")
            else:
                row.append(" ")
        lines.append("".join(row))
    return "\n".join(lines)


def run(rows: int, cols: int, seed, heuristic: str, obstacles: bool) -> None:
    maze = Maze.random_obstacles(rows, cols, seed=seed) if obstacles else Maze.generate(rows, cols, seed)
    result = solve(maze, HEURISTICS[heuristic])
    print(render(maze, result))
    print(f"\nLegend: S start, G goal, ● shortest path, · explored, █ wall")
    print(f"{heuristic}: {'path cost ' + str(result.cost) if result.found else 'NO PATH'}, "
          f"{result.expanded} nodes expanded\n")
    print(f"{'Heuristic':<16}{'Cost':>6}{'Expanded':>10}{'Time (ms)':>11}")
    for name, h in HEURISTICS.items():
        r = solve(maze, h)
        print(f"{name:<16}{r.cost:>6}{r.expanded:>10}{r.seconds * 1000:>11.2f}")
