# AetherForge

**AI-Native Game Creation & Runtime Engine**

AetherForge 是一个以 AI Agent 为主要用户的游戏开发与运行平台。它通过 **MCP Server** 暴露所有引擎能力，让 Codex / Claude 等 AI 可以直接理解、调用、观察和修改游戏世界。

---

## 快速开始

### 环境要求

- Python 3.10+
- 依赖安装：

```powershell
cd .
pip install -r requirements.txt
```

### 启动引擎

```powershell
# 方式一：MCP Server（推荐 — 供 Codex / Claude 调用）
cd .
python -m aetherforge.mcp_server
# 输出：AetherForge MCP Server v2.0.0 started - waiting for MCP client...

# 方式二：CLI
python -m aetherforge.cli

# 方式三：Web 查看器 (2D + 3D)
python -m aetherforge.main
```

---

## 让 Codex 调用 AetherForge

在 Codex 中，将以下内容加入任务提示词或 `AGENTS.md`：

> 该项目的 MCP Server 位于 `.`，运行命令为 `python -m aetherforge.mcp_server`。
> 引擎提供 56 个工具，涵盖语义世界模型、物理引擎、音频引擎、3D 渲染、AI 绘图、AI 音乐生成。
> 可通过 `read_project` / `observe` 查看世界状态，用 `create_entity` / `create_rule` / `create_quest` 构建游戏逻辑。

**MCP 配置（用于 Claude Desktop / Codex 等客户端）：**

```json
{
  "mcpServers": {
    "aetherforge": {
      "command": "python",
      "args": ["-m", "aetherforge.mcp_server"],
      "cwd": "D:\\news"
    }
  }
}
```

---

## 功能概览

| 模块 | 工具数 | 说明 |
|------|--------|------|
| **核心世界模型** | 17 | 创建/修改实体、规则、任务、NPC 行为、触发器 |
| **物理引擎** (pymunk) | 7 | 2D 物理：碰撞体、力、重力、射线检测 |
| **音频引擎** (pygame.mixer) | 7 | 加载/播放音效、背景音乐、音量控制 |
| **3D 渲染** (Three.js) | 5 | 网格、变换、灯光、相机、场景导出 |
| **AI 图片生成** | 4 | 多模型支持（anything-v5 / SD / FLUX 等） |
| **AI 音乐生成** | 4 | 多模型支持（MusicGen / AudioGen 等） |
| **工具链** | 12 | 保存/加载、测试、工作流、回滚 |

---

## AI 图片生成

引擎自动检测可用的图片生成模型：

**内置模型列表：**
- `anything-v5` — 二次元风格 (本地模型)
- `sd-v1.5` / `sd-v2.1` — Stable Diffusion
- `sdxl` — Stable Diffusion XL
- `sd3` — Stable Diffusion 3
- `flux-dev` — FLUX.1 dev
- `flux-schnell` — FLUX.1 schnell

```powershell
# 选择模型
python -c "from aetherforge.ai_engines.image_gen import ImageGenEngine; e=ImageGenEngine(); print(e.list_models())"
```

**自定义模型：** 将模型文件放入 `models/image/` 目录，引擎自动识别。

---

## AI 音乐生成

### 前置依赖

音乐生成需要 **Facebook AudioCraft**。安装方式：

```powershell
# 方案 A：完整安装（推荐 — 需要 FFmpeg SDK）
choco install ffmpeg         # 安装 FFmpeg（需要管理员权限）
pip install av>=12.0.0       # 跳过编译问题
pip install torch==2.1.0     # AudioCraft 需要此版本
pip install audiocraft

# 方案 B：跳过 torch 重装（用已有 torch）
pip install av>=12.0.0
pip install audiocraft --no-deps
pip install -r requirements-audiocraft.txt
```

**如果遇到编译错误 `LNK1181: 无法打开输入文件 avformat.lib`：**

这是 `av` 包需要 FFmpeg C 库编译。解决方案：
1. 安装 FFmpeg 开发版：`choco install ffmpeg`（含 .lib 文件）
2. 或使用预编译 wheel：`pip install av==17.1.0`（已预装）
3. 或修改 `audiocraft` 的依赖：将 `av==11.0.0` 改为 `av>=12.0.0`

**内置模型：**
- `musicgen-small` — MusicGen 小模型（最快）
- `musicgen-medium` — MusicGen 中模型（默认）
- `musicgen-large` — MusicGen 大模型（最佳质量）
- `audiogen` — AudioGen（音效生成）

