@echo off
:: Đường dẫn đến thư mục Topmost
set "APPDIR=D:\Code\Topmost"

:: Kiểm tra quyền admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Request Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Chuyển đến thư mục
cd /d "%APPDIR%"

:: Chạy script .pyw bằng pythonw.exe (ẩn console)
start "" pythonw.exe "%APPDIR%\topmost.pyw"
