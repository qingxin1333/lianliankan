@echo off
chcp 65001 >nul
echo ========================================
echo       Lianliankan Auto Script
echo ========================================
echo.
echo Usage:
echo - Default: 0.1s click interval
echo - Fast: 0.05s click interval  
echo - Ultra Fast: 0.02s click interval
echo - Slow: 0.2s click interval
echo.
echo Please select mode:
echo [1] Default (0.1s)
echo [2] Fast (0.05s)
echo [3] Ultra Fast (0.02s)
echo [4] Slow (0.5s)
echo [5] Custom Speed
echo [6] Exit
echo.
set /p choice=Enter choice (1-6): 

if "%choice%"=="1" (
    set speed=0.1
    goto run
)
if "%choice%"=="2" (
    set speed=0.05
    goto run
)
if "%choice%"=="3" (
    set speed=0.02
    goto run
)
if "%choice%"=="4" (
    set speed=0.2
    goto run
)
if "%choice%"=="5" (
    set /p speed=Enter click interval (0.01-2.0s): 
    goto run
)
if "%choice%"=="6" (
    exit
)
echo Invalid choice, please restart
pause
exit

:run
echo.
echo Starting Lianliankan Auto Script...
echo Click speed: %speed%s
echo Press ESC to stop
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo Using virtual environment Python
    .venv\Scripts\python.exe lianliankan.py %speed%
) else (
    echo Virtual environment not found, installing dependencies...
    pip install -r requirements.txt
    echo Using system Python
    python lianliankan.py %speed%
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo        Script Completed!
    echo ========================================
) else (
    echo.
    echo Script exited with code: %ERRORLEVEL%
    echo Please ensure QQ Lianliankan game is running
)

if exist ".venv\Scripts\activate.bat" (
    call conda deactivate 2>nul || deactivate 2>nul
)

echo.
pause
