@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo === AetherForge Studio Build Script ===
echo.

set JDK=D:\game\jdk21\jdk-21.0.11+10
set BASE=%~dp0
set BUILD=%BASE%build
set SRC=%BASE%src
set LIBS=%BASE%flatlaf-3.5.4.jar
set JAR=%BASE%AetherForgeStudio.jar

echo [1/4] Cleaning build directory...
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%BUILD%" 2>nul

echo [2/4] Extracting FlatLaf into build...
cd /d "%BUILD%"
"%JDK%\bin\jar" xf "%LIBS%"

echo [3/4] Compiling Java sources...
cd /d "%BASE%"
"%JDK%\bin\javac" -cp "%BUILD%" -d "%BUILD%" -encoding UTF8 ^
    "%SRC%\com\aetherforge\AetherForgeStudio.java" ^
    "%SRC%\com\aetherforge\model\*.java" ^
    "%SRC%\com\aetherforge\ui\*.java" ^
    "%SRC%\com\aetherforge\util\*.java"
if errorlevel 1 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo [4/4] Packaging JAR...
cd /d "%BUILD%"
echo Main-Class: com.aetherforge.AetherForgeStudio > MANIFEST.MF
"%JDK%\bin\jar" cfm "%JAR%" MANIFEST.MF -C . .

echo.
echo === Build complete: AetherForgeStudio.jar ===
echo Run: "%JDK%\bin\javaw" -jar "%JAR%"
