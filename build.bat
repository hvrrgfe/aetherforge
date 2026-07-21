@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo === AetherForge Studio Build Script ===
echo.

rem -- Configuration --
if "%JAVA_HOME%"=="" (
    if exist "C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot" (
        set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot
    ) else (
        echo [ERROR] JAVA_HOME not set. Set to your JDK 21+ path.
        exit /b 1
    )
)

set BASE=%~dp0
set BUILD=%BASE%build
set DIST=%BASE%dist-new
set SRC=%BASE%src
set LIBS=%BASE%flatlaf-3.5.4.jar;%BASE%gson-2.11.0.jar

echo JDK: %JAVA_HOME%
echo.

echo [1/5] Cleaning...
if exist "%BUILD%" rmdir /s /q "%BUILD%"
if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%BUILD%\classes" 2>nul

echo [2/5] Compiling...
cd /d "%BASE%"
dir /s /B "%SRC%\*.java" > "%BUILD%\sources.txt"
"%JAVA_HOME%\bin\javac" -cp "%LIBS%" -d "%BUILD%\classes" -encoding UTF8 @"%BUILD%\sources.txt"
if errorlevel 1 ( echo [ERROR] Compilation failed! & exit /b 1 )

echo [3/5] Creating fat JAR...
cd /d "%BUILD%\classes"
"%JAVA_HOME%\bin\jar" xf "%BASE%\flatlaf-3.5.4.jar" 2>nul
"%JAVA_HOME%\bin\jar" xf "%BASE%\gson-2.11.0.jar" 2>nul
cd /d "%BASE%"
echo Main-Class: com.aetherforge.AetherForgeStudio > "%BUILD%\MANIFEST.MF"
"%JAVA_HOME%\bin\jar" cfm "%BASE%AetherForgeStudio-fat.jar" "%BUILD%\MANIFEST.MF" -C "%BUILD%\classes" .
if errorlevel 1 ( echo [ERROR] JAR creation failed! & exit /b 1 )

echo [4/5] Generating icon (if needed)...
if not exist "%BASE%app-icon.ico" (
    echo [WARN] No icon found, using default
)

echo [5/5] Creating Windows EXE (jpackage)...
mkdir "%BASE%\dist-input" 2>nul
copy /Y "%BASE%AetherForgeStudio-fat.jar" "%BASE%\dist-input\" >nul
"%JAVA_HOME%\bin\jpackage" --type app-image -n AetherForgeStudio ^
    --main-jar AetherForgeStudio-fat.jar ^
    --main-class com.aetherforge.AetherForgeStudio ^
    --input "%BASE%\dist-input" --dest "%DIST%" ^
    --icon "%BASE%app-icon.ico" ^
    --java-options "-Dfile.encoding=UTF-8"
if errorlevel 1 echo [WARN] jpackage skipped

echo.
echo === Build Complete ===
echo JAR: %BASE%AetherForgeStudio-fat.jar

rem Cleanup
rmdir /s /q "%BASE%\dist-input" 2>nul
del "%BASE%MANIFEST.MF" 2>nul
