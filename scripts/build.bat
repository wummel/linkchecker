@echo off
set PYTHON="c:\Python25\python.exe"
%PYTHON% setup.py sdist --manifest-only
%PYTHON% setup.py build -c mingw32
copy build\lib.win32-2.5\linkcheck\HtmlParser\htmlsax.pyd linkcheck\HtmlParser
copy build\lib.win32-2.5\linkcheck\ftpparse\_ftpparse.pyd linkcheck\ftpparse
copy build\lib.win32-2.5\linkcheck\network\_network.pyd linkcheck\network
