#!/usr/bin/env python

#    Copyright (C) 2000  Bastian Kleineidam
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from distutils.core import setup
from distutils.dist import Distribution
from Template import Template
import sys,os,string

class LCDistribution(Distribution):
    default_include_dirs = ['/usr/include/openssl',
                            '/usr/local/include/openssl']
    def run_commands (self):
        self.check_ssl()
        self.replace_vars()
        for cmd in self.commands:
            self.run_command (cmd)

    def check_ssl(self):
        incldir = self.has_ssl()
        if incldir:
            self.announce("SSL header file ssl.h found, "
                          "enabling SSL compilation.")
            self.ext_modules = [('ssl', {'sources': ['ssl.c'],
                        'include_dirs': [incldir],
                        'library_dirs': ['/usr/lib'],
                        'libs': ['ssl']})]
        else:
            self.announce("SSL header file ssl.h missing, "
                          "disabling SSL compilation.\n"
			  "Use the -I option for the build_ext command.")

    def has_ssl(self):
        incls = self.find_command_obj("build_ext").include_dirs
        incls = (incls and string.split(incls, os.pathsep)) or []
        for d in incls + self.default_include_dirs:
            if os.path.exists(os.path.join(d, "ssl.h")):
                return d
        return 0

                                           
    def replace_vars(self):
        inst = self.find_command_obj("install")
        inst.ensure_ready()
        t = Template("linkcheck/__init__.py.tmpl")
        f = open("linkcheck/__init__.py","w")
        f.write(t.fill_in({"install_data": inst.install_data}))
        f.close()
        if sys.platform=='win32':
            t = Template("linkchecker.bat.tmpl")
            f = open("linkchecker.bat","w")
            f.write(t.fill_in({"path_to_linkchecker": inst.install_scripts}))
            f.close()
            self.scripts.append('linkchecker.bat')


setup (name = "linkchecker",
       version = "1.2.3",
       description = "check links of HTML pages",
       author = "Bastian Kleineidam",
       author_email = "calvin@users.sourceforge.net",
       url = "http://linkchecker.sourceforge.net/",
       licence = "GPL",
       long_description =
"""With LinkChecker you can check your HTML documents for broken links.
Features:
o recursive checking
o multithreaded
o output can be colored or normal text, HTML, SQL, CSV or a GML sitemap
  graph
o HTTP/1.1, HTTPS, FTP, mailto:, news:, Gopher, Telnet and local file links 
  are supported.
  Javascript links are currently ignored
o restrict link checking with regular expression filters for URLs
o HTTP proxy support
o give username/password for HTTP and FTP authorization
o robots.txt exclusion protocol support
o internationalization support (currently english and german)
""",
       distclass = LCDistribution,
       packages = ['','DNS','linkcheck'],
       scripts = ['linkchecker'],
       data = ['locale/de/LC_MESSAGES/linkcheck.po'],
)
