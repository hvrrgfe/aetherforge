@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo === AetherForge Studio Build Script ===
echo.

rem === Configuration ===
rem Set JAVA_HOME to your JDK 21+ path, or it will use the JDK from PATH
if "%JAVA_HOME%"=="" (
    if exist "D:\game\jdk21\jdk-21.0.11+10" (
        set JAVA_HOME=D:\game\jdk21\jdk-21.0.11+10
    ) else (
        echo [ERROR] JAVA_HOME not set and default path not found.
        echo Set JAVA_HOME to your JDK 21 installation, e.g.:
        echo   set JAVA_HOME=C:\Program Files\Java\jdk-21
        exit /b 1
    )
)

set BASE=%~dp0
set BUILD=%BASE%build
set SRC=%BASE%src
set LIBS=%BASE%flatlaf-3.5.4.jar
set JAR=%BASE%AetherForgeStudio.jar

echo JDK: %JAVA_HOME%
echo.

echo [1/4] Cleaning build directory...
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%BUILD%" 2>nul

echo [2/4] Extracting FlatLaf into build...
cd /d "%BUILD%"
"%JAVA_HOME%\bin\jar" xf "%LIBS%"

echo [3/4] Compiling Java sources...
cd /d "%BASE%"
"%JAVA_HOME%\bin\javac" -cp "%BUILD%" -d "%BUILD%" -encoding UTF8 ^
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
"%JAVA_HOME%\bin\jar" cfm "%JAR%" MANIFEST.MF -C . .

echo.
echo === Build complete ===
echo JAR: %JAR%
echo Run: "%JAVA_HOME%\bin\javaw" -jar "%JAR%"
