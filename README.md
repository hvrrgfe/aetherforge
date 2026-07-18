<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/MCP-Enabled-FF6B35?style=flat" alt="MCP">
  <img src="https://img.shields.io/badge/3D-Three.js-green?style=flat&logo=three.js" alt="3D">
  <img src="https://img.shields.io/badge/Physics-pymunk-purple?style=flat" alt="Physics">
  <img src="https://img.shields.io/badge/AI-MusicGen-red?style=flat" alt="AI Music">
  <img src="https://img.shields.io/badge/AI-Stable%20Diffusion-orange?style=flat" alt="AI Image">
  <br>
  <img src="https://img.shields.io/github/last-commit/hvrrgfe/aetherforge?style=flat&color=informational" alt="Last Commit">
  <img src="https://img.shields.io/github/license/hvrrgfe/aetherforge?style=flat" alt="License">
</p>

<h1 align="center">⚡ AetherForge</h1>
<p align="center"><strong>给 AI 用的游戏引擎，人看着就行</strong></p>
<p align="center">
  Codex、Claude 这类 AI 通过 <b>MCP 协议</b>直接调 53 个工具<br>
  搭场景 · 写规则 · 上物理 · 播音频 · 3D 渲染 · AI 画图作曲
</p>

---

## 📋 目录

