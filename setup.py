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

from types import StringType
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
        # we have to write a configuration file because we need the
        # <install_data>/share/locale directory (and other stuff
        # like author, url, ...)
        # install data
        data = []
        for d in ['purelib', 'platlib', 'lib', 'headers', 'scripts', 'data']:
            attr = 'install_'+d
            if self.root:
                val = getattr(self, attr)[len(self.root):]
            else:
                val = getattr(self, attr)
            data.append("%s = %s" % (attr, `val`))
        from pprint import pformat
        data.append('outputs = %s' % pformat(self.get_outputs()))
	self.distribution.create_conf_file(self.install_lib, data)


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
        # we have some default include and library directories
        self.basic_finalize_options()
        if self.ssl_include_dirs is None:
            self.ssl_include_dirs = ['/usr/include/openssl',
                                     '/usr/local/include/openssl']
        if self.ssl_library_dirs is None:
            self.ssl_library_dirs = ['/usr/lib',
                                     '/usr/local/lib']

    def basic_finalize_options(self):
        """fix up types of option values"""
        # this should be in config.finalize_options
        # I submitted a patch
        if self.include_dirs is None:
            self.include_dirs = self.distribution.include_dirs or []
        elif type(self.include_dirs) is StringType:
            self.include_dirs = string.split(self.include_dirs, os.pathsep)

        if self.libraries is None:
            self.libraries = []
        elif type(self.libraries) is StringType:
            self.libraries = [self.libraries]

        if self.library_dirs is None:
            self.library_dirs = []
        elif type(self.library_dirs) is StringType:
            self.library_dirs = [self.library_dirs]


    def run (self):
        # try to compile a test program with SSL
        config.run(self)
        have_ssl = self.check_lib("ssl",
                                  library_dirs = self.ssl_library_dirs,
                                  include_dirs = self.ssl_include_dirs,
                                  headers = ["ssl.h"])
        # write the result in the configuration file
        data = []
	data.append("have_ssl = %d" % (have_ssl))
        data.append("ssl_library_dirs = %s" % `self.ssl_library_dirs`)
        data.append("ssl_include_dirs = %s" % `self.ssl_include_dirs`)
        data.append("libraries = %s" % `['ssl', 'crypto']`)
        data.append("install_data = %s" % `os.getcwd()`)
        self.distribution.create_conf_file(".", data)


class LCDistribution(Distribution):
    def __init__(self, attrs=None):
        Distribution.__init__(self, attrs=attrs)
        self.config_file = self.get_name()+"Conf.py"


    def run_commands(self):
        if "config" not in self.commands:
            self.check_ssl()
        Distribution.run_commands(self)


    def check_ssl(self):
        if not os.path.exists(self.config_file):
            raise SystemExit, "please run 'python setup.py config'"
            #self.announce("generating default configuration")
            #self.run_command('config')
        import LinkCheckerConf
        if 'bdist_wininst' in self.commands and os.name!='nt':
            self.announce("bdist_wininst command found on non-Windows "
	                  "platform. Disabling SSL compilation")
        elif LinkCheckerConf.have_ssl:
            self.ext_modules = [Extension('ssl', ['ssl.c'],
                        include_dirs=LinkCheckerConf.ssl_include_dirs,
                        library_dirs=LinkCheckerConf.ssl_library_dirs,
                        libraries=LinkCheckerConf.libraries)]


    def create_conf_file(self, directory, data=[]):
        data.insert(0, "# this file is automatically created by setup.py")
        filename = os.path.join(directory, self.config_file)
        # add metadata
        metanames = dir(self.metadata) + \
                    ['fullname', 'contact', 'contact_email']
        for name in metanames:
              method = "get_" + name
              cmd = "%s = %s" % (name, `getattr(self.metadata, method)()`)
              data.append(cmd)
        # write the config file
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)

myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

setup (name = "LinkChecker",
       version = "1.2.8",
       description = "check links of HTML pages",
       author = myname,
       author_email = myemail,
       maintainer = myname,
       maintainer_email = myemail,
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
o proxy support
o give username/password for HTTP and FTP authorization
o robots.txt exclusion protocol support
o i18n support
o command line interface
o (Fast)CGI web interface (requires HTTP server)
""",
       distclass = LCDistribution,
       cmdclass = {'config': LCConfig, 'install': LCInstall},
       packages = ['','DNS','linkcheck'],
       scripts = ['linkchecker'],
       data_files = [('share/locale/de/LC_MESSAGES',
                      ['locale/de/LC_MESSAGES/linkcheck.mo']),
                     ('share/locale/fr/LC_MESSAGES',
                      ['locale/fr/LC_MESSAGES/linkcheck.mo']),
                     ('share/linkchecker',['linkchecker.bat',
		                           'linkcheckerrc',]),
		    ],
)
