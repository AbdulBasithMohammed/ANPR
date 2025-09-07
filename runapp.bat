@echo off

:: Change drive to C:
C:
:: Change directory to your project directory
cd "C:\ANPRSystem"

:: Activate the virtual environment
call "C:\ANPRSystem\sys\Scripts\activate"

:: Run the ANPR Main script
start /B "" "C:\ANPRSystem\sys\Scripts\python.exe" app.py