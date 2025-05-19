@echo off
echo Activating virtual environment...

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Verify activation
echo Virtual environment activated.
echo Python path: 
where python

REM Run the application
echo Starting Data Insight Analyzer...
python app.py

pause