@echo off
cls

IF EXIST "venv" GOTO Convert
echo Virtual environment not found. Installing ...
call install_venv.bat


:Run
ECHO Running application
call "venv\Scripts\activate.bat"
python ssp_content_creator.py 

:End

