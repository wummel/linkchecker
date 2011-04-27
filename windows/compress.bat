:: Compressing executables and libraries
:: Copyright (C) 2011 Bastian Kleineidam
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

set UPX_EXE="C:\Software\upx307w\upx.exe"

:: Do not compress the MS Visual C++ runtime files. Otherwise the
:: program won't run.
if "%1" == "msvcm90.dll" goto :finish
if "%1" == "msvcp90.dll" goto :finish
if "%1" == "msvcr90.dll" goto :finish

%UPX_EXE% "%1" --best

:finish
