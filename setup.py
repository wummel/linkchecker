#!/usr/bin/env python
from distutils.core import setup

setup (name = "linkchecker",
       version = "1.2.0",
       description = "check links of HTML pages",
       author = "Bastian Kleineidam",
       author_email = "calvin@users.sourceforge.net",
       url = "http://linkchecker.sourceforge.net",
       licence = "GPL",

       packages = ['','DNS','linkcheck'],
       # uncomment ext_modules to enable HTTPS support
       # you must have an SSL library and the Python header
       # files installed
       ext_modules = [('ssl', {'sources': ['ssl.c'],
                        'include_dirs': ['/usr/include/openssl'],
                        'libs': ['ssl']})],
       )
