#!/usr/bin/python -O

# Copyright (C) 2000,2001  Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from types import StringType
from distutils.core import setup, DEBUG
from distutils.dist import Distribution
from distutils.extension import Extension
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.command.config import config
from distutils import util
from distutils.file_util import write_file
from distutils.dep_util import newer

import os, string, re, sys


class MyInstall(install):
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
        # copy batch file to desktop
        if os.name=="nt":
            path = self.install_scripts
            if os.environ.has_key("ALLUSERSPROFILE"):
                path = os.path.join(os.environ["ALLUSERSPROFILE"], "Desktop")
            elif os.environ.has_key("USERPROFILE"):
                path = os.path.join(os.environ["USERPROFILE"], "Desktop")
            data = open("linkchecker.bat").readlines()
            data = map(string.strip, data)
            data = map(lambda s: s.replace("$python", sys.executable), data)
            data = map(lambda s, self=self: s.replace("$install_scripts",
              self.install_scripts), data)
            self.distribution.create_batch_file(path, data)


    # sent a patch for this, but here it is for compatibility
    def dump_dirs (self, msg):
        if DEBUG:
            from distutils.fancy_getopt import longopt_xlate
            print msg + ":"
            for opt in self.user_options:
                opt_name = opt[0]
                if opt_name[-1] == "=":
                    opt_name = opt_name[0:-1]
                if self.negative_opt.has_key(opt_name):
                    opt_name = string.translate(self.negative_opt[opt_name],
                                                longopt_xlate)
                    val = not getattr(self, opt_name)
                else:
                    opt_name = string.translate(opt_name, longopt_xlate)
                    val = getattr(self, opt_name)
                print "  %s: %s" % (opt_name, val)


class MyConfig(config):
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
        # suitable for each platform
        config.finalize_options(self)
        if self.ssl_include_dirs is None:
            if os.name=='posix':
                self.ssl_include_dirs = ['/usr/include/openssl',
                                         '/usr/local/include/openssl']
            else:
                # dont know default incldirs on other platforms
                self.ssl_include_dirs = []
        if self.ssl_library_dirs is None:
            if os.name=='posix':
                self.ssl_library_dirs = ['/usr/lib', '/usr/local/lib']
            else:
                # dont know default libdirs on other platforms
                self.ssl_library_dirs = []


    def run (self):
        # try to compile a test program with SSL
        config.run(self)
        self.libraries.append('ssl')
        have_ssl = self.check_lib("ssl",
                                  library_dirs = self.ssl_library_dirs,
                                  include_dirs = self.ssl_include_dirs,
                                  headers = ["ssl.h"])
        # write the result in the configuration file
        data = []
	data.append("have_ssl = %d" % (have_ssl))
        data.append("ssl_library_dirs = %s" % `self.ssl_library_dirs`)
        data.append("ssl_include_dirs = %s" % `self.ssl_include_dirs`)
        data.append("libraries = %s" % `self.libraries`)
        data.append("install_data = %s" % `os.getcwd()`)
        self.distribution.create_conf_file(".", data)


class MyDistribution(Distribution):
    def __init__(self, attrs=None):
        Distribution.__init__(self, attrs=attrs)
        self.config_file = "_"+self.get_name()+"_configdata.py"


    def run_commands(self):
        if "config" not in self.commands:
            self.check_ssl()
        Distribution.run_commands(self)


    def check_ssl(self):
        if not os.path.exists(self.config_file):
            #raise SystemExit, "please run 'python setup.py config'"
            self.announce("generating default configuration")
            self.run_command('config')
        import _linkchecker_configdata
        if 'bdist_wininst' in self.commands and os.name != 'nt':
            self.announce("bdist_wininst command found on non-Windows "
	                  "platform. Disabling SSL compilation")
        elif _linkchecker_configdata.have_ssl:
            self.ext_modules = [Extension('linkcheckssl.ssl',
	                ['linkcheckssl/ssl.c'],
                        include_dirs=_linkchecker_configdata.ssl_include_dirs,
                        library_dirs=_linkchecker_configdata.ssl_library_dirs,
                        libraries=_linkchecker_configdata.libraries)]


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


    def create_batch_file(self, directory, data):
        filename = os.path.join(directory, "linkchecker.bat")
        # write the batch file
        util.execute(write_file, (filename, data),
                 "creating %s" % filename, self.verbose>=1, self.dry_run)


myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

setup (name = "linkchecker",
       version = "1.3.9",
       description = "check HTML documents for broken links",
       author = myname,
       author_email = myemail,
       maintainer = myname,
       maintainer_email = myemail,
       url = "http://linkchecker.sourceforge.net/",
       licence = "GPL",
       long_description = """Linkchecker features
o recursive checking
o multithreading
o output in colored or normal text, HTML, SQL, CSV or a sitemap
  graph in GML or XML.
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Gopher, Telnet and local
  file links support
o restriction of link checking with regular expression filters for URLs
o proxy support
o username/password authorization for HTTP and FTP
o robots.txt exclusion protocol support
o i18n support
o a command line interface
o a (Fast)CGI web interface (requires HTTP server)
""",
       distclass = MyDistribution,
       cmdclass = {'config': MyConfig,
                   'install': MyInstall,
		  },
       packages = ['','DNS','linkcheck','linkcheckssl'],
       scripts = ['linkchecker'],
       data_files = [('share/locale/de/LC_MESSAGES',
      ['locale/de/LC_MESSAGES/linkcheck.mo']),
     ('share/locale/fr/LC_MESSAGES',
      ['locale/fr/LC_MESSAGES/linkcheck.mo']),
     ('share/linkchecker', ['linkcheckerrc']),
     ('share/linkchecker/examples',
      ['lconline/leer.html',
       'lconline/index.html', 'lconline/lc_cgi.html',
       'lc.cgi','lc.fcgi','lc.sz_fcgi','linkchecker.bat']),
      ('man/man1', ['linkchecker.1']),
    ],
)
