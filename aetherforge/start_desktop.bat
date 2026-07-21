@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  AetherForge Studio - Desktop 模式
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required
    pause
    exit /b 1
)

:: Start Flask server
echo [1/3] Starting AetherForge engine server...
taskkill /f /fi "WINDOWTITLE eq AetherForge-Server" >nul 2>&1
start "AetherForge-Server" /MIN cmd /c "python run_web.py 2>&1"

:: Wait for server
echo   Waiting for server...
:wait
timeout /t 2 /nobreak >nul
powershell -Command "try{$r=Invoke-WebRequest -Uri 'http://127.0.0.1:7890/api/summary' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -eq 200){exit 0}}catch{}" 2>nul
if errorlevel 1 goto wait

echo   [OK] Server ready!

:: Start WebView2 client
echo [2/3] Starting AetherForge Studio client...
cd AetherForgeStudio-WebView2

if not exist "bin\Release\net9.0-windows10.0.26100.0\win-x64\publish\AetherForgeStudio.exe" (
    echo   Building client...
    dotnet publish -c Release --self-contained -r win-x64 2>&1 | findstr /V "info\|message\|确定"
)

if exist "bin\Release\net9.0-windows10.0.26100.0\win-x64\publish\AetherForgeStudio.exe" (
    start "" "bin\Release\net9.0-windows10.0.26100.0\win-x64\publish\AetherForgeStudio.exe"
    echo   [OK] Client started!
) else (
    echo   [INFO] Opening browser instead...
    start http://127.0.0.1:7890
)

echo.
echo [3/3] Ready!
echo   Dashboard: http://127.0.0.1:7890
echo   3D Viewer: http://127.0.0.1:7890/viewer_3d.html
echo.
echo  Press Ctrl+C or close this window to stop.
echo.

:: Wait for user to close
pause

:: Cleanup
echo Shutting down...
taskkill /f /fi "WINDOWTITLE eq AetherForge-Server" >nul 2>&1
taskkill /f /im "AetherForgeStudio.exe" >nul 2>&1
echo Done.