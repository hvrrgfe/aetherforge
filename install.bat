@echo off
chcp 65001 >nul
title AetherForge 安装程序
cd /d "%~dp0"

echo ========================================
echo   AetherForge v2.0.0 - 安装程序
echo ========================================
echo.

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python。请安装 Python 3.10+:
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

:: 检查 Python 版本
python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [错误] 需要 Python 3.10 或更高版本
    pause
    exit /b 1
)
echo [完成] Python 版本检查通过

:: 升级 pip
echo.
echo [1/3] 正在升级 pip...
python -m pip install --upgrade pip -q

:: 安装核心依赖
echo.
echo [2/3] 正在安装核心依赖...
pip install -r requirements.txt

:: 安装 aetherforge 包
echo.
echo [3/3] 正在安装 aetherforge 包...
pip install -e . --no-deps

:: 可选引擎
echo.
echo 可选引擎:
echo   物理引擎:  pip install pymunk
echo   音频引擎:  pip install pygame
echo   AI 图片:   pip install torch diffusers transformers
echo   AI 音乐:   pip install torch audiocraft

echo.
echo ========================================
echo   安装完成！
echo.
echo   启动 MCP 服务器:
echo     python -m aetherforge.mcp_server
echo.
echo   运行测试:
echo     python -m pytest test/ -v
echo ========================================
pause
