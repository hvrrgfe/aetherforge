@echo off
title AetherForge Installer
cd /d "%%~dp0"

echo ========================================
echo   AetherForge v2.0.0 - 安装程序
echo ========================================
echo.

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+:
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

:: 检查 Python 版本
python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10+ required.
    pause
    exit /b 1
)
echo [OK] Python version OK.

:: 可选升级 pip
echo.
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip -q

:: 安装核心依赖
echo.
echo [2/4] Installing core dependencies...
pip install -r requirements.txt

:: 安装 aetherforge 包本身（可编辑模式）
echo.
echo [3/4] Installing aetherforge package...
pip install -e . --no-deps

:: 可选: 物理引擎
echo.
echo [4/4] Optional engines:
echo   Physics:  pip install pymunk
echo   Audio:    pip install pygame
echo   AI Image: pip install torch diffusers transformers
echo   AI Music: pip install torch audiocraft
echo   Full:     pip install -e ".[full]"

echo.
echo ========================================
echo   安装完成！
echo.
echo   启动方式:
echo     MCP Server:  python -m aetherforge.mcp_server
echo     CLI:         python -m aetherforge.cli
echo     Web UI:      python -m aetherforge.main
echo     Test:        python -m aetherforge.test.test_runner
echo ========================================
pause