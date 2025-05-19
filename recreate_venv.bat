@echo off
echo Removing old virtual environment...
rmdir /s /q venv

echo Creating new virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --prefer-binary -r requirements.txt

echo.
echo Virtual environment recreated successfully!
echo.

pause