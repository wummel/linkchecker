@echo off
set PYTHON="c:\Python26\python.exe"
%PYTHON% setup.py clean --all
del linkcheck\HtmlParser\htmlsax.pyd
del linkcheck\network\_network.pyd
del doc\html\lccollection.qhc
del doc\html\lcdoc.qch
