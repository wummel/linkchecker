REM batch file for generating the windows .exe installer
@echo off
c:\Programme\Python24\python.exe setup.py sdist --manifest-only
c:\Programme\Python24\python.exe setup.py build -c mingw32 bdist_wininst -b hase.bmp
