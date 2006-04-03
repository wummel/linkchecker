@echo off
REM batch file for generating the windows .exe installer
set PYTHON="c:\Python 24\python.exe"
%PYTHON% setup.py clean --all
%PYTHON% setup.py sdist --manifest-only
%PYTHON% setup.py build -c mingw32 bdist_wininst -b hase.bmp
REM start resource editor for .exe icon
"%PROGRAMFILES%\XN Resource Editor\XNResourceEditor.exe"