- [✨ 功能](#-功能)
- [📦 安装](#-安装)
- [🚀 快速开始](#-快速开始)
- [🛠 工具一览](#-工具一览)
- [🤖 Codex 集成](#-codex-集成)
- [🎨 AI 模型](#-ai-模型)
- [⚠️ 常见问题](#️-常见问题)
- [📄 开源协议](#-开源协议)

---

## ✨ 功能

| 模块 | 说明 |
|------|------|
| 🧠 **语义世界模型** | 实体有类型、描述、能力、状态、关系——AI 可直接理解 |
| ⚛️ **物理引擎** | pymunk 驱动的 2D 物理：重力、碰撞、力、射线检测 |
| 🔊 **音频引擎** | pygame.mixer：音效、背景音乐、音量控制、淡入淡出 |
| 🎮 **3D 渲染** | Three.js WebGL：网格、灯光、相机、场景导出 |
| 🖼️ **AI 图片生成** | 7 种模型：anything-v5 / SD / SDXL / FLUX |
| 🎵 **AI 音乐生成** | 5 种模型：MusicGen small / medium / large / melody / AudioGen |
| 🔄 **事务回滚** | 所有操作可撤销，`commit_change` / `rollback_change` |
| 🧪 **自动化测试** | 一键运行场景测试 |
| 🔌 **MCP 协议** | 原生支持 Codex / Claude Desktop 等 MCP 客户端 |

---

## 📦 安装

### 环境要求

- Python 3.10+
- 4GB+ 内存（AI 功能需要 8GB+）

### 1. 克隆仓库

```powershell
git clone https://github.com/hvrrgfe/aetherforge.git
cd aetherforge
```

### 2. 安装核心依赖

```powershell
pip install -r requirements.txt
```

### 3. 安装可选引擎

<details>
<summary><b>物理引擎</b>（推荐）</summary>

```powershell
pip install pymunk
```
</details>

<details>
<summary><b>音频引擎</b>（推荐）</summary>

```powershell
pip install pygame
```
</details>

<details>
<summary><b>AI 图片生成</b>（需要 8GB+ 内存）</summary>

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install diffusers transformers
```
</details>

<details>
<summary><b>AI 音乐生成</b>（需要 8GB+ 内存，见 FAQ）</summary>

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install audiocraft --no-build-isolation --no-deps --no-cache-dir
pip install julius flashy hydra-core hydra_colorlog num2words tqdm
pip install spacy transformers huggingface_hub
pip install librosa torchmetrics xformers
```
</details>

### 🔄 4. 更新项目

定期更新以获取最新功能和修复：

```powershell
# ① 拉取最新代码
git pull

# ② 同步安装新依赖
pip install -r requirements.txt

# ③ 如果需要，更新配置文件（保留你的自定义配置）
python -c "from aetherforge.config import get_config, save_config; save_config(get_config()); print('Config updated')"
```

完成后重新启动引擎即可。

---

### ✅ 5. 验证安装

```powershell
python -c "from aetherforge.api.engine_v2 import EngineToolsV2; from aetherforge.core.world_model import WorldModel; t = EngineToolsV2(WorldModel()); print('OK:', len(t.list_tools().data['tools']), 'tools')"
```

---

## 🚀 快速开始



```powershell
python -m aetherforge.mcp_server
# 输出：AetherForge MCP Server v2.0.0 started - waiting for MCP client...
```

### Web 应用（供人查看）

```powershell
# 2D + 3D 画面
python -m aetherforge.main --demo
```

| 端点 | 地址 |
|------|------|
| 🌐 游戏画面 | [http://localhost:7890/](http://localhost:7890/) |
| 🎮 3D 画面 | [http://localhost:7890/viewer-3d](http://localhost:7890/viewer-3d) |
| 🔌 工具列表 (API) | [http://localhost:7890/api/tools/](http://localhost:7890/api/tools/) |
| 📡 世界状态 | [http://localhost:7890/api/observe](http://localhost:7890/api/observe) |

### 命令行

```powershell
# 查看所有工具
python -m aetherforge.cli --tool list_tools

# 交互模式
python -m aetherforge.cli
```

---

## 🛠 工具一览

### 核心（22 个）

```
create_entity    modify_entity    remove_entity    get_entity       find_entities
create_rule      remove_rule      create_quest     complete_quest_step  update_quest_state
set_behavior     set_weather      set_player       trigger_event    read_project
observe          commit_change    rollback_change  set_audio        set_art_intent
save_project     load_project
```

### 物理引擎（7 个）— 需 pymunk

```
init_physics  add_physics_body  remove_physics_body  apply_force
set_gravity   ray_cast          get_physics_info
```

### 音频引擎（7 个）— 需 pygame

```
init_audio  load_sound  play_sound  play_music
stop_music  set_audio_volume  get_audio_state
```

### 3D 引擎（6 个）— 浏览器 Three.js

```
set_3d_mesh  set_3d_transform  add_3d_light
set_3d_camera  get_3d_state
```

### AI 图片生成（4 个）— 需 torch + diffusers

```
init_image_gen  generate_image  set_image_model  get_image_models
```

### AI 音乐生成（4 个）— 需 torch + audiocraft

```
init_music_gen  generate_music  set_music_model  get_music_models
```

### 特殊功能（3 个）

```
load_demo  run_tests  execute_workflow
```

---


## 🤖 Codex 集成

### MCP 客户端配置

在 Claude Desktop / Codex 客户端的 MCP 配置中加上：

```json
{
  "mcpServers": {
    "aetherforge": {
      "command": "python",
      "args": ["-m", "aetherforge.mcp_server"],
      "cwd": "C:\\path\\to\\aetherforge"
    }
  }
}
```

### Codex 提示词模板

放到 Codex 的 `AGENTS.md` 或任务提示词里：

```markdown
## AetherForge 引擎指令

你已经连上了 AetherForge MCP Server。有 53 个工具可用。

### 几条原则
- 别去改 Python 文件——所有操作走工具
- 描述实体时带上语义（type、description、capabilities、state）
- 事务安全——失败了可以 rollback_change() 撤回
- 工具返回 JSON——解析结果，别搜日志

### 开发流程
read_project → create_entity → create_rule → set_behavior → observe → run_tests → commit_change

### 常用工具速查
| 想干啥 | 用啥工具 | 参数 |
|------|------|------|
| 创建场景 | create_entity | semantic_type, name, position, visual |
| 改天气 | set_weather | weather: "rainy"/"clear" |
| 设玩家 | set_player | entity_id |
| 加规则 | create_rule | when, then, trigger_type |
| 创建任务 | create_quest | name, description, steps |
| NPC 行为 | set_behavior | entity_id, behavior_type, goals |
| 物理 | init_physics → add_physics_body | shape, mass, dynamic |
| 音频 | init_audio → play_music | name, volume, loop |
| 3D | set_3d_mesh → set_3d_transform | geometry, color, x/y/z |
| AI 画图 | generate_image | prompt, width, height |
| AI 音乐 | generate_music | description, duration |

### 怎么看结果
- 游戏画面：http://localhost:7890/
- 3D 画面：http://localhost:7890/viewer-3d
- 世界状态：http://localhost:7890/api/observe
```

## 🎨 AI 模型

### 图片生成

引擎自动扫描 `models/` 目录和 HuggingFace 缓存，支持 7 种模型：

| 模型 | 参数 | 最低显存 | 说明 |
|------|------|----------|------|
| `anything-v5` | — | 4GB | 动漫风格，适合游戏素材 |
| `sd-1.5` | 860M | 4GB | Stable Diffusion 1.5 |
| `sd-2.1` | 860M | 4GB | SD 2.1 质量改进 |
| `sdxl` | 2.6B | 8GB | SDXL 高质量 |
| `sd3` | 2.6B | 8GB | Stable Diffusion 3 |
| `flux-schnell` | 3.5B | 8GB | FLUX 快速版 |
| `flux-dev` | 12B | 12GB | FLUX 高质量版 |

### 音乐生成

| 模型 | 参数 | 说明 |
|------|------|------|
| `musicgen-small` | 300M | 最快，适合音效 |
| `musicgen-medium` | 1.5B | 均衡质量/速度 |
| `musicgen-large` | 3.3B | 最佳质量，需 8GB+ |
| `musicgen-melody` | 1.5B | 旋律条件生成 |
| `audiogen` | 1.5B | 专注音效生成 |

### 切换模型
```powershell
# 看看有哪些模型
python -m aetherforge.cli --tool list_image_models
python -m aetherforge.cli --tool list_music_models

# 切换模型（名字或本地路径都行）
python -m aetherforge.cli --tool select_image_model --params '{"name_or_path":"sdxl"}'
python -m aetherforge.cli --tool select_music_model --params '{"name_or_path":"musicgen-large"}'

# 开画
python -m aetherforge.cli --tool generate_image --params '{"prompt":"a rusty iron door"}'

---

## 📁 本地模型放置指南

引擎启动时会自己扫 models/ 目录，模型扔进去就能用。

### 目录结构

```
aetherforge/
├── models/                    # ← 引擎自动扫描此目录
│   ├── anything-v5/           #   模型名称随意，引擎自动识别
│   │   ├── model_index.json   #   Diffusers 格式必须有此文件
│   │   ├── unet/
│   │   ├── vae/
│   │   └── text_encoder/
│   ├── sdxl-base-1.0/         #   SDXL 模型同理
│   ├── my-custom-model/       #   你自己的模型
│   │   ├── model_index.json
│   │   └── *.safetensors
│   └── musicgen-medium/       #   音乐模型（目录名含 musicgen）
│       └── ...
└── ...
```

### 支持的模型格式

| 格式 | 说明 | 必须包含 |
|------|------|----------|
| **Diffusers** | 完整 pipeline 目录 | `model_index.json` + `unet/`、`vae/`、`text_encoder/` 等子目录 |
| **SafeTensors** | 单个或多个 `.safetensors` 文件 | 至少一个 `.safetensors` 文件 |
| **HuggingFace 缓存** | HF 自动下载到缓存目录 | 无需手动操作，`~/.cache/huggingface/hub/` 自动识别 |

### 放置步骤

**① 创建 `models/` 目录**

```powershell
# 在项目根目录创建
mkdir models
```

**② 放入模型**

- **anything-v5**：将完整模型文件夹放到 `models/anything-v5/`
- **从 HuggingFace 下载**：

```powershell
# 方法 A：使用 huggingface-cli 下载到本地
pip install huggingface-hub
huggingface-cli download stablediffusionapi/anything-v5 --local-dir models/anything-v5

# 方法 B：直接复制已有文件夹
Copy-Item -Recurse D:\path\to\your\model models\my-model
```

**③ 验证识别**

```powershell
python -m aetherforge.cli --tool list_image_models
python -m aetherforge.cli --tool list_music_models
```

引擎会输出类似：
```
Available image models: anything-v5 (local), sdxl (downloadable)...
Available music models: musicgen-medium (local), musicgen-small (downloadable)...
```

### 手动指定路径

如果模型不在标准路径，可通过配置指定：

```yaml
# ~/.aetherforge/config.yaml
image_gen:
  model_path: "D:/my_models/sd-model"
music_gen:
  model_id: "facebook/musicgen-small"
```

或在工具中直接传路径：

```powershell
python -m aetherforge.cli --tool select_image_model --params '{"name_or_path":"D:/my_models/sd-model"}'
```

### 引擎自动识别逻辑

- **图片模型**：扫 `models/` 下子目录，找 `model_index.json` 或 `*.safetensors`
- **音乐模型**：扫目录名带 `musicgen` 的文件夹
- **HF 缓存**：自动识别 `~/.cache/huggingface/hub/models--*`
- **anything-v5**：引擎内建识别，放 `models/anything-v5/` 就行
- **后备**：本地找不到就从 HuggingFace 下（需要外网）

---

## ⚠️ 常见问题

<details>
<summary><b>audiocraft 安装失败：av 编译错误 LNK1181</b></summary>

```
error: Failed building wheel for av
LINK : fatal error LNK1181: 无法打开输入文件 avformat.lib
```

**原因：** `audiocraft` 锁死 `av==11.0.0`，该版本无 Windows 预编译 wheel。

**方案 A：使用预装 av + 跳过隔离编译（推荐）**

```powershell
pip install av>=12.0.0
pip install audiocraft --no-build-isolation --no-deps --no-cache-dir
pip install julius flashy hydra-core hydra_colorlog num2words tqdm
pip install spacy transformers huggingface_hub
pip install librosa torchmetrics xformers
```

**方案 B：安装 FFmpeg SDK（完整编译）**

```powershell
choco install ffmpeg   # 需要管理员权限
pip install audiocraft
```
</details>

<details>
<summary><b>MCP Server 报 Internal Server Error</b></summary>

```
Received exception from stream: 1 validation error for JSONRPCMessage
{"method":"notifications/message","params":{"data":"Internal Server Error"}}
```

**原因：** HuggingFace 网络超时导致 MusicGen 模型下载卡死（旧版本），或终端发送空行到 stdin。

**解决：** 更新到最新版本即可：

```powershell
git pull
```

新版本 `init_music_gen` 不再阻塞下载。无网络时返回错误提示，不会卡死 MCP Server。
</details>

<details>
<summary><b>HuggingFace 网络超时</b></summary>

环境无法访问 huggingface.co 时，模型自动下载会失败。

**解决：**
1. 在有外网的机器上预下载模型，复制到 `models/` 目录
2. 或使用本地路径：`select_model("D:/path/to/local/model")`
</details>

---

## 📄 开源协议

MIT License

---

<p align="center">
  <sub>AetherForge — 让 AI 不需要学习传统引擎，直接用意图、语义、工具和反馈创造游戏。</sub>
</p>