```powershell
# 选择模型
python -c "from aetherforge.ai_engines.music_gen import MusicGenEngine; e=MusicGenEngine(); print(e.list_models())"
```

---

## 3D 引擎

基于 Three.js 的 WebGL 渲染器，运行在浏览器中：

```powershell
python -m aetherforge.main
# 打开 http://localhost:8080 查看 3D 场景
```

---

## 物理引擎

基于 pymunk (Chipmunk2D) 的 2D 物理模拟：

```python
from aetherforge.runtime.physics import PhysicsEngine
physics = PhysicsEngine(world)
physics.init()
physics.add_body("player", shape="box", mass=1.0)
physics.apply_force("player", fx=100, fy=0)
```

---

## 项目结构

```
aetherforge/
├── core/              # 语义世界模型、规则引擎、任务系统
├── api/               # 引擎工具接口 (ToolResult)
├── runtime/           # 游戏循环、物理、音频
├── renderer/          # 3D 场景图 (Three.js)
├── ai_engines/        # AI 图片生成、AI 音乐生成
├── demo/              # 示例场景 (雨夜车站)
├── test/              # 自动化测试
├── models/            # 模型存放目录
├── static/            # Web 前端文件
├── mcp_server.py      # MCP Server (56 tools)
├── cli.py             # 命令行接口
├── autonomous.py      # 自动化开发循环
└── config.py          # 全局配置
```

---

## MCP 工具列表 (56)

| 工具名 | 说明 |
|--------|------|
| `create_entity` | 创建语义实体 |
| `modify_entity` | 修改实体属性 |
| `remove_entity` | 删除实体 |
| `get_entity` | 查询实体详情 |
| `find_entities` | 按类型/标签搜索实体 |
| `create_rule` | 创建交互规则 |
| `remove_rule` | 删除规则 |
| `create_quest` | 创建任务 |
| `complete_quest_step` | 完成任务步骤 |
| `update_quest_state` | 更新任务状态 |
| `set_behavior` | 设置 NPC 行为 |
| `set_weather` | 设置天气 |
| `set_player` | 设置玩家实体 |
| `read_project` | 读取项目摘要 |
| `observe` | 观察世界快照 |
| `trigger_event` | 触发游戏事件 |
| `set_audio` | 配置音频 |
| `set_art_intent` | 设置美术意图 |
| `commit_change` | 提交变更 |
| `rollback_change` | 回滚变更 |
| `save_project` | 保存项目 |
| `load_project` | 加载项目 |
| `load_demo` | 加载示例场景 |
| `run_tests` | 运行测试 |
| `execute_workflow` | 执行多步工作流 |
| `init_physics` | 初始化物理引擎 |
| `add_physics_body` | 添加物理体 |
| `remove_physics_body` | 移除物理体 |
| `apply_force` | 施加力 |
| `set_gravity` | 设置重力 |
| `ray_cast` | 射线检测 |
| `get_physics_info` | 获取物理信息 |
| `init_audio` | 初始化音频 |
| `load_sound` | 加载音效 |
| `play_sound` | 播放音效 |
| `play_music` | 播放音乐 |
| `stop_music` | 停止音乐 |
| `set_audio_volume` | 设置音量 |
| `get_audio_state` | 获取音频状态 |
| `set_3d_mesh` | 设置 3D 网格 |
| `set_3d_transform` | 设置 3D 变换 |
| `add_3d_light` | 添加 3D 灯光 |
| `set_3d_camera` | 设置 3D 相机 |
| `get_3d_state` | 获取 3D 场景状态 |
| `init_image_gen` | 初始化图片生成 |
| `generate_image` | 生成图片 |
| `set_image_model` | 选择图片模型 |
| `get_image_models` | 列出图片模型 |
| `init_music_gen` | 初始化音乐生成 |
| `generate_music` | 生成音乐 |
| `set_music_model` | 选择音乐模型 |
| `get_music_models` | 列出音乐模型 |

---

## 配置

编辑 `config.py` 或设置环境变量：

```python
# 图片生成模型选择
IMAGE_MODEL = "anything-v5"  # 自动检测可用模型

# 音乐生成模型选择
MUSIC_MODEL = "musicgen-medium"  # 自动检测可用模型

# API Keys (用于在线模型)
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## GitHub

仓库地址：https://github.com/hvrrgfe/aetherforge

```powershell
git clone https://github.com/hvrrgfe/aetherforge.git
cd aetherforge
pip install -r requirements.txt
```

---

## License

MIT