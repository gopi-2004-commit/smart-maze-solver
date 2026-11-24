# Smart Maze Solver (A* Search)

An AI maze solver that finds the **shortest path** through a 2D grid with obstacles, using **A\*** and the **Manhattan distance** heuristic. A Python backend does the searching; an HTML/CSS/JavaScript frontend lets you watch it work.

## Project layout
```
smart-maze-solver/
├── main.py                # entry point (web app, or --cli)
├── requirements.txt       # flask
├── backend/               # Python: the "AI" and the API
│   ├── maze.py            # Maze as a 2D grid (0 = open, 1 = wall), generators
│   ├── heuristics.py      # Manhattan, Euclidean, Chebyshev, zero (Dijkstra)
│   ├── astar.py           # A* as a step-by-step generator + solve()
│   ├── server.py          # Flask API + serves the frontend
│   └── cli.py             # terminal version
├── frontend/              # browser UI
│   ├── index.html
│   ├── style.css
│   └── app.js             # canvas drawing, editing, animation, API calls
└── tests/                 # unit tests (A* cost equals BFS shortest path, API checks)
```

## Run it
Requires Python 3.9+.
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                     # opens http://127.0.0.1:5000
python main.py --cli --seed 7      # terminal version instead
python -m unittest                 # run the tests
```
Useful options: `--port 8000`, `--no-browser`. Always open the page through the Flask address, not by double-clicking `index.html`.

## Using the web app
- **Start search** animates A* exploring the maze; press again to pause or resume (Space also works).
- **New maze**, **Random obstacles** (may have no path), **Clear walls**, **Reset**.
- **Draw walls** by dragging on the grid; **right-click or drag a wall** to erase. **Drag the orange start or red goal** to move them. Editing resets the search.
- Pick a **heuristic** and **grid size**, and change the **speed**.
- **Compare heuristics** shows cost, nodes expanded and time for each; the best (fewest nodes) is highlighted.

Colours: orange = start, red = goal, teal = frontier (open set), purple = explored (closed set), yellow = shortest path.

## How it works
1. The browser sends the grid, start, goal and heuristic to `POST /api/solve`.
2. The backend runs A\*, which expands the cell with the lowest `f = g + h` (`g` = cost so far, `h` = heuristic estimate to the goal).
3. It returns the shortest path plus every expansion step, and the browser replays the steps as an animation.

**Manhattan distance** (`|Δrow| + |Δcol|`) never overestimates on a 4-way grid, so the path found is guaranteed shortest, and it steers the search toward the goal. Dijkstra (`h = 0`) finds the same path but explores far more cells.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/config` | Available heuristics |
| POST | `/api/generate` | `{kind: "maze"\|"obstacles", rows, cols, seed?}` → new maze |
| POST | `/api/solve` | `{grid, start, goal, heuristic}` → path, cost, steps |
| POST | `/api/compare` | `{grid, start, goal}` → results per heuristic |

Invalid input returns HTTP 400 with `{"error": "..."}`.

## Ideas to extend
8-way movement, weighted terrain, bidirectional search, saving and loading mazes.
