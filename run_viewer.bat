@echo off
chcp 65001 >nul
setlocal
if "%JAVA_HOME%"=="" (
    set JAVA=java
) else (
    set JAVA="%JAVA_HOME%\bin\java"
)
echo === AetherForge Game Viewer ===
set JAR=%~dp0AetherForgeStudio-fat.jar
if not exist "%JAR%" (
    echo [ERROR] AetherForgeStudio-fat.jar not found!
    echo Run build.bat first.
    pause
    exit /b 1
)
%JAVA% -cp "%JAR%" com.aetherforge.ui.GameViewer %*
if errorlevel 1 (
    echo.
    pause
)
