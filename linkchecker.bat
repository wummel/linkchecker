@echo off

rem if you want to have german output uncomment the next line
rem set LC_MESSAGES=de
rem Limited to 9 parameters? Is there a * for Windows?
python "$path_to_linkchecker\linkchecker" %1 %2 %3 %4 %5 %6 %7 %8 %9
