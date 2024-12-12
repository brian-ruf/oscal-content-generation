@echo off
cls

ECHO Checking for PIP upgrade on system
python.exe -m pip install --upgrade pip
IF NOT EXIST "venv" (
    ECHO Creating virtual environment
    python -m venv "venv"
) ELSE (
    ECHO Virtual envirionment already exists.
)
echo continuing
call "venv\Scripts\activate.bat"
ECHO Checking for PIP upgrade in virtual environment
python.exe -m pip install --upgrade pip
ECHO Installing requirements.txt
python -m pip install -r requirements.txt

@REM ECHO Installing pyinstaller
