@echo off
set PYTHON="c:\Python26\python.exe"
%PYTHON% -3 c:\python26\scripts\nosetests -m "^test_.*" tests/
@pause
