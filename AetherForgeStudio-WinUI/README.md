# AetherForge Studio - WinUI 3 Desktop Client

Built with **WinUI 3 + Windows App SDK + .NET 9**.

## Prerequisites

- **Visual Studio 2022** (17.12 or later)
  - Workload: ".NET Desktop Development"
  - Workload: "Universal Windows Platform Development" (required for WinUI XAML compilation)
  - OR Visual Studio Build Tools with these workloads
- **Windows 10** version 1809 (build 17763) or later

## Build & Run

```powershell
# Using Visual Studio
Open AetherForgeStudio-WinUI\AetherForgeStudio.csproj in VS2022
Press F5 to build and run

# Using dotnet CLI (requires VS Build Tools with UWP workload)
cd AetherForgeStudio-WinUI
dotnet build -c Release
```

## Architecture

The WinUI client communicates with the Python backend via HTTP/WebSocket:

```
WinUI Client (C#)
  |  HTTP REST + WebSocket
  v
Python AetherForge Engine (port 7890)
  |  MCP / Agent Runtime
  v
World Model + AI Engines
```

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | World overview with entity/rule/quest counts |
| Agent Workspace | `/agents` | Task input, agent status cards, progress bar |
| World Viewer | `/world` | Three.js 3D preview via WebView2 |
| Verification | `/verify` | Evidence chain, commit/rollback controls |

## Connecting to Backend

1. Start the Python engine:
   ```powershell
   cd D:\game\aetherforge
   python -m aetherforge.main
   ```
2. Start the WinUI client - it connects to `http://127.0.0.1:7890` by default