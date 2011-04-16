:: Build LinkChecker
:: Copyright (C) 2010-2011 Bastian Kleineidam
:: This program is free software; you can redistribute it and/or modify
:: it under the terms of the GNU General Public License as published by
:: the Free Software Foundation; either version 2 of the License, or
:: (at your option) any later version.
::
:: This program is distributed in the hope that it will be useful,
:: but WITHOUT ANY WARRANTY; without even the implied warranty of
:: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
:: GNU General Public License for more details.
::
:: You should have received a copy of the GNU General Public License along
:: with this program; if not, write to the Free Software Foundation, Inc.,
:: 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
@echo off
set PYDIR=C:\Python27
set PYVER=2.7
set PLATNAME=win32
set COMPILER="-c mingw32"
:: for 64bit platforms use Win SDK
::set PLATNAME=win-amd64
::set COMPILER=
%PYDIR%\python.exe setup.py sdist --manifest-only
%PYDIR%\python.exe setup.py build %COMPILER%
:: copy .pyd files to start linkchecker in local directory
copy build\lib.%PLATNAME%-%PYVER%\linkcheck\HtmlParser\htmlsax.pyd linkcheck\HtmlParser
copy build\lib.%PLATNAME%-%PYVER%\linkcheck\network\_network.pyd linkcheck\network
:: generate GUI documentation
c:\qt\2010.05\qt\bin\qcollectiongenerator doc\html\lccollection.qhcp -o doc\html\lccollection.qhc
