:: Generating the LinkChecker Windows .exe installer
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
set UPX_EXE="C:\Software\upx308w\upx.exe"
set SZ_EXE="C:\Programme\7-Zip\7z.exe"
for /f "usebackq tokens=*" %%a in (`%PYDIR%\python.exe setup.py --version`) do set VERSION="%%a"
set PORTDIR=LinkChecker-%VERSION%

:: uncomment for skipping portable dist creation
::goto :dist
echo Building portable distribution
set LINKCHECKER_PORTABLE=1
rd /s /q dist > nul
%PYDIR%\python.exe setup.py py2exe
rd /s /q %PORTDIR% > nul
xcopy /e /i dist %PORTDIR%
del %PORTDIR%\omt.iss
echo Compressing Python libraries and executables
:: skip DLL compression as it causes the GUI not to start
for /r %PORTDIR% %%f in (*.pyd,*.exe) do %UPX_EXE% "%%f" --best
echo Generating portable distribution file
%SZ_EXE% a -mx=9 LinkChecker-%VERSION%-portable.zip %PORTDIR%
rd /s /q %PORTDIR%

:dist
set LINKCHECKER_PORTABLE=0
rd /s /q build > nul
call %~dp0\build.bat
rd /s /q dist > nul
%PYDIR%\python.exe setup.py py2exe

:finish
