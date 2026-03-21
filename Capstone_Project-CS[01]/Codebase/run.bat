@echo off
REM Quick start script for CV Creation Using LLM (Windows)

echo ======================================
echo CV Creation Using LLM - Quick Start
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import langchain" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed!
    echo.
) else (
    echo Dependencies already installed!
    echo.
)

REM Check for .env file
if not exist ".env" (
    echo .env file not found!
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OpenAI API key!
    echo Run: notepad .env
    echo.
    pause
)

REM Run the application
echo Starting CV Creation System...
echo.
python main.py

REM Deactivate when done
call deactivate
pause
