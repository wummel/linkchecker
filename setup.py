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
from distutils import util
from distutils.file_util import write_file
import os


class LCInstall(install):
    def run(self):
        install.run(self)
        self.distribution.create_conf_file(self.install_lib)


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
        data = []
	data.append("have_ssl = %d" % (have_ssl))
        data.append("ssl_library_dirs = %s" % `self.ssl_library_dirs`)
        data.append("ssl_include_dirs = %s" % `self.ssl_include_dirs`)
        data.append("libraries = %s" % `['ssl', 'crypto']`)
        data.append("install_data = %s" % `os.getcwd()`)
        self.distribution.create_conf_file(".", data)


class LCDistribution(Distribution):

    config_file = "LinkCheckerConf.py"

    def run_commands(self):
        if "config" not in self.commands:
            self.check_ssl()
        Distribution.run_commands(self)

    def check_ssl(self):
        if not os.path.exists(self.config_file):
            self.announce("generating default configuration")
            self.run_command('config')
        import LinkCheckerConf
        if 'bdist_wininst' in self.commands and os.name!='nt':
            self.announce("bdist_wininst command found on non-Windows "
	                  "platform. Disabling SSL compilation")
        elif LinkCheckerConf.have_ssl:
            self.ext_modules = [Extension('ssl', ['ssl.c'],
                        include_dirs=LinkCheckerConf.ssl_include_dirs,
                        library_dirs=LinkCheckerConf.ssl_library_dirs,
                        libraries=LinkCheckerConf.libraries)]

    def create_conf_file(self, dir, data=[]):
        data.insert(0, "# this file is automatically created by setup.py")
        filename = os.path.join(dir, self.config_file)
        data.append("name = %s" % `self.get_name()`)
        data.append("version = %s" % `self.get_version()`)
        data.append("author = %s" % `self.get_author()`)
        data.append("author_email = %s" % `self.get_author_email()`)
        data.append("url = %s" % `self.get_url()`)
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose >= 1, self.dry_run)

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
