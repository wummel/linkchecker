@echo off
set PYTHON="c:\Python 24\python.exe"
%PYTHON% setup.py sdist --manifest-only
%PYTHON% setup.py build -c mingw32
copy build\lib.win32-2.4\linkcheck\HtmlParser\htmlsax.pyd linkcheck\HtmlParser
copy build\lib.win32-2.4\linkcheck\ftpparse\_ftpparse.pyd linkcheck\ftpparse
