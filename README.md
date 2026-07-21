# AetherForge

**AI-Native 游戏创作与运行时系统**

| 语言 | 模块 | 功能 | 状态 |
|------|------|------|------|
| **Java 21** | `src/com/aetherforge/launcher/` | 统一启动器 (Swing, 组件管理 + 模型下载) | ✅ 新增 |
| **C# .NET 9** | `AetherForgeStudio-WinUI/` | 桌面客户端 (WinUI 3, MVVM, WebSocket) | ✅ 已编译 EXE |
| **Python 3.10+** | `aetherforge/` | 核心引擎 (76+ tools, MCP, Agent Runtime) | ✅ 完整 |
| **Java 21** | `src/com/aetherforge/ui/` | 桌面编辑器 (Swing + FlatLaf) | ✅ 完整 |

---

## 快速开始

### 启动器（推荐）

一键管理所有组件和 AI 模型：

```powershell
launcher.bat
```

启动器包含三个标签页：
| 标签页 | 功能 |
|--------|------|
| **▶ 启动** | 启动/停止 MCP Server、Web UI、Java 编辑器、WinUI 客户端 |
| **📦 模型管理** | 下载图像/音乐 AI 模型，实时进度追踪 |
| **⭐ 设置** | Python 路径、模型目录、端口配置 |

### WinUI 桌面客户端

```powershell
.\AetherForgeStudio-WinUI\publish\AetherForgeStudio.exe
```

### Python 引擎 / MCP Server

```powershell
python -m aetherforge.mcp_server    # MCP Server (76 tools)
python -m aetherforge.main          # Web UI (port 7890)
```

### 运行测试

```powershell
python -m pytest aetherforge/test/ -v   # Python 测试
mvn test                                # Java 测试
```

### Java 编辑器

```powershell
build.bat                             # 编译 + 打包
java -jar AetherForgeStudio-fat.jar   # 启动编辑器
```

## AI 模型下载器

内置于启动器的「模型管理」标签页，支持从 HuggingFace Hub 下载：

**图像生成模型（6个）**

| 模型 | HuggingFace ID | 参数 | 大小 |
|------|:-:|:-:|:-:|
| Anything V5 | stablediffusionapi/anything-v5 | 1.4B | ~2.5 GB |
| Stable Diffusion 1.5 | runwayml/stable-diffusion-v1-5 | 1.4B | ~2.5 GB |
| SDXL | stabilityai/stable-diffusion-xl-base-1.0 | 2.6B | ~7 GB |
| FLUX.1 Schnell | black-forest-labs/FLUX.1-schnell | 3.5B | ~8 GB |
| FLUX.1 Dev | black-forest-labs/FLUX.1-dev | 12B | ~24 GB |

**音乐/音效生成模型（5个）**

| 模型 | HuggingFace ID | 参数 | 大小 |
|------|:-:|:-:|:-:|
| MusicGen Small | facebook/musicgen-small | 300M | ~1.2 GB |
| MusicGen Medium | facebook/musicgen-medium | 1.5B | ~4 GB |
| MusicGen Large | facebook/musicgen-large | 3.3B | ~8 GB |
| MusicGen Melody | facebook/musicgen-melody | 1.5B | ~4 GB |
| AudioGen | facebook/audiogen-medium | 1.5B | ~4 GB |

下载后自动注册到引擎，可通过 API 激活使用。

---

## Agent Runtime

多 Agent 协作系统，核心能力：

| 组件 | 说明 |
|------|------|
| **Orchestrator** | 任务调度、Agent 生命周期管理 |
| **Explorer** | 只读探索世界状态，收集 Facts |
| **Planner** | 基于 Facts 制定可验证计划 |
| **Builder** | 执行计划、调用引擎工具修改世界 |
| **Verifier** | 独立验证，重新读取引擎状态 |
| **Critic** | 对抗性审查，寻找遗漏问题 |
| **Evidence Store** | 证据链验证，来源不可伪造 |
| **Commit Gate** | 事务门禁，验证通过才允许提交 |
| **Token Manager** | Token 预算控制，优雅暂停 |
| **Model Router** | OpenAI 兼容 API 抽象层 |
| **Art Director** | 美术风格一致性审查 |

配置模型路径（config.py）：

```python
model_endpoint = https://api.openai.com/v1
model_api_key = sk-...
model_name = gpt-4o
```

### 风险分级

| 级别 | 参与 Agent | 适用场景 |
|------|-----------|---------|
| L0 | Builder -> Check | 低风险操作 |
| L1 | Planner -> Builder -> Check | 中等复杂度 |
| L2 | Explorer -> Planner -> Builder -> Verifier -> Commit | 标准任务 |
| L3 | 全角色 + Human Approval | 高风险变更 |

## API 路由

| 路由 | 说明 |
|------|------|
| POST /api/tools/<tool> | 调用引擎工具 |
| GET /api/tools | 列出所有工具 |
| GET /api/observe | 获取世界快照 |
| GET /api/game-state | 游戏状态（前端渲染） |
| GET /api/models/list | 列出所有可用 AI 模型 |
| POST /api/models/download | 下载模型 |
| GET /api/models/downloads | 下载进度 |
| POST /api/models/select | 激活模型 |
| DELETE /api/models/delete | 删除模型 |

---

## 项目结构

```
D:\game/
├── aetherforge/               # Python 核心包
│   ├── agents/                # Agent Runtime (7 角色)
│   ├── api/                   # MCP 工具 + Flask 路由
│   ├── core/                  # 世界模型 + 实体定义
│   ├── runtime/               # 事务、快照、事件日志、权限
│   ├── validation/            # 证据链、提交门禁、验证器
│   ├── tools/                 # 模型管理器、网络检测、安全审查
│   ├── ai_engines/            # AI 引擎 (图像/音乐生成)
│   ├── test/                  # Python 测试（117+ 个）
│   ├── config.py              # 引擎配置
│   ├── main.py                # Web UI 入口
│   └── mcp_server.py          # MCP Server
├── AetherForgeStudio-WinUI/   # WinUI 3 桌面客户端 (.NET 9)
├── AetherForgeStudio-WebView2/# WebView2 客户端 (.NET 9)
├── src/                       # Java 代码
├── docs/                      # 设计文档
├── test/                      # Java 测试
├── launcher.bat               # 启动器快捷脚本
├── build.bat                  # Java 编译脚本
├── pom.xml                    # Maven 配置
├── pyproject.toml             # Python 项目配置
├── setup.py                   # Python 包安装
├── run_web.py                 # Web 服务器入口
└── run_tests.bat              # Python 测试
```

---

## 技术栈

- **Java 21** — 启动器 (Swing + FlatLaf 主题)
- **C# .NET 9** — WinUI 3 桌面客户端 (Windows App SDK)
- **Python 3.10+** — Agent Runtime, MCP Server, 世界模型, 验证引擎
- **协议** — MCP (Model Context Protocol), HTTP REST, WebSocket
- **AI** — OpenAI 兼容 API (支持 GPT, DeepSeek, Qwen 等)
- **AI 模型** — HuggingFace Diffusers + AudioCraft (图像/音乐生成)
- **测试** — pytest (117+ tests) + JUnit 5
