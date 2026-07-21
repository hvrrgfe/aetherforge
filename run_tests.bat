@echo off
cd /d "%~dp0"
echo Running AetherForge tests...
python -m pytest aetherforge/test/ -v
pause
