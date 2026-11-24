"""Smart Maze Solver – entry point.

    python main.py              # start the web app at http://127.0.0.1:5000
    python main.py --cli        # terminal mode
"""
import argparse
import threading
import webbrowser

from backend import HEURISTICS


def main():
    p = argparse.ArgumentParser(description="Maze solver using A* search")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    p.add_argument("--cli", action="store_true", help="run in the terminal instead")
    p.add_argument("--rows", type=int, default=31, help="CLI maze rows (made odd)")
    p.add_argument("--cols", type=int, default=41, help="CLI maze columns (made odd)")
    p.add_argument("--seed", type=int, default=None, help="CLI random seed")
    p.add_argument("--heuristic", choices=list(HEURISTICS), default="Manhattan", help="CLI heuristic")
    p.add_argument("--obstacles", action="store_true", help="CLI: random obstacles instead of a maze")
    a = p.parse_args()

    if a.cli:
        from backend.cli import run
        run(a.rows | 1, a.cols | 1, a.seed, a.heuristic, a.obstacles)
        return

    from backend.server import create_app
    url = f"http://{a.host}:{a.port}"
    if not a.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Maze solver running at {url}  (Ctrl+C to stop)")
    create_app().run(host=a.host, port=a.port)


if __name__ == "__main__":
    main()
