@echo off
chcp 65001 >nul
title 智能化健康管理系统

echo ╔══════════════════════════════════════╗
echo ║   智能化健康管理系统 — 一键启动      ║
echo ╚══════════════════════════════════════╝
echo.

REM ========== 配置路径 ==========
set MYSQL_DIR=E:\d\MySQL\MySQL Server 8.0
set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend
set MYSQL_PORT=3306
set API_PORT=8000
set FRONT_PORT=5173

REM ========== 1. 检查并启动 MySQL ==========
echo [1/4] 检查 MySQL 状态...
"%MYSQL_DIR%\bin\mysql.exe" -u root -proot --protocol=TCP -P %MYSQL_PORT% -e "SELECT 1;" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo   ✓ MySQL 已在运行
) else (
    echo   ⏳ 正在启动 MySQL...
    start /B "" "%MYSQL_DIR%\bin\mysqld.exe" --defaults-file="%MYSQL_DIR%\my.ini"

    set WAIT_COUNT=0
    :wait_mysql
    set /a WAIT_COUNT+=1
    if %WAIT_COUNT% GTR 15 (
        echo   ✗ MySQL 启动超时，请手动启动
        pause
        exit /b 1
    )
    "%MYSQL_DIR%\bin\mysql.exe" -u root -proot --protocol=TCP -P %MYSQL_PORT% -e "SELECT 1;" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        timeout /t 1 /nobreak >nul
        goto wait_mysql
    )
    echo   ✓ MySQL 已启动
)

REM ========== 2. 启动后端服务 ==========
echo [2/4] 启动后端服务 (端口 %API_PORT%)...

cd /d "%BACKEND_DIR%"

REM 检查依赖
python -c "import fastapi" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   ⏳ 首次运行，安装后端依赖...
    pip install -r requirements.txt
)

start "HealthBackend" cmd /c "uvicorn main:app --host 0.0.0.0 --port %API_PORT% --reload"

echo   ⏳ 等待后端启动...
set WAIT_COUNT=0
:wait_backend
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GTR 12 (
    echo   ⚠ 后端启动可能较慢
    goto skip_backend
)
timeout /t 1 /nobreak >nul
>nul 2>&1 curl -s http://127.0.0.1:%API_PORT%/api/health
if %ERRORLEVEL% NEQ 0 goto wait_backend
:skip_backend
echo   ✓ 后端已启动

REM ========== 3. 启动前端服务 ==========
echo [3/4] 启动前端开发服务器 (端口 %FRONT_PORT%)...

cd /d "%FRONTEND_DIR%"

if not exist "node_modules" (
    echo   ⏳ 首次运行，安装前端依赖...
    call npm install
)

start "HealthFrontend" cmd /c "npx vite --port %FRONT_PORT%"

echo   ⏳ 等待前端启动...
set WAIT_COUNT=0
:wait_frontend
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GTR 15 (
    echo   ⚠ 前端启动可能较慢
    goto skip_frontend
)
timeout /t 1 /nobreak >nul
>nul 2>&1 curl -s http://127.0.0.1:%FRONT_PORT%/
if %ERRORLEVEL% NEQ 0 goto wait_frontend
:skip_frontend
echo   ✓ 前端已启动

REM ========== 4. 打开浏览器 ==========
echo [4/4] 打开应用...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:%FRONT_PORT%/

echo.
echo ╔══════════════════════════════════════╗
echo ║   ✅ 全部启动完成！                   ║
echo ║                                      ║
echo ║   前端页面: http://localhost:%FRONT_PORT%  ║
echo ║   API 文档: http://localhost:%API_PORT%/docs  ║
echo ║                                      ║
echo ║   关闭此窗口不会关闭服务              ║
echo ║   如需停止，请关闭对应的命令行窗口    ║
echo ╚══════════════════════════════════════╝
echo.
pause
