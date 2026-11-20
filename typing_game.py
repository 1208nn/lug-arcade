"""命令雨：在 shell 命令落到提示符之前把它敲完。"""

from __future__ import annotations

import random
from dataclasses import dataclass

from canvas import (
    AMBER, AMBER2, BG, BLUE, BLUE2, DIM, FAINT, GREEN, INK, PANEL, PANEL2,
    PINK, RED, WHITE, Canvas, truncate, width,
)
from village import Outcome

COMMANDS = (
    ("ls -la", "列出所有文件"),
    ("cd ..", "回到上一级"),
    ("pwd", "显示当前路径"),
    ("mkdir demo", "新建目录"),
    ("cp a.txt b.txt", "复制文件"),
    ("rm note.txt", "删除文件"),
    ("cat README.md", "查看文件内容"),
    ("grep -r TODO .", "搜索 TODO"),
    ("chmod +x run.sh", "加执行权限"),
    ("ps aux", "查看进程"),
    ("df -h", "查看磁盘"),
    ("sudo apt update", "更新软件源"),
    ("tar -xzf pack.tgz", "解压压缩包"),
    ("ssh lug@booth", "连到摊位"),
    ("ls | grep log", "过滤文件列表"),
    ("echo $HOME", "打印家目录"),
)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


class TypingGame:
    GOAL = 8
    LIVES = 3

    def __init__(self, w: int, h: int, seed: int | None = None) -> None:
        self.w = w
        self.h = h
        self.rng = random.Random(seed)
        self.status = "playing"
        self.score = 0
        self.lives = self.LIVES
        self.cleared = 0
        self.combo = 0
        self.max_combo = 0
        self.hits = 0
        self.errors = 0
        self.elapsed = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.spawn_delay = 0.0
        self.recent: list[str] = []
        self.particles: list[Particle] = []
        self.popups: list[tuple[float, float, str, tuple, float]] = []
        self.floor_y = h - 6
        self.cmd = ""
        self.hint = ""
        self.index = 0
        self.y = 4.0
        self.speed = self._base_speed()
        self._next(initial=True)

    def _base_speed(self) -> float:
        return max(1.15, (self.floor_y - 4) / 10.5)

    def _next(self, initial: bool = False) -> None:
        pool = [c for c in COMMANDS if c[0] not in self.recent] or list(COMMANDS)
        self.cmd, self.hint = self.rng.choice(pool)
        self.recent.append(self.cmd)
        self.recent = self.recent[-5:]
        self.index = 0
        self.y = 4.0
        self.speed = self._base_speed() + self.cleared * 0.13
        self.spawn_delay = 0.0

    @property
    def accuracy(self) -> int:
        total = self.hits + self.errors
        return round(self.hits / total * 100) if total else 100

    def handle_key(self, key: str) -> None:
        if self.status != "playing" or not self.cmd:
            return
        if key == "backspace":
            if self.index > 0:
                self.index -= 1
            return
        if key == "space":
            ch = " "
        elif len(key) == 1 and key.isprintable():
            ch = key
        else:
            return
        if ch == self.cmd[self.index]:
            self.index += 1
            self.hits += 1
            if self.index >= len(self.cmd):
                self._complete()
        else:
            self.errors += 1
            self.combo = 0
            self.shake = 0.22
            self.flash = 0.18
            self._puff(0.5, 0.5, RED, 5)

    def _complete(self) -> None:
        self.cleared += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        gained = 100 + self.combo * 25 + max(0, int((self.floor_y - self.y) * 4))
        self.score += gained
        cx = self.w / 2
        self.popups.append((cx - 2, self.y + 1, f"+{gained}", GREEN, 0.9))
        self._puff(cx, self.y + 2, GREEN, 18)
        if self.cleared >= self.GOAL:
            self.status = "won"
            return
        self.cmd = ""
        self.spawn_delay = 0.32

    def _puff(self, x: float, y: float, color, n: int) -> None:
        for _ in range(n):
            self.particles.append(Particle(
                x + self.rng.uniform(-5, 5), y + self.rng.uniform(-2, 2),
                self.rng.uniform(-22, 22), self.rng.uniform(-30, 4),
                self.rng.uniform(0.3, 0.7), color,
            ))

    def update(self, dt: float) -> None:
        dt = min(0.06, dt)
        if self.status != "playing":
            return
        self.elapsed += dt
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 48 * dt
        self.particles = [p for p in self.particles if p.life > 0]
        self.popups = [(x, y - 8 * dt, text, col, life - dt)
                       for x, y, text, col, life in self.popups if life > dt]
        if self.spawn_delay > 0:
            self.spawn_delay -= dt
            if self.spawn_delay <= 0:
                self._next()
            return
        if not self.cmd:
            return
        self.y += self.speed * dt
        if self.y + 3 >= self.floor_y:
            self.lives -= 1
            self.combo = 0
            self.shake = 0.3
            self.flash = 0.3
            self._puff(self.w / 2, self.floor_y - 1, RED, 16)
            if self.lives <= 0:
                self.status = "lost"
                self.cmd = ""
            else:
                self.cmd = ""
                self.spawn_delay = 0.55

    def outcome(self) -> Outcome:
        return Outcome(
            "typing", self.status == "won", int(self.score), self.elapsed,
            [
                ("完成命令", f"{self.cleared} / {self.GOAL}"),
                ("最大连击", f"x{self.max_combo}"),
                ("准确率", f"{self.accuracy}%"),
                ("剩余生命", f"{max(0, self.lives)} / {self.LIVES}"),
            ],
        )

    def render(self, c: Canvas) -> None:
        w, h = c.w, c.h
        c.fill(0, 0, w, h, " ", INK, BG)
        # HUD
        c.fill(0, 0, w, 2, " ", INK, BG)
        c.put(0, 0, " ZJUT LUG ", BG, BLUE, bold=True)
        c.put(12, 0, "Linux 新手村", INK, BG, bold=True)
        c.center(0, "命令雨 · 第 1 关", WHITE, BG, bold=True)
        c.right(w - 1, 0, f"命令 {self.cleared}/{self.GOAL}", BLUE2, BG, bold=True)
        c.put(1, 1, "SCORE", FAINT, BG)
        c.put(7, 1, f"{int(self.score):05d}", WHITE, BG, bold=True)
        hearts = "♥" * max(0, self.lives) + "♡" * (self.LIVES - max(0, self.lives))
        c.put(17, 1, hearts, PINK, BG, bold=True)
        c.put(24, 1, f"COMBO x{self.combo}", AMBER if self.combo else FAINT, BG, bold=True)
        c.right(w - 1, 1, f"ACC {self.accuracy}%", DIM, BG)

        panel_x, panel_w = 2, w - 4
        c.box(panel_x, 2, panel_w, self.floor_y - 1, BLUE, "COMMAND RAIN", BLUE2, BG, fill_inner=True)
        # 面板内部的代码雨
        for i in range(26):
            x = (i * 37 + 5) % max(1, w - 8) + 4
            yy = 3 + (i * 23 + int(self.elapsed * (6 if i % 3 else 11))) % max(1, self.floor_y - 5)
            c.put(x, yy, ("$", "0", "1", "{", "}", "#")[i % 6], (26, 42, 68), BG)
        c.put(panel_x + 2, 3, "把命令完整敲进终端。空格也算一个字符。", FAINT, BG)
        track = self.floor_y - 2
        c.hline(panel_x + 1, self.floor_y, panel_w - 2, "━", (90, 42, 54), BG)
        c.put(w - 13, self.floor_y, " PROMPT ", RED, BG, bold=True)

        # 下落的命令卡
        if self.cmd:
            ch = self.h
            card_w = min(panel_w - 8, max(36, width(self.cmd) + 12))
            card_x = (w - card_w) // 2
            if self.shake > 0:
                card_x += int(2 * (self.shake / 0.22)) * (1 if int(self.shake * 60) % 2 else -1)
            yy = int(min(self.y, self.floor_y - 4))
            border = RED if self.flash > 0 else BLUE2
            c.fill(card_x, yy, card_w, 4, " ", INK, PANEL2)
            c.box(card_x, yy, card_w, 4, border, "", border, PANEL2)
            tx = card_x + 3
            blink = int(self.elapsed * 8) % 2 == 0
            for i, chv in enumerate(self.cmd):
                if i < self.index:
                    col, bold = GREEN, True
                elif i == self.index:
                    col, bold = AMBER2, True
                else:
                    col, bold = INK, False
                if i == self.index and blink:
                    # 反色光标：不遮住下一个字符
                    c.put(tx + i, yy + 1, chv, BG, AMBER, bold=True)
                else:
                    c.put(tx + i, yy + 1, chv, col, PANEL2, bold=bold)
            c.put(card_x + 3, yy + 2, truncate(self.hint, card_w - 6), DIM, PANEL2)

        # 提示符
        py = self.floor_y + 1
        c.put(3, py, "lug@village:~$ ", GREEN, BG, bold=True)
        typed = self.cmd[:self.index] if self.cmd else ""
        c.put(19, py, typed, AMBER2, BG, bold=True)
        if int(self.elapsed * 6) % 2 == 0:
            c.put(19 + width(typed), py, "█", AMBER, BG, bold=True)
        c.right(w - 3, py, "落到这里就掉 1 条命", FAINT, BG)

        # 粒子 / 飘字
        for p in self.particles:
            k = max(0.0, min(1.0, p.life / 0.7))
            col = tuple(int(BG[i] + (p.color[i] - BG[i]) * k) for i in range(3))
            c.put(int(p.x), int(p.y), "·" if p.life < 0.35 else "✧", col, BG, bold=True)
        for x, y, text, col, life in self.popups:
            c.put(int(x), int(y), text, col, BG, bold=True)

        c.put(2, h - 3, "直接敲键盘", FAINT, BG)
        c.put(15, h - 3, "Backspace 撤回", FAINT, BG)
        c.put(33, h - 3, "Esc 暂停", FAINT, BG)
        c.right(w - 2, h - 3, "Ctrl-C 退出", FAINT, BG)
        c.hline(0, h - 1, w, "─", FAINT, BG)
