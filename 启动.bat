@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  正在清理 8765 端口上的旧服务...

powershell -NoProfile -Command ^
  "$conns = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue;" ^
  "if ($conns) {" ^
  "  $conns | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {" ^
  "    try { Stop-Process -Id $_ -Force -ErrorAction Stop; Write-Host ('  已结束进程 PID ' + $_) } catch {}" ^
  "  }" ^
  "} else { Write-Host '  端口空闲' }"

timeout /t 1 /nobreak >nul

echo.
echo  面试复习系统启动中（支持编辑保存到代码文件）
echo  浏览器打开: http://127.0.0.1:8765/
echo  黑窗口请保持打开；按 Ctrl+C 可停止
echo.
echo  如何确认不是旧服务：
echo  打开后若双击编辑、失焦能提示「已保存到代码文件」，就是新服务。
echo  若仍提示保存失败，关掉所有黑窗口后再点一次本 bat。
echo.

start "" "http://127.0.0.1:8765/"
python scripts\dev_server.py
if errorlevel 1 (
  echo.
  echo  启动失败。请确认已安装 Python，且本目录存在 scripts\dev_server.py
  pause
)
