#!/usr/bin/env python
from distutils.core import setup
from distutils.dist import Distribution
import sys

# Hack for linkchecker.bat
class LCDistribution(Distribution):
    def __init__(self, attrs=None):
        Distribution.__init__(self, attrs)
        if sys.platform=='win32':
            self.scripts.append('linkchecker.bat')


setup (name = "linkchecker",
       version = "1.2.3",
       description = "check links of HTML pages",
       author = "Bastian Kleineidam",
       author_email = "calvin@users.sourceforge.net",
       url = "http://linkchecker.sourceforge.net/",
       licence = "GPL",

       distclass = LCDistribution,
       packages = ['','DNS','linkcheck'],
       # uncomment ext_modules to enable HTTPS support
       # you must have an SSL library and the Python header
       # files installed
       ext_modules = [('ssl', {'sources': ['ssl.c'],
                        'include_dirs': ['/usr/include/openssl'],
                        'library_dirs': ['/usr/lib'],
                        'libs': ['ssl']})],
       scripts = ['linkchecker'],
       )
