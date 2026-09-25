@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  面试复习系统已启动
echo  浏览器打开: http://127.0.0.1:8765/
echo  按 Ctrl+C 可停止
echo.
start "" "http://127.0.0.1:8765/"
python -m http.server 8765
