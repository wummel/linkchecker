@echo off
REM batch file for generating the windows .exe installer
set PYTHON=c:\Python24\python.exe
%PYTHON% setup.py sdist --manifest-only
%PYTHON% setup.py build -c mingw32 bdist_wininst -b hase.bmp
