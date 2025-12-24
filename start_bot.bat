@echo off
title Tongue Twister Bot
color 0A

echo ========================================
echo   TONGUE TWISTER BOT - STARTING
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [INFO] Python Version:
python --version
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo [WARNING] Please create .env file with DISCORD_TOKEN
    echo [WARNING] Continuing anyway...
    echo.
) else (
    echo [OK] .env file found
    echo.
)

REM Check if required directories exist
if not exist data (
    echo [INFO] Creating data directory...
    mkdir data
    echo [OK] Data directory created
    echo.
) else (
    echo [OK] Data directory exists
    echo.
)

REM Check if database exists
if exist data\twister.db (
    echo [OK] Database file exists
    echo.
) else (
    echo [INFO] Database will be created on first run
    echo.
)

REM Check if virtual environment exists (optional)
if exist venv (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
)

REM Show environment info
echo [DEBUG] Current Directory: %CD%
echo [DEBUG] Python Path: 
where python
echo.

REM Check for required packages
echo [INFO] Checking required packages...
python -c "import discord; print('[OK] discord.py installed')" 2>nul || echo [WARNING] discord.py not found
python -c "import whisper; print('[OK] whisper installed')" 2>nul || echo [WARNING] whisper not found
python -c "import aiosqlite; print('[OK] aiosqlite installed')" 2>nul || echo [WARNING] aiosqlite not found
echo.

echo ========================================
echo   STARTING BOT...
echo ========================================
echo.
echo [INFO] Press Ctrl+C to stop the bot
echo.

REM Run the bot
python main.py

REM If we get here, the bot exited
echo.
echo ========================================
echo   BOT STOPPED
echo ========================================
echo.
echo [INFO] Exit code: %ERRORLEVEL%
echo.

pause

