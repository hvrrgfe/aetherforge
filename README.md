<p align="center">
  <img src="https://img.shields.io/badge/Java-21-ED8B00?style=flat&logo=openjdk&logoColor=white" alt="Java 21">
  <img src="https://img.shields.io/badge/FlatLaf-3.5.4-4051b5?style=flat" alt="FlatLaf">
  <img src="https://img.shields.io/github/v/release/hvrrgfe/aetherforge?style=flat" alt="Release">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat" alt="License">
</p>

# ⚒️ AetherForge Studio

> **2D 游戏场景编辑器** — Java + Swing + FlatLaf 桌面端  
> 暗色/亮色/Dracula 主题切换 · 中英文双语 · 撤销/重做 · 场景序列化

---

## 📸 界面预览

```
┌──────────────────────────────────────────────────────┐
│  ☰  ◆ AetherForge Studio          ─  □  ✕         │  ← 无边框标题栏
├─────────┬──────────────────────────┬────────────────┤
│         │  [选择] [移动] [缩放] ⚙  │  属性          │
│ 场景树   │                          │  ID: ent_abc   │
│  ├ Scene │    2D 视口              │  类型: player  │
│  ├ Player│    (拖拽平移/滚轮缩放)   │  名称: 玩家   │
│  ├ Goblin│    (右键菜单)           │  位置: 0   0  │
│  ├ Merchant│  (Shift+S 网格吸附)   │  尺寸: 32  32 │
│  ├ Chest │                          │  颜色: ■      │
│  └ Oak Tree│                        │  圆形: □      │
│         │                          │  玩家: □      │
│         ├──────────────────────────┤               │
│         │ 输出控制台                │               │
│         │ [HH:mm:ss] 创建实体: ... │               │
├─────────┴──────────────────────────┴────────────────┤
│  就绪  │  中文  暗色                                 │  ← 状态栏
└──────────────────────────────────────────────────────┘
```

---

## ✨ 功能特性

### 🎨 界面设计
- **无边框窗口** — 自定义标题栏，双击最大化/还原，拖拽移动，边缘缩放
- **三栏布局** — 场景树 / 视口+控制台 / 属性检查器（拖动分栏）
- **三套主题** — 暗色（Codex 风格）、亮色、Dracula 紫黑，实时切换
- **CJK 字体优化** — 微软雅黑 → 黑体 → 宋体 Fallback，消除方框

### 🖥️ 2D 视口
- 鼠标拖拽 **平移** 场景，滚轮 **缩放**（5%–2000%）
- **网格吸附** (Shift+S 切换)
- **工具模式** — 选择 / 移动 / 缩放
- **悬停高亮** + **选中光晕**（GLOW_OUTER/GLOW_INNER）
- **动画效果** — 实体出现渐变、删除淡出
- 右键上下文菜单 — 创建/删除实体

### 📦 实体系统
- **6 种预设** — Player、Goblin、Merchant、Chest、Oak Tree 及自定义
- **属性编辑** — ID、类型、名称、位置、尺寸、颜色、圆形标记、玩家标记
- **多选支持** — Ctrl+点击多选
- **唯一 ID** — UUID 自动生成（6 位短 ID）

### ↩️ 撤销/重做
- 命令模式（Command Pattern），100 步历史栈
- 创建/删除实体可撤销/重做

### 🌐 国际化
- **简体中文 / English** 实时切换（Ctrl+L）
- **三套主题** 实时切换（Ctrl+T）
- 界面、菜单、日志、状态栏全量覆盖

### 💾 场景管理
- **JSON 序列化** — 场景保存/加载（手写解析器，零依赖）
- 文件对话框（Ctrl+S 保存 / Ctrl+O 加载）
- 新建场景（Ctrl+Shift+N）

---

## 🚀 快速开始

### 下载运行

从 [Releases](https://github.com/hvrrgfe/aetherforge/releases) 下载 `AetherForgeStudio-v1.2.0-win64.zip`：

```bash
# 解压后直接运行（已捆绑 JRE 21，无需安装 Java）
AetherForgeStudio.exe
```

### 从源码构建

**前置要求：** JDK 21+、Maven 3.9+

```bash
git clone https://github.com/hvrrgfe/aetherforge.git
cd aetherforge

# 构建 fat JAR（含 FlatLaf 依赖）
mvn clean package -B

# 运行
java -jar target/aetherforge-studio-1.2.0.jar
```

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Ctrl+S` | 保存场景 |
| `Ctrl+O` | 加载场景 |
| `Ctrl+N` | 新建实体 |
| `Ctrl+Shift+N` | 新建场景 |
| `Ctrl+L` | 切换语言（中文/English） |
| `Ctrl+T` | 切换主题（暗色/亮色/Dracula） |
| `F5` | 重置相机位置 |
| `Delete` | 删除选中实体 |
| `Shift+S` | 切换网格吸附 |

---

## 🧱 项目结构

```
src/com/aetherforge/
├── AetherForgeStudio.java    # 入口：FlatLaf 初始化 + CJK 字体
├── model/
│   ├── Command.java           # 命令接口
│   ├── CreateEntityCommand.java
│   ├── DeleteEntityCommand.java
│   ├── Entity.java            # 实体数据模型
│   ├── Scene.java             # 场景模型 + 撤销/重做栈
│   └── SceneListener.java     # 场景事件监听器
├── ui/
│   ├── InspectorController.java  # 属性检查器面板
│   ├── LayoutBuilder.java        # 布局构建器（标题栏/状态栏/分栏）
│   ├── MainWindow.java           # 主窗口协调器
│   ├── SceneController.java      # 场景树控制器
│   └── ViewportPanel.java        # 2D 视口渲染 + 鼠标交互
└── util/
    ├── Colors.java             # 主题色 + 调色板
    ├── DarkScrollBarUI.java    # 自定义暗色滚动条
    ├── EntityIcon.java         # 实体图标渲染
    ├── I18n.java               # 国际化（中/英双语）
    ├── SceneSerializer.java    # JSON 序列化/反序列化
    └── Theme.java              # 主题切换管理
```

---

## ⚙️ 技术栈

| 技术 | 用途 |
|------|------|
| Java 21 | 语言 / JVM |
| Swing | UI 框架 |
| FlatLaf 3.5.4 | 跨平台外观主题 |
| Maven | 构建 + 依赖管理 |
| JLink + JPackage | 自定义运行时 + EXE 打包 |
| Temurin 21 | 捆绑运行时 |

---

## 📄 许可

MIT License © 2026 hvrrgfe
