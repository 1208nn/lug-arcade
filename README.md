# ZJUT LUG · Linux 新手村

**三个真正的小游戏**，不是答题，不收集身份信息，不联网，不写数据库。

1. **命令雨**：shell 命令从终端上方落下，在它落到提示符之前敲完。清掉 8 个命令，3 条命。
2. **文件迷宫**：在目录树迷宫里收集 4 个文件，避开巡逻的 Bug，再走到出口。3 条命、75 秒。
3. **发行版记忆**：翻开卡片，配出 6 对发行版 Logo。90 秒，鼠标和键盘都能玩。

三关走完会得到一张终端里的**新手村毕业画面**，可以拍照；上面只显示本局成绩和用时，没有身份信息。

## 运行

需要 [uv](https://docs.astral.sh/uv/)。活动前联网跑一次，现场离线可玩：

```bash
cd lug-newbie
mise exec -- uv sync
./lug
```

终端至少 **80 x 24**，推荐 **100 x 30** 全屏。窗口变化会自动重排。

调试时固定随机种子：

```bash
./lug --seed 7
```

## 操作

| 键 / 鼠标 | 作用 |
| --- | --- |
| `Tab` / `←` `→` | 菜单切换按钮 |
| `Enter` / `空格` | 确认、开始、翻牌 |
| `方向键` / `WASD` | 迷宫移动 / 记忆移动光标 |
| 直接敲键盘 | 命令雨输入；`Backspace` 撤回 |
| `Esc` | 游戏中暂停 |
| `P` | 迷宫 / 记忆里暂停；命令雨里 `p` 是命令字符 |
| `鼠标左键` | 菜单按钮、记忆翻牌 |
| `鼠标右键` | 游戏中暂停 |
| `Ctrl-C` | 退出 |

暂停菜单支持 `继续 / 重开 / 退出`，也可以用鼠标点。

## 三个小游戏

### 命令雨

- 命令卡从上往下掉，落到 `PROMPT` 就掉 1 条命
- 敲对字符变绿，当前字符反色显示；敲错只闪红，不前进
- 清掉 8 个命令通关
- 连击越高，单条命令得分越高；速度会慢慢加快
- 命令包括 `ls -la`、`grep -r TODO .`、`sudo apt update`、`tar -xzf pack.tgz` 等

### 文件迷宫

- 33x17 / 41x21 的随机迷宫，带环路
- 收集 `notes.txt`、`photo.png`、`run.sh`、`track.mp3` 四个文件
- 收集齐后出口从 `▣` 变成 `⌂`，走进去通关
- 2–3 只 Bug 在走廊里巡逻；撞到会回到起点，文件保留，掉 1 条命
- 75 秒倒计时

### 发行版记忆

- 4 x 3 张卡片，6 对 Logo：Ubuntu、Debian、Arch Linux、Fedora、Linux Mint、openSUSE
- 翻开两张，配对成功保留；失败会在短暂展示后翻回去
- 连击加分，90 秒内清空桌面通关
- Logo 用真彩半块字符绘制，不依赖终端图片协议

## 终端特性

- 真彩 TUI，30 FPS 主循环
- 标题页自动选择图片协议显示 Tux：
  - Kitty / Ghostty：Kitty 图形协议
  - WezTerm：iTerm2 内联图片（`OSC 1337`）
  - Tabby：Sixel（Tabby 会吞掉 `OSC 1337`）
  - 其他 / ConPTY：半块字符兜底
- SGR 鼠标（`1000` / `1006`）
- 方向键、Tab、鼠标、`WASD` 都可用
- 窗口缩放自动重排

## 项目结构

```text
lug             启动脚本
main.py         状态机、输入、30 FPS 主循环
village.py      三关流程、成绩、毕业判定
ui.py           标题 / 说明 / 关卡介绍 / 结果 / 暂停 / 毕业
typing_game.py  命令雨
maze_game.py    文件迷宫
memory_game.py  发行版记忆
canvas.py       真彩画布
term.py         终端输入、图片协议、SGR 鼠标
assetslib.py    PNG / 半块降采样
assets/         Tux、发行版 Logo、桌面插画
tools/          素材与 Sixel 调色板生成脚本
```

## 测试

```bash
mise exec -- uv run python -m py_compile main.py ui.py village.py typing_game.py maze_game.py memory_game.py canvas.py term.py assetslib.py
```

已验证：

- 80x24 / 100x30 布局
- 标题、说明、三关介绍、暂停、结果、毕业画面
- 命令雨输入、连击、掉命、通关
- 迷宫连通性、文件收集、出口、Bug 碰撞、通关与超时
- 记忆翻牌、配对、鼠标点击、通关与超时
- Tab / 方向键 / 鼠标菜单
- WezTerm（iTerm2）、Tabby（Sixel）、ConPTY（半块）三种图片链路无 Traceback
