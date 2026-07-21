@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [AetherForgeStudio] 正在编译并启动...
dotnet run
if %errorlevel% neq 0 (
    echo.
    echo [错误] 请先安装 .NET 9 SDK:
    echo         https://dotnet.microsoft.com/download/dotnet/9.0
    pause
)
pause
