"""文件迷宫：在目录树里收集文件，避开 Bug，走到出口。"""

from __future__ import annotations

import random
from collections import deque

from canvas import (
    AMBER, BG, BLUE, BLUE2, DIM, FAINT, GREEN, INK, PANEL, PANEL2,
    PINK, RED, WHITE, Canvas,
)
from village import Outcome

FILES = (
    ("T", "notes.txt", (110, 220, 255)),
    ("P", "photo.png", (255, 170, 110)),
    ("S", "run.sh", (112, 232, 164)),
    ("M", "track.mp3", (214, 160, 255)),
)
DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))


class MazeGame:
    LIVES = 3
    TIME = 75.0

    def __init__(self, w: int, h: int, seed: int | None = None) -> None:
        self.w = w
        self.h = h
        self.rng = random.Random(seed)
        self.status = "playing"
        self.cols = 33 if w < 96 else 41
        self.rows = 17 if h < 28 else 21
        self.grid = self._make_maze()
        self.start = (1, 1)
        self.player = list(self.start)
        self.visited = {self.start}
        self.exit = self._farthest(self.start)
        self.files = {}
        self._place_files()
        self.bugs = self._place_bugs()
        self.collected: set[tuple[int, int]] = set()
        self.lives = self.LIVES
        self.elapsed = 0.0
        self.steps = 0
        self.deaths = 0
        self.invuln = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.bug_timer = 0.0
        self.popups: list[list] = []
        self.score = 0

    # ---------- 生成 ----------

    def _make_maze(self) -> list[list[str]]:
        cols, rows = self.cols, self.rows
        g = [["#"] * cols for _ in range(rows)]
        g[1][1] = " "
        stack = [(1, 1)]
        while stack:
            x, y = stack[-1]
            nxt = []
            for dx, dy in DIRS:
                nx, ny = x + dx * 2, y + dy * 2
                if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and g[ny][nx] == "#":
                    nxt.append((nx, ny, dx, dy))
            if nxt:
                nx, ny, dx, dy = self.rng.choice(nxt)
                g[y + dy][x + dx] = " "
                g[ny][nx] = " "
                stack.append((nx, ny))
            else:
                stack.pop()
        # 打掉一些墙，形成环路，迷宫不至于太死
        for y in range(2, rows - 2):
            for x in range(2, cols - 2):
                if g[y][x] != "#":
                    continue
                ns = [(g[y + dy][x + dx] == " ") for dx, dy in DIRS]
                if (ns[0] and ns[2] and not ns[1] and not ns[3]) or (
                    ns[1] and ns[3] and not ns[0] and not ns[2]
                ):
                    if self.rng.random() < 0.16:
                        g[y][x] = " "
        return g

    def _floor(self) -> list[tuple[int, int]]:
        return [(x, y) for y in range(1, self.rows - 1)
                for x in range(1, self.cols - 1) if self.grid[y][x] == " "]

    def _distances(self, start: tuple[int, int]) -> dict[tuple[int, int], int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in dist and 0 <= nx < self.cols and 0 <= ny < self.rows \
                        and self.grid[ny][nx] == " ":
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        return dist

    def _farthest(self, start: tuple[int, int]) -> tuple[int, int]:
        dist = self._distances(start)
        return max(dist, key=dist.get)

    def _place_files(self) -> None:
        dist = self._distances(self.start)
        floors = [p for p in dist if p != self.exit and p != self.start]
        if not floors:
            return
        # 按距离分层后抽样，保证四个文件一定不重复。
        floors.sort(key=lambda p: dist[p])
        bucket = max(1, len(floors) // len(FILES))
        picks: list[tuple[int, int]] = []
        for i, (letter, name, color) in enumerate(FILES):
            lo = min(len(floors) - 1, i * bucket)
            hi = min(len(floors), (i + 1) * bucket)
            pool = [p for p in floors[lo:hi] if p not in picks] or [p for p in floors if p not in picks]
            if not pool:
                break
            cell = self.rng.choice(pool)
            picks.append(cell)
            self.files[cell] = (letter, name, color)

    def _place_bugs(self) -> list[dict]:
        dist = self._distances(self.start)
        candidates = [p for p in dist if dist[p] > 8 and p not in self.files and p != self.exit]
        self.rng.shuffle(candidates)
        bugs = []
        for cell in candidates[:2 if self.cols < 40 else 3]:
            bugs.append({"x": cell[0], "y": cell[1], "dir": self.rng.randrange(4), "timer": 0.0})
        return bugs

    # ---------- 更新 ----------

    @property
    def remaining(self) -> float:
        return max(0.0, self.TIME - self.elapsed)

    @property
    def collected_count(self) -> int:
        return len(self.collected)

    def handle_key(self, key: str) -> None:
        if self.status != "playing":
            return
        deltas = {
            "up": (0, -1), "w": (0, -1), "W": (0, -1),
            "down": (0, 1), "s": (0, 1), "S": (0, 1),
            "left": (-1, 0), "a": (-1, 0), "A": (-1, 0),
            "right": (1, 0), "d": (1, 0), "D": (1, 0),
        }
        if key not in deltas:
            return
        dx, dy = deltas[key]
        self._move(dx, dy)

    def _move(self, dx: int, dy: int) -> None:
        x, y = self.player
        nx, ny = x + dx, y + dy
        if not (0 <= nx < self.cols and 0 <= ny < self.rows) or self.grid[ny][nx] != " ":
            return
        self.player = [nx, ny]
        self.steps += 1
        self.visited.add((nx, ny))
        cell = (nx, ny)
        if cell in self.files and cell not in self.collected:
            self.collected.add(cell)
            self.score += 150
            _, name, color = self.files[cell]
            self._popup(nx, ny, f"+150 {name}", color)
        if cell == self.exit:
            if self.collected_count >= len(FILES):
                self.status = "won"
                self._popup(nx, ny, "回到新手村！", GREEN)
            else:
                self._popup(nx, ny, f"还差 {len(FILES) - self.collected_count} 个文件", AMBER)
        if self.status == "playing":
            self._check_bugs()

    def _check_bugs(self) -> None:
        if self.invuln > 0:
            return
        for bug in self.bugs:
            if (bug["x"], bug["y"]) == tuple(self.player):
                self._hit()
                return

    def _hit(self) -> None:
        self.lives -= 1
        self.deaths += 1
        self.invuln = 1.6
        self.shake = 0.35
        self.flash = 0.35
        self.player = list(self.start)
        self._popup(*self.start, "撞到 Bug！", RED)
        if self.lives <= 0:
            self.status = "lost"

    def _popup(self, x: int, y: int, text: str, color) -> None:
        self.popups.append([x, y, text, color, 1.0])

    def update(self, dt: float) -> None:
        dt = min(0.06, dt)
        if self.status != "playing":
            return
        self.elapsed += dt
        self.invuln = max(0.0, self.invuln - dt)
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        self.bug_timer += dt
        if self.bug_timer >= 0.52:
            self.bug_timer = 0.0
            for bug in self.bugs:
                self._move_bug(bug)
            self._check_bugs()
        for p in self.popups:
            p[1] -= 2 * dt
            p[4] -= dt
        self.popups = [p for p in self.popups if p[4] > 0]
        if self.remaining <= 0 and self.status == "playing":
            self.status = "lost"

    def _move_bug(self, bug: dict) -> None:
        x, y = bug["x"], bug["y"]
        opts = []
        for i, (dx, dy) in enumerate(DIRS):
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == " ":
                opts.append(i)
        if not opts:
            return
        avoid = (bug["dir"] + 2) % 4
        good = [i for i in opts if i != avoid] or opts
        # 偏好继续走，遇到岔路再随机
        if bug["dir"] in good and self.rng.random() < 0.55:
            pick = bug["dir"]
        else:
            pick = self.rng.choice(good)
        bug["dir"] = pick
        dx, dy = DIRS[pick]
        bug["x"] += dx
        bug["y"] += dy

    def outcome(self) -> Outcome:
        bonus = 500 + int(self.remaining * 8) if self.status == "won" else 0
        final = max(0, self.score + bonus - self.deaths * 80)
        return Outcome(
            "maze", self.status == "won", final, self.elapsed,
            [
                ("收集文件", f"{self.collected_count} / {len(FILES)}"),
                ("用时", f"{self.elapsed:0.1f}s"),
                ("剩余生命", f"{max(0, self.lives)} / {self.LIVES}"),
                ("步数", str(self.steps)),
            ],
        )

    # ---------- 渲染 ----------

    def render(self, c: Canvas) -> None:
        w, h = c.w, c.h
        c.fill(0, 0, w, h, " ", INK, BG)
        # HUD
        c.fill(0, 0, w, 2, " ", INK, BG)
        c.put(0, 0, " ZJUT LUG ", BG, GREEN, bold=True)
        c.put(12, 0, "Linux 新手村", INK, BG, bold=True)
        c.center(0, "文件迷宫 · 第 2 关", WHITE, BG, bold=True)
        c.right(w - 1, 0, f"{self.remaining:04.1f}s", RED if self.remaining < 15 else GREEN, BG, bold=True)
        c.put(1, 1, "SCORE", FAINT, BG)
        c.put(7, 1, f"{self.score:05d}", WHITE, BG, bold=True)
        hearts = "♥" * max(0, self.lives) + "♡" * (self.LIVES - max(0, self.lives))
        c.put(17, 1, hearts, PINK, BG, bold=True)
        c.put(24, 1, f"文件 {self.collected_count}/{len(FILES)}", AMBER, BG, bold=True)
        c.put(36, 1, "收集齐后去出口", FAINT, BG)
        c.right(w - 1, 1, "方向键 / WASD", DIM, BG)

        cellw = 2
        maze_w = self.cols * cellw
        x0 = (w - maze_w) // 2
        y0 = 3
        if maze_w + 2 > w or self.rows + 5 > h:
            c.center(max(1, h // 2), "窗口太小，放大后再继续", AMBER, BG, bold=True)
            return
        c.box(x0 - 1, y0 - 1, maze_w + 2, self.rows + 2, BLUE, "~/village", BLUE2, BG, fill_inner=True)
        for y in range(self.rows):
            for x in range(self.cols):
                px, py = x0 + x * 2, y0 + y
                g = self.grid[y][x]
                if g == "#":
                    shade = (28, 42, 68) if (x + y) % 3 else (34, 50, 80)
                    c.put(px, py, "▓▓", shade, BG)
                else:
                    trail = (x, y) in self.visited
                    col = (46, 62, 88) if trail else (32, 42, 62)
                    c.put(px, py, "· " if trail else "  ", col, BG)
                if (x, y) in self.files and (x, y) not in self.collected:
                    letter, _, col = self.files[(x, y)]
                    c.put(px, py, letter + " ", col, BG, bold=True)
        # 出口
        ex, ey = self.exit
        open_ = self.collected_count >= len(FILES)
        c.put(x0 + ex * 2, y0 + ey, "⌂ " if open_ else "▣ ",
              GREEN if open_ else FAINT, BG, bold=True)
        # Bug
        for bug in self.bugs:
            col = RED if int(self.elapsed * 6) % 2 else (180, 60, 80)
            c.put(x0 + bug["x"] * 2, y0 + bug["y"], "* ", col, BG, bold=True)
        # 玩家
        px, py = self.player
        if self.invuln <= 0 or int(self.elapsed * 12) % 2 == 0:
            jitter = 0
            if self.shake > 0:
                jitter = 1 if int(self.shake * 40) % 2 else -1
            c.put(x0 + px * 2 + jitter, y0 + py, "@ ", WHITE, BG, bold=True)
        # 浮动提示
        for x, y, text, col, life in self.popups:
            tx = max(1, min(w - len(text) - 2, x0 + x * 2 - 2))
            ty = max(3, min(h - 3, y0 + y - 1))
            c.put(tx, ty, text, col, BG, bold=True)

        # 图例
        c.put(2, h - 2, "T notes.txt", (110, 220, 255), BG, bold=True)
        c.put(16, h - 2, "P photo.png", (255, 170, 110), BG, bold=True)
        c.put(30, h - 2, "S run.sh", (112, 232, 164), BG, bold=True)
        c.put(41, h - 2, "M track.mp3", (214, 160, 255), BG, bold=True)
        c.put(55, h - 2, "@ 你", WHITE, BG, bold=True)
        c.put(61, h - 2, "* Bug", RED, BG, bold=True)
        c.put(2, h - 1, "方向键 / WASD 移动 · 收集 4 个文件后走到 ⌂ · P 暂停", FAINT, BG)
        c.right(w - 2, h - 1, "Ctrl-C 退出", FAINT, BG)
