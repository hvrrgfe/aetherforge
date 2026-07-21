@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === AetherForge Launcher ===
echo.
java -cp "flatlaf-3.5.4.jar;gson-2.11.0.jar;AetherForgeStudio-fat.jar" com.aetherforge.launcher.AetherForgeLauncher
pause