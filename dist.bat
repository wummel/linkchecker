@echo off
: batch file for generating the windows .exe installer
set PYTHON="c:\Python26\python.exe"
call build.bat
rd /S /Q dist
%PYTHON% setup.py py2exe
