@echo off
: batch file for generating the windows .exe installer
set PYTHON="c:\Python26\python.exe"
rd /S /Q build
rd /S /Q dist
%PYTHON% setup.py sdist --manifest-only
%PYTHON% setup.py build -c mingw32 py2exe
