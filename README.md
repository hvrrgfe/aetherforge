# AetherForge

**AI-Native 游戏引擎 — 专为 AI Agent 设计**

[![GitHub](https://img.shields.io/badge/GitHub-hvrrgfe/aetherforge-181717?logo=github)](https://github.com/hvrrgfe/aetherforge)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)

AetherForge 是一个 AI-first 游戏引擎。**AI Agent 是主要用户**，人类只需监督。
引擎通过 MCP（Model Context Protocol）暴露 104 个工具，AI Agent 可以直接调用创建游戏世界、生成音乐、物理模拟等。

**GitHub**: https://github.com/hvrrgfe/aetherforge

---

## 快速开始

### 安装

```powershell
git clone https://github.com/hvrrgfe/aetherforge.git
cd aetherforge
install.bat
```

### 启动 MCP Server

```powershell
python -m aetherforge.mcp_server
```

输出：

```
AetherForge MCP Server v2.0.0 (direct mode)
  104 tools from engine reflection
  Waiting for MCP client...
```

MCP Server 启动后，AI 客户端（Codex CLI、Claude Desktop、Cursor 等）即可自动发现 104 个工具。

### 运行测试

```powershell
python -m pytest test/ -v
```

---

## 给 AI 客户端的 AGENTS.md 配置

在项目根目录的 AGENTS.md 中写入：

```markdown
# AetherForge AI Agent 指南

通过 MCP 连接本地引擎，启动方式：python -m aetherforge.mcp_server

暴露 104 个工具：

| 分类 | 工具 |
|------|------|
| 实体 | create_entity, modify_entity, remove_entity, get_entity, find_entities |
| 世界 | observe, set_weather, set_player, trigger_event |
| 规则 | create_rule, remove_rule |
| 任务 | create_quest, complete_quest_step, update_quest_state |
| 行为 | set_behavior, player_interact |
| 音乐 | init_music_gen, generate_music, generate_sound_effect, select_music_model |
| 图像 | init_image_gen, generate_image, generate_texture |
| 物理 | init_physics, add_physics_body, apply_force, ray_cast |
| 3D | set_3d_mesh, set_3d_transform, add_3d_light, set_3d_camera |
| Agent | agent_start_task, agent_get_status, agent_commit, agent_rollback |
| 模型 | list_all_models, download_selected_model, search_models |
| 事务 | commit_change, rollback_change, save_project, load_project |

所有工具返回 JSON。先 observe() 看世界状态，再 create_entity 等工具修改。
```

---

## AI Agent 操作示例

### 创建游戏世界

注意：以下 JSON 字符串推荐在 AI 客户端中直接自然语言描述，引擎工具会自动解析。

```python
create_entity(semantic_type="player", name="勇者", description="年轻的冒险者", capabilities=["move","interact"], state={"health":100})
create_entity(semantic_type="npc", name="铁匠", description="村庄铁匠，可打造武器", capabilities=["talk","trade"], state={"mood":"friendly"})
create_entity(semantic_type="key_item", name="龙泉剑", description="削铁如泥的宝剑", capabilities=["pick_up","use"], state={"attack":10})
observe()
```

### 设置规则和任务

```python
create_rule(when=["player:near(npc)"], then=["trigger_dialog()"], trigger_type="proximity")
create_quest("铁匠的委托", "帮铁匠取回工具", [{"step_id":"find_tool", "description":"在矿洞找到工具", "condition":"player.has_item(tool)"}])
```

### 生成游戏音乐

```python
init_music_gen()
select_music_model("musicgen-small")
generate_music(description="宁静的村庄背景音乐，笛子和吉他", duration=10.0)
generate_sound_effect(description="宝剑出鞘", duration=2.0)
play_music(name="bgm", file_path="assets/generated/music_xxx.wav")
```

### 事务回滚

```python
modify_entity("ent_player_id", {"state.health": 50})
rollback_change()
```

---

## 安装 AI 模型

### 音乐模型（MusicGen-Small）

```powershell
pip install -r requirements-audiocraft.txt
python -m aetherforge.cli model download facebook/musicgen-small
```

或通过 Python：

```python
from aetherforge.tools.model_manager import model_mgr
result = model_mgr.download("musicgen-small")
print(result)
```

可用音乐模型：

| 模型 | 参数量 | 大小 | 说明 |
|------|:------:|:----:|------|
| MusicGen Small | 300M | ~1.2 GB | 快速生成，推荐首选 |
| MusicGen Medium | 1.5B | ~4 GB | 均衡质量 |
| MusicGen Large | 3.3B | ~8 GB | 最高质量 |
| MusicGen Melody | 1.5B | ~4 GB | 旋律引导 |
| AudioGen | 1.5B | ~4 GB | 音效生成 |

### 图像模型（可选）

```python
from aetherforge.tools.model_manager import model_mgr
result = model_mgr.download("anything-v5")
print(result)
```

---

## Codex 提示词模板

以下提示词可直接在 Codex CLI 中使用：

### 创建 RPG 村庄

```
你是 AetherForge 游戏引擎的 AI 操作员。MCP Server 已在本地运行。
请帮我创建一个武侠小镇：
1. 创建玩家「剑客」
2. 创建 NPC「客栈老板」（可对话、可交易）
3. 创建道具「龙泉剑」（攻击力 +10）
4. 设置靠近触发对话的规则
5. 创建任务「寻找失落的宝剑」
```

### 生成游戏音乐

```
你现在通过 AetherForge MCP 连接了音乐生成引擎。
1. 初始化音乐引擎
2. 选择 musicgen-small 模型
3. 生成 15 秒战斗背景音乐
4. 生成 8 秒森林环境音效
5. 列出所有已生成资产
```

### 自主开发循环

```
你正在使用 AetherForge 引擎，通过 MCP 协议操作。
执行完整的自主开发循环：
1. 查看当前世界状态（observe）
2. 创建 3 个有相互关系的实体
3. 设置 NPC 行走行为
4. 生成一段游戏音乐
5. 提交变更
```

---

## 项目结构

```
aetherforge/
+-- agents/           AI Agent 运行时（7 种角色）
|   +-- roles/        Explorer, Planner, Builder, Verifier, Critic, Art Director
+-- api/              工具层 + MCP Server
|   +-- engine_v2.py  104 个工具
|   +-- mcp_server.py MCP 协议入口
+-- core/             世界模型 + 语义实体
+-- runtime/          游戏循环、事务、快照、事件日志
+-- validation/       证据链、提交门禁、检查器
+-- ai_engines/       AI 引擎（图像/音乐生成）
+-- tools/            模型管理器、导出、安全审查
+-- config.py         引擎配置
+-- cli.py            CLI 调试工具
```

---

## 技术栈

| 语言/工具 | 用途 |
|-----------|------|
| Python 3.10+ | 核心引擎、AI Agent、MCP Server |
| MCP | Model Context Protocol（AI 通信协议） |
| Diffusers / Audiocraft | AI 图像/音乐生成 |
| OpenAI 兼容 API | Agent Runtime 的 LLM 后端 |

---

## 链接

- GitHub: https://github.com/hvrrgfe/aetherforge
- Issues: https://github.com/hvrrgfe/aetherforge/issues
