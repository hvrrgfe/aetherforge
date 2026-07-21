@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Running AetherForge tests...
python -m pytest test/ -v
pause
