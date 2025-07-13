@echo off
REM Quick development launch for Windows

echo Launching Real Estate Command Center (Development Mode)
echo ======================================================

set REAL_ESTATE_ENV=development
set REAL_ESTATE_DEBUG=1

cd desktop
python src\main.py

pause