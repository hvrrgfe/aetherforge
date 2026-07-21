# AetherForge

**AI-Native Game Creation & Runtime System**

三套实现：

| 目录 | 语言 | 功能 | 状态 |
|------|------|------|------|
| \etherforge/\ | Python 3.10+ | 核心引擎 (67 tools, MCP, Flask, CLI) | ✅ 完整 |
| \src/\ | Java 21 (Swing + FlatLaf) | 桌面编辑器 (场景/检查器/视口) | ✅ 完整 |
| ~~\AetherForgeStudio-WinUI/\~~ | C# .NET 9 (WinUI) | 桌面客户端 | ❌ 已废弃 |

## 快速开始

### Python 引擎

\\powershell
pip install aetherforge
python -m aetherforge.mcp_server    # MCP Server (推荐)
python -m aetherforge.main          # Web UI (port 7890)
python -m aetherforge.cli           # CLI
\
### Java 编辑器

\\powershell
build.bat          # 编译 + 打包 fat JAR
java -jar AetherForgeStudio-fat.jar   # 启动
\
## 项目结构

\aetherforge/               # Python 引擎
├── api/                   # 工具层 (EngineTools, engine_v2)
├── core/                  # 语义世界模型 (WorldModel, SemanticEntity)
├── runtime/               # 运行时 (game_loop, physics, audio)
├── ai_engines/            # AI 生成 (image_gen, music_gen)
├── renderer/              # 3D 场景图
├── tools/                 # 模型管理
└── test/                  # 测试

src/                       # Java 桌面编辑器
├── com/aetherforge/
│   ├── AetherForgeStudio.java  # 入口
│   ├── model/                  # Scene, Entity, Command 模式
│   ├── ui/                     # MainWindow, Viewport, Inspector
│   └── util/                   # Colors, Theme, I18n, SceneSerializer
└── test/                  # 单元测试
\
## 测试

\\powershell
# Python
python -m aetherforge.test.test_runner

# Java
cd src && javac -cp ../flatlaf-3.5.4.jar -d ../build ../test/com/aetherforge/**/*.java
\
## 功能

- **语义实体系统** — 每个实体有 semantic_type, description, capabilities, relationships
- **世界模型** — 实体 CRUD + 规则引擎 + 任务系统 + NPC 行为
- **物理引擎** — 基于 pymunk 的 2D 物理
- **音频引擎** — 基于 pygame 的语义音频播放
- **AI 生成** — 图像 (diffusers) + 音乐 (audiocraft)
- **3D 场景图** — Three.js 浏览器渲染
- **Java 桌面编辑器** — 拖拽编辑 + 撤销/重做 + 多主题 + 中英双语

## 许可

MIT
