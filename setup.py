#!/usr/bin/env python
from distutils.core import setup
from distutils.dist import Distribution
from Template import Template
import sys

# Hack for linkchecker.bat
class LCDistribution(Distribution):
    def run_commands (self):
        if sys.platform=='win32':
            inst = self.find_command_obj("install")
            inst.ensure_ready()
            t = Template("linkchecker.bat.tmpl")
            f = open("linkchecker.bat","w")
	    f.write(t.fill_in({"path_to_linkchecker": inst.install_scripts}))
            f.close()
            self.scripts.append('linkchecker.bat')
        for cmd in self.commands:
            self.run_command (cmd)


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
