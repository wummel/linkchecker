@echo off

rem Limited to 9 parameters? Is there a $* for Windows?
python "@INSTALL_BIN@\linkchecker" %1 %2 %3 %4 %5 %6 %7 %8 %9
