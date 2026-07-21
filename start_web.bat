@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  AetherForge Studio - WebView2 ģʽ
echo ========================================
echo.

:: Start Flask server
echo [1/2] Starting AetherForge engine server...
start "AetherForge-Server" /MIN cmd /c "python run_web.py 2>&1"
if errorlevel 1 (
    echo [ERROR] Failed to start server. Make sure Python 3.10+ is installed.
    pause
    exit /b 1
)

:: Wait for server
echo   Waiting for server...
:wait
timeout /t 2 /nobreak >nul
powershell -Command "try{$r=Invoke-WebRequest -Uri 'http://127.0.0.1:7890/api/summary' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -eq 200){exit 0}}catch{}" 2>nul
if errorlevel 1 goto wait

echo   [OK] Server is running on http://127.0.0.1:7890

:: Open browser
echo [2/2] Opening AetherForge Studio in browser...
start http://127.0.0.1:7890
echo.
echo  AetherForge Studio is running!
echo  Dashboard: http://127.0.0.1:7890
echo  3D Viewer: http://127.0.0.1:7890/viewer_3d.html
echo.
echo  Close this window to stop the server.
pause

:: Kill server on exit
taskkill /f /fi "WINDOWTITLE eq AetherForge-Server" >nul 2>&1