@echo off
rem Copyright (C) 2000  Bastian Kleineidam
rem
rem This program is free software; you can redistribute it and/or modify
rem it under the terms of the GNU General Public License as published by
rem the Free Software Foundation; either version 2 of the License, or
rem (at your option) any later version.
rem
rem This program is distributed in the hope that it will be useful,
rem but WITHOUT ANY WARRANTY; without even the implied warranty of
rem MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
rem GNU General Public License for more details.
rem
rem You should have received a copy of the GNU General Public License
rem along with this program; if not, write to the Free Software
rem Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

rem uncomment the next line to enable german output
rem set LC_MESSAGES=de
rem uncomment the next line to enable french output
rem set LC_MESSAGES=fr

rem If you see $python or $install_scripts on the next line, then you
rem are looking at a skeleton .bat file suited only for installation.
rem Look in c:\python21\scripts or wherever Python is installed for
rem the executable .bat file.
$python -O $install_scripts\linkchecker --interactive %*
