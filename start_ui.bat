@echo off
cd /d "%~dp0AetherForgeStudio-WinUI"
echo [AetherForgeStudio] Building and starting...
dotnet run
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Make sure .NET 9 SDK is installed:
    echo         https://dotnet.microsoft.com/download/dotnet/9.0
    pause
)
pause
