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
from distutils.extension import Extension
from distutils.command.install import install
from distutils.command.config import config
import os

# put the config file in the test dir to prevent installation
config_file = "test/config.py"

class LCInstall(install):
    def run(self):
        install.run(self)
        self.create_conf_file()

    def create_conf_file(self):
        from distutils.fancy_getopt import longopt_xlate
        filename = os.path.join(self.install_lib,
                                self.distribution.get_name() + "Conf.py")
        data = []
        self.execute(write_file, (filename, data),
                     "creating %s" % filename)


class LCConfig(config):
    user_options = config.user_options + [
        ('ssl-include-dirs=', None,
         "directories to search for SSL header files"),
        ('ssl-library-dirs=', None,
         "directories to search for SSL library files"),
        ]

    def initialize_options (self):
        config.initialize_options(self)
        self.ssl_include_dirs = None
        self.ssl_library_dirs = None

    def finalize_options(self):
        if self.ssl_include_dirs is None:
            self.ssl_include_dirs = ['/usr/include/openssl',
                                     '/usr/local/include/openssl']
        if self.ssl_library_dirs is None:
            self.ssl_library_dirs = ['/usr/lib',
                                     '/usr/local/lib']

    def check_lib(self, library, library_dirs=None,
                  headers=None, include_dirs=None,
                  other_libraries=[]):
        self._check_compiler()
        return self.try_link("int main (void) { }",
                             headers, include_dirs,
			     [library]+other_libraries, library_dirs)


    def run (self):
        have_ssl = self.check_lib("ssl",
                                  library_dirs = self.ssl_library_dirs,
                                  include_dirs = self.ssl_include_dirs,
                                  other_libraries = ["crypto"],
                                  headers = ["ssl.h"])
        f = open(config_file,'w')
	f.write("have_ssl = %d\n" % (have_ssl))
        f.write("ssl_library_dirs = %s\n" % `self.ssl_library_dirs`)
        f.write("ssl_include_dirs = %s\n" % `self.ssl_include_dirs`)
        f.write("libraries = %s\n" % `['ssl', 'crypto']`)
        f.close()


class LCDistribution(Distribution):

    def run_commands (self):
        if "config" not in self.commands:
            self.check_ssl()
        Distribution.run_commands(self)

    def check_ssl(self):
        if not os.path.exists(config_file):
            raise SystemExit, 'Please configure LinkChecker by running ' \
	                      '"python setup.py config".'
        from test import config
        if 'bdist_wininst' in self.commands and os.name!='nt':
            self.announce("bdist_wininst command found on non-Windows "
	                  "platform. Disabling SSL compilation")
        elif config.have_ssl:
            self.ext_modules = [Extension('ssl', ['ssl.c'],
                        include_dirs=config.ssl_include_dirs,
                        library_dirs=config.ssl_library_dirs,
                        libraries=config.libraries)]


setup (name = "LinkChecker",
       version = "1.2.6",
       description = "check links of HTML pages",
       author = "Bastian Kleineidam",
       author_email = "calvin@users.sourceforge.net",
       url = "http://linkchecker.sourceforge.net/",
       licence = "GPL",
       long_description =
"""With LinkChecker you can check your HTML documents for broken links.

Features:
---------
o recursive checking
o multithreaded
o output can be colored or normal text, HTML, SQL, CSV or a GML sitemap
  graph
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Gopher, Telnet and local
  file links are supported.
  Javascript links are currently ignored
o restrict link checking with regular expression filters for URLs
o HTTP proxy support
o give username/password for HTTP and FTP authorization
o robots.txt exclusion protocol support
o internationalization support
o (Fast)CGI web interface
""",
       distclass = LCDistribution,
       cmdclass = {'config': LCConfig, 'install': LCInstall},
       packages = ['','DNS','linkcheck'],
       scripts = ['linkchecker'],
       data_files = [('share/locale/de/LC_MESSAGES',
                      ['locale/de/LC_MESSAGES/linkcheck.mo',
		       'locale/de/LC_MESSAGES/linkcheck.po']),
                     ('share/locale/fr/LC_MESSAGES',
                      ['locale/fr/LC_MESSAGES/linkcheck.mo',
		       'locale/fr/LC_MESSAGES/linkcheck.po']),
                     ('/etc', ['linkcheckerrc']),
                     ('share/linkchecker',['linkchecker.bat']),
		    ],
)
