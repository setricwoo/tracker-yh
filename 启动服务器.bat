@echo off
chcp 65001 >nul
title 中东地缘跟踪器 - 本地服务器
echo ========================================
echo  银华基金 - 中东地缘局势跟踪器
echo ========================================
echo.
echo 正在启动本地服务器...
echo 访问地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.
python -m http.server 8080
pause
