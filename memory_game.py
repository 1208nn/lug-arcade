"""发行版记忆：翻开卡片，配出 6 对发行版 Logo。"""

from __future__ import annotations

import random

import assetslib
from canvas import (
    AMBER, BG, BLUE, DIM, FAINT, GREEN, INK, PANEL, PANEL2,
    RED, WHITE, Canvas, truncate, width,
)
from village import Outcome

DISTROS = (
    ("Ubuntu", "assets/logo_ubuntu.png", (233, 84, 32)),
    ("Debian", "assets/logo_debian.png", (220, 66, 80)),
    ("Arch Linux", "assets/logo_arch.png", (74, 163, 255)),
    ("Fedora", "assets/logo_fedora.png", (60, 110, 232)),
    ("Linux Mint", "assets/logo_mint.png", (95, 191, 127)),
    ("openSUSE", "assets/logo_suse.png", (115, 186, 70)),
)


class MemoryGame:
    TIME = 90.0

    def __init__(self, w: int, h: int, seed: int | None = None) -> None:
        self.w = w
        self.h = h
        self.rng = random.Random(seed)
        self.deck = [i for i in range(len(DISTROS)) for _ in range(2)]
        self.rng.shuffle(self.deck)
        self.matched: set[int] = set()
        self.flipped: list[int] = []
        self.lock = 0.0
        self.cursor = 0
        self.status = "playing"
        self.elapsed = 0.0
        self.moves = 0
        self.combo = 0
        self.max_combo = 0
        self.score = 0
        self.flash = 0.0
        self.shake = 0.0
        self.big = h >= 28
        self.card_w = 21 if w >= 96 else 17
        self.card_h = 7 if self.big else 6
        self.gap_x = 2
        self.gap_y = 1
        self.board_w = self.card_w * 4 + self.gap_x * 3
        self.board_h = self.card_h * 3 + self.gap_y * 2
        self.x0 = max(1, (w - self.board_w) // 2)
        self.y0 = max(2, (h - self.board_h) // 2)

    @property
    def remaining(self) -> float:
        return max(0.0, self.TIME - self.elapsed)

    @property
    def pairs(self) -> int:
        return len(self.matched) // 2

    def _rect(self, idx: int) -> tuple[int, int, int, int]:
        row, col = divmod(idx, 4)
        x = self.x0 + col * (self.card_w + self.gap_x)
        y = self.y0 + row * (self.card_h + self.gap_y)
        return x, y, self.card_w, self.card_h

    def _face_up(self, idx: int) -> bool:
        return idx in self.matched or idx in self.flipped

    def move_cursor(self, dx: int, dy: int) -> None:
        row, col = divmod(self.cursor, 4)
        row = (row + dy) % 3
        col = (col + dx) % 4
        self.cursor = row * 4 + col

    def flip(self, idx: int | None = None) -> None:
        if self.status != "playing" or self.lock > 0:
            return
        if idx is None:
            idx = self.cursor
        if idx < 0 or idx >= len(self.deck) or idx in self.matched or idx in self.flipped:
            return
        self.flipped.append(idx)
        if len(self.flipped) == 1:
            return
        self.moves += 1
        a, b = self.flipped
        if self.deck[a] == self.deck[b]:
            self.matched.update((a, b))
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            self.score += 200 + self.combo * 50
            self.flipped = []
            self.lock = 0.28
            if len(self.matched) == len(self.deck):
                self.status = "won"
                self.score += 400 + int(self.remaining * 10)
        else:
            self.combo = 0
            self.flash = 0.25
            self.shake = 0.25
            self.lock = 0.85

    def handle_key(self, key: str) -> None:
        if self.status != "playing":
            return
        if key in ("left", "a", "A"):
            self.move_cursor(-1, 0)
        elif key in ("right", "d", "D"):
            self.move_cursor(1, 0)
        elif key in ("up", "w", "W"):
            self.move_cursor(0, -1)
        elif key in ("down", "s", "S"):
            self.move_cursor(0, 1)
        elif key in ("enter", "space"):
            self.flip()

    def click(self, x: int, y: int) -> None:
        if self.status != "playing":
            return
        for idx in range(len(self.deck)):
            rx, ry, rw, rh = self._rect(idx)
            if rx <= x < rx + rw and ry <= y < ry + rh:
                self.cursor = idx
                self.flip(idx)
                return

    def update(self, dt: float) -> None:
        dt = min(0.06, dt)
        if self.status != "playing":
            return
        self.elapsed += dt
        self.flash = max(0.0, self.flash - dt)
        self.shake = max(0.0, self.shake - dt)
        if self.lock > 0:
            self.lock -= dt
            if self.lock <= 0:
                if len(self.flipped) == 2 and self.deck[self.flipped[0]] != self.deck[self.flipped[1]]:
                    self.flipped = []
        if self.remaining <= 0:
            self.status = "lost"

    def outcome(self) -> Outcome:
        return Outcome(
            "memory", self.status == "won", int(self.score), self.elapsed,
            [
                ("配对", f"{self.pairs} / 6"),
                ("翻牌次数", str(self.moves)),
                ("最大连击", f"x{self.max_combo}"),
                ("用时", f"{self.elapsed:0.1f}s"),
            ],
        )

    def _draw_logo(self, c: Canvas, name: str, x: int, y: int, cols: int, rows: int) -> None:
        small = assetslib.half(name, cols, rows)
        if small is None:
            c.put(x, y, "缺失", RED, PANEL)
            return
        for yy in range(small.h // 2):
            for xx in range(small.w):
                i = (yy * 2 * small.w + xx) * 3
                j = ((yy * 2 + 1) * small.w + xx) * 3
                top = (small.buf[i], small.buf[i + 1], small.buf[i + 2])
                bot = (small.buf[j], small.buf[j + 1], small.buf[j + 2])
                c.put(x + xx, y + yy, "▀", top, bot)

    def render(self, c: Canvas) -> None:
        w, h = c.w, c.h
        c.fill(0, 0, w, h, " ", INK, BG)
        # 背景只留一点边缘星，不干扰卡片
        for i in range(16):
            c.put((i * 47 + 3) % max(1, w), 2 + (i * 13) % max(1, h - 4),
                  "·", (22, 32, 52), BG)
        # HUD
        c.fill(0, 0, w, 2, " ", INK, BG)
        c.put(0, 0, " ZJUT LUG ", BG, AMBER, bold=True)
        c.put(12, 0, "Linux 新手村", INK, BG, bold=True)
        c.center(0, "发行版记忆 · 第 3 关", WHITE, BG, bold=True)
        c.right(w - 1, 0, f"{self.remaining:04.1f}s", RED if self.remaining < 15 else AMBER, BG, bold=True)
        c.put(1, 1, "SCORE", FAINT, BG)
        c.put(7, 1, f"{self.score:05d}", WHITE, BG, bold=True)
        c.put(17, 1, f"配对 {self.pairs}/6", GREEN, BG, bold=True)
        c.put(27, 1, f"翻牌 {self.moves}", DIM, BG)
        c.put(37, 1, f"COMBO x{self.combo}", AMBER if self.combo else FAINT, BG, bold=True)
        c.right(w - 1, 1, "方向键移动 · Enter 翻牌", DIM, BG)

        for idx in range(len(self.deck)):
            x, y, cw, ch = self._rect(idx)
            distro = self.deck[idx]
            name, logo, color = DISTROS[distro]
            up = self._face_up(idx)
            matched = idx in self.matched
            focused = idx == self.cursor and self.status == "playing"
            if self.shake > 0 and len(self.flipped) == 2 and idx in self.flipped:
                x += 1 if int(self.shake * 50) % 2 else -1
            border = GREEN if matched else (color if up else (AMBER if focused else (RED if self.flash > 0 and idx in self.flipped else BLUE)))
            bg = PANEL if up else PANEL2
            c.fill(x, y, cw, ch, " ", INK, bg)
            c.box(x, y, cw, ch, border, "", border, bg)
            if up:
                logo_cols, logo_rows = cw - 4, (ch - 3)
                self._draw_logo(c, logo, x + 2, y + 1, logo_cols, logo_rows)
                label = truncate(name, cw - 3)
                c.put(x + max(1, (cw - width(label)) // 2), y + ch - 2,
                      label, color if not matched else GREEN, bg, bold=True)
                if matched:
                    c.put(x + cw - 2, y, "✓", GREEN, bg, bold=True)
            else:
                c.put(x + cw // 2, y + ch // 2 - 1, "?", color if focused else FAINT, bg, bold=True)
                c.put(x + max(1, (cw - 8) // 2), y + ch // 2 + 1, "LINUX", (62, 78, 106), bg)
            if focused:
                c.put(x + 1, y + ch - 1, "▸", AMBER, bg, bold=True)

        msg = "配出 6 对发行版 Logo" if self.status == "playing" else ""
        c.put(2, h - 2, msg, FAINT, BG)
        c.put(30, h - 2, "Enter / 鼠标翻牌", FAINT, BG)
        c.put(50, h - 2, "P 暂停", FAINT, BG)
        c.right(w - 2, h - 2, "Ctrl-C 退出", FAINT, BG)
        c.hline(0, h - 1, w, "─", FAINT, BG)
