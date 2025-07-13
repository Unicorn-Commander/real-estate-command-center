@echo off
REM Launch script for Real Estate Command Center on Windows

echo ========================================
echo   Real Estate Command Center Launcher
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [OK] Python found

REM Check if we're in the right directory
if not exist "desktop\src\main.py" (
    echo [ERROR] Cannot find desktop\src\main.py
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Menu
echo.
echo Select launch mode:
echo 1) Development (debug enabled)
echo 2) Production (optimized)
echo 3) Exit
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto development
if "%choice%"=="2" goto production
if "%choice%"=="3" goto exit

echo [ERROR] Invalid choice
pause
exit /b 1

:development
echo.
echo Launching in Development mode...
set REAL_ESTATE_ENV=development
set REAL_ESTATE_DEBUG=1
cd desktop
python src\main.py
goto end

:production
echo.
echo Launching in Production mode...
set REAL_ESTATE_ENV=production
set REAL_ESTATE_DEBUG=0
cd desktop
python src\main.py
goto end

:exit
echo Exiting...
exit /b 0

:end
pause