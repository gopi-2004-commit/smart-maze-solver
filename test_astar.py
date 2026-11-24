import unittest
from collections import deque

from backend import HEURISTICS, Maze, manhattan, solve


def bfs_cost(maze):
    q, seen = deque([(maze.start, 0)]), {maze.start}
    while q:
        cell, d = q.popleft()
        if cell == maze.goal:
            return d
        for nb in maze.neighbors(cell):
            if nb not in seen:
                seen.add(nb)
                q.append((nb, d + 1))
    return -1


class AStarTests(unittest.TestCase):
    def test_matches_bfs_on_many_mazes(self):
        for seed in range(25):
            for maze in (Maze.generate(21, 21, seed), Maze.random_obstacles(15, 15, 0.3, seed)):
                expected = bfs_cost(maze)
                for name, h in HEURISTICS.items():
                    with self.subTest(seed=seed, heuristic=name):
                        self.assertEqual(solve(maze, h).cost, expected)

    def test_path_is_valid(self):
        maze = Maze.generate(25, 25, 3)
        r = solve(maze)
        self.assertEqual(r.path[0], maze.start)
        self.assertEqual(r.path[-1], maze.goal)
        for a, b in zip(r.path, r.path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)
            self.assertFalse(maze.is_wall(b))

    def test_no_path_when_goal_walled_in(self):
        maze = Maze(7, 7)
        for cell in ((5, 6), (6, 5)):
            maze.set_wall(cell, True)
        r = solve(maze)
        self.assertFalse(r.found)
        self.assertEqual(r.path, [])

    def test_start_equals_goal(self):
        maze = Maze(5, 5)
        maze.goal = maze.start
        r = solve(maze)
        self.assertTrue(r.found)
        self.assertEqual(r.cost, 0)

    def test_manhattan_beats_dijkstra(self):
        maze = Maze(30, 30)  # open field
        self.assertLess(solve(maze, manhattan).expanded, solve(maze, HEURISTICS["Dijkstra (h=0)"]).expanded)

    def test_generated_maze_is_solvable(self):
        for seed in range(20):
            self.assertTrue(solve(Maze.generate(31, 41, seed)).found)


if __name__ == "__main__":
    unittest.main()
