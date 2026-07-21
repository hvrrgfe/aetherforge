@echo off
cd /d "%~dp0"
echo Starting AetherForge MCP Server...
python -m aetherforge.mcp_server
pause
