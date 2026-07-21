# AetherForge

**AI-Native 游戏创作与运行时系统**

| 语言 | 模块 | 功能 | 状态 |
|------|------|------|------|
| Python 3.10+ | `aetherforge/` | 核心引擎 (76+ tools, MCP, Agent Runtime) | ✅ 完整 |
| C# .NET 9 | `AetherForgeStudio-WinUI/` | 桌面客户端 (WinUI 3, MVVM, WebSocket) | ✅ 完整 |
| Java 21 | `src/` | 桌面编辑器 (Swing + FlatLaf) | ✅ 完整 |

## 快速开始

### WinUI 桌面客户端（推荐）

`powershell
cd AetherForgeStudio-WinUI
dotnet run
`

启动前需安装 .NET 9 SDK：https://dotnet.microsoft.com/download/dotnet/9.0

### Python 引擎 / MCP Server

`powershell
python -m aetherforge.mcp_server    # MCP Server (76 tools)
python -m aetherforge.main          # Web UI (port 7890)
`

### 运行测试

`powershell
python -m pytest aetherforge/test/ -v
`

### Java 编辑器

`powershell
build.bat                             # 编译 + 打包
java -jar AetherForgeStudio-fat.jar   # 启动
`

## Agent Runtime (新增)

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

配置模型路由（`config.py`）：

`python
model_endpoint = https://api.openai.com/v1
model_api_key = sk-...
model_name = gpt-4o
`

### 风险分级

| 级别 | 参与 Agent | 适用场景 |
|------|-----------|---------|
| L0 | Builder → Check | 低风险操作 |
| L1 | Planner → Builder → Check | 中等复杂度 |
| L2 | Explorer → Planner → Builder → Verifier → Commit | 标准任务 |
| L3 | 全角色 + Human Approval | 高风险变更 |

## 验证器模块

| 验证器 | 说明 |
|--------|------|
| AssertionEngine | 实体存在、属性匹配 |
| SceneTestRunner | 场景自动化测试 |
| InvariantChecker | 世界状态一致性检查 |
| ConsistencyValidator | 关系完整性、引用有效性 |
| QuestReachabilityValidator | 任务前置条件、可达性 |
| BehaviorChecker | 行为绑定、参数完整性 |
| AssetChecker | 资源文件存在、格式正确 |
| PhysicsChecker | 碰撞体、质量、位置重叠 |

## 项目管理工具

| 命令 | 说明 |
|------|------|
| `start_ui.bat` | 启动 WinUI 桌面客户端 |
| `start_server.bat` | 启动 Python MCP Server |
| `run_tests.bat` | 运行 96 个测试 |

## 项目结构

`
D:\game\aetherforge\
├── aetherforge/              # Python 核心包
│   ├── agents/               # Agent Runtime (5 角色)
│   │   └── roles/            # Explorer / Planner / Builder / Verifier / Critic
│   ├── api/                  # MCP 工具定义 (engine_v2.py)
│   ├── core/                 # 世界模型 + 实体定义
│   ├── runtime/              # 事务、快照、事件日志、权限
│   ├── validation/           # 证据链、提交门禁、8 个验证器
│   ├── tools/                # 模型管理器、网络检测、安全审查
│   ├── ai_engines/           # AI 引擎 (图片/音乐生成)
│   └── test/                 # 96 个测试
├── AetherForgeStudio-WinUI/  # WinUI 3 桌面客户端
│   ├── Pages/                # 9 个页面 (Dashboard/AgentWorkspace/World/...)
│   ├── Controls/             # AgentStatusCard / EvidencePanel / TransactionBar
│   ├── Services/             # HTTP + WebSocket 客户端
│   ├── ViewModels/           # 5 个 ViewModel (MVVM)
│   ├── Models/               # 数据模型
│   └── Strings/              # en-US + zh-CN 双语资源
├── src/                      # Java 编辑器 (Swing)
├── docs/                     # 设计文档
├── start_ui.bat              # 启动 WinUI
├── start_server.bat          # 启动 MCP Server
└── run_tests.bat             # 运行测试
`

## 技术栈

- **Python 3.10+** — Agent Runtime, MCP Server, 世界模型, 验证引擎
- **C# .NET 9** — WinUI 3 桌面客户端 (Windows App SDK 2.3.1)
- **Java 21** — Swing 编辑器 (FlatLaf 主题)
- **协议** — MCP (Model Context Protocol), HTTP REST, WebSocket
- **AI** — OpenAI 兼容 API (支持 GPT, DeepSeek, Qwen 等)
- **测试** — pytest (96 tests, 全部通过)
