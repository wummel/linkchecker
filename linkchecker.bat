@echo off

rem === adjust vars below ===
set PYTHON=c:\progra~1\python\python.exe
set LINKCHECKER=c:\progra~1\linkchecker-1.1.0
rem === end configure ===

%PYTHON% %LINKCHECKER%\linkchecker %1 %2 %3 %4 %5 %6 %7 %8 %9
