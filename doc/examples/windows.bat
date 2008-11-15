@echo off
:: example using linkchecker on windows, logging to html
set PYDIR=c:\python26
%PYDIR%\python.exe %PYDIR%\scripts\linkchecker -Fhtml http://www.example.com
