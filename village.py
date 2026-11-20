"""新手村流程：三关、成绩与毕业。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LevelDef:
    key: str
    name: str
    subtitle: str
    goal: str
    controls: str
    accent: tuple[int, int, int]


LEVELS = (
    LevelDef(
        "typing",
        "命令雨",
        "在命令落地之前敲完它",
        "清掉 8 个命令。每个命令落到提示符就会掉 1 条命，3 条命用完就失败。",
        "直接敲键盘 · Backspace 撤回 · Esc 暂停",
        (110, 200, 255),
    ),
    LevelDef(
        "maze",
        "文件迷宫",
        "把文件带回新手村",
        "在迷宫里收集 4 个文件，再走到出口。避开巡逻的 Bug，别把 3 条命撞光。",
        "方向键 / WASD 移动 · P 暂停",
        (112, 232, 164),
    ),
    LevelDef(
        "memory",
        "发行版记忆",
        "把成对的 Logo 翻出来",
        "翻开两张卡片，配出 6 对发行版 Logo。90 秒内清空桌面。",
        "方向键移动 · Enter 翻牌 · 鼠标点击 · P 暂停",
        (255, 199, 92),
    ),
)


@dataclass
class Outcome:
    key: str
    won: bool
    score: int
    seconds: float
    stats: list[tuple[str, str]] = field(default_factory=list)


class Run:
    def __init__(self) -> None:
        self.index = 0
        self.outcomes: dict[str, Outcome] = {}
        self.started = time.monotonic()

    @property
    def level(self) -> LevelDef:
        return LEVELS[min(self.index, len(LEVELS) - 1)]

    @property
    def total_score(self) -> int:
        return sum(o.score for o in self.outcomes.values())

    @property
    def won_count(self) -> int:
        return sum(1 for o in self.outcomes.values() if o.won)

    @property
    def all_won(self) -> bool:
        return len(self.outcomes) == len(LEVELS) and self.won_count == len(LEVELS)

    @property
    def elapsed(self) -> float:
        return max(0.0, time.monotonic() - self.started)

    def record(self, outcome: Outcome) -> None:
        self.outcomes[outcome.key] = outcome

    def advance(self) -> None:
        self.index = min(len(LEVELS), self.index + 1)

    @property
    def finished(self) -> bool:
        return self.index >= len(LEVELS)
