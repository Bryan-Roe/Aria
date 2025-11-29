@echo off
REM Quick start script for QAI Integration Service (Windows)

echo Starting QAI Integration Service...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing dependencies...
pip install -q -r requirements.txt
echo.

REM Start the service
echo Starting FastAPI service on http://localhost:8000
echo Interactive docs at http://localhost:8000/docs
echo.
python app.py
