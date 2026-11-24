"""Flask API for the maze solver. Also serves the HTML/CSS/JS frontend.

POST /api/generate  -> new maze
POST /api/solve     -> A* result plus every search step (for animation)
POST /api/compare   -> expanded nodes / cost / time for every heuristic
"""
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .astar import astar_steps, solve
from .heuristics import HEURISTICS
from .maze import Maze

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
MIN_DIM, MAX_DIM = 5, 101


class BadRequest(Exception):
    pass


def _int_in(data, key, lo, hi, default=None):
    v = data.get(key, default)
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise BadRequest(f"{key} must be an integer between {lo} and {hi}.")
    return v


def _cell(data, key, rows, cols):
    v = data.get(key)
    if (not isinstance(v, list) or len(v) != 2
            or not all(isinstance(x, int) and not isinstance(x, bool) for x in v)
            or not (0 <= v[0] < rows and 0 <= v[1] < cols)):
        raise BadRequest(f"{key} must be [row, col] inside the grid.")
    return v


def parse_maze(data) -> Maze:
    """Validate a JSON body of {grid, start, goal} and return a Maze."""
    if not isinstance(data, dict):
        raise BadRequest("Send a JSON object.")
    grid = data.get("grid")
    if (not isinstance(grid, list) or not MIN_DIM <= len(grid) <= MAX_DIM
            or not all(isinstance(r, list) and len(r) == len(grid[0]) for r in grid)
            or not MIN_DIM <= len(grid[0]) <= MAX_DIM
            or not all(v in (0, 1) and not isinstance(v, bool) for r in grid for v in r)):
        raise BadRequest(f"grid must be a rectangle of 0/1 values, {MIN_DIM}-{MAX_DIM} per side.")
    rows, cols = len(grid), len(grid[0])
    start, goal = _cell(data, "start", rows, cols), _cell(data, "goal", rows, cols)
    if grid[start[0]][start[1]] or grid[goal[0]][goal[1]]:
        raise BadRequest("start and goal must not be on a wall.")
    return Maze.from_grid(grid, start, goal)


def heuristic_of(data):
    name = data.get("heuristic", "Manhattan")
    if name not in HEURISTICS:
        raise BadRequest(f"heuristic must be one of: {', '.join(HEURISTICS)}.")
    return HEURISTICS[name]


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.errorhandler(BadRequest)
    def bad_request(e):
        return jsonify(error=str(e)), 400

    @app.get("/api/config")
    def config():
        return jsonify(heuristics=list(HEURISTICS), max_size=MAX_DIM)

    @app.post("/api/generate")
    def generate():
        data = request.get_json(silent=True) or {}
        rows = _int_in(data, "rows", MIN_DIM, MAX_DIM, 31) | 1
        cols = _int_in(data, "cols", MIN_DIM, MAX_DIM, 41) | 1
        seed = data.get("seed")
        if data.get("kind") == "obstacles":
            m = Maze.random_obstacles(rows, cols, seed=seed)
        else:
            m = Maze.generate(rows, cols, seed)
        return jsonify(rows=m.rows, cols=m.cols, grid=m.grid, start=m.start, goal=m.goal)

    @app.post("/api/solve")
    def solve_route():
        data = request.get_json(silent=True)
        maze, h = parse_maze(data), heuristic_of(data or {})
        steps = []
        result = solve(maze, h)  # timing and summary
        for s in astar_steps(maze, h):
            if not s.done:
                steps.append([s.current[0], s.current[1], [list(c) for c in s.opened]])
        return jsonify(found=result.found, cost=result.cost, expanded=result.expanded,
                       ms=round(result.seconds * 1000, 3), path=[list(c) for c in result.path],
                       steps=steps)

    @app.post("/api/compare")
    def compare():
        maze = parse_maze(request.get_json(silent=True))
        rows = []
        for name, h in HEURISTICS.items():
            r = solve(maze, h)
            rows.append(dict(heuristic=name, found=r.found, cost=r.cost,
                             expanded=r.expanded, ms=round(r.seconds * 1000, 3)))
        return jsonify(results=rows)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND, "index.html")

    @app.get("/<path:name>")
    def assets(name):
        return send_from_directory(FRONTEND, name)

    return app
