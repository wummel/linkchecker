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
import os,string


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
    def run (self):
        data = ["install_data = %s" % `os.getcwd()`]
        self.distribution.create_conf_file(".", data)


class LCDistribution(Distribution):
    def __init__(self, attrs=None):
        Distribution.__init__(self, attrs=attrs)
        self.config_file = self.get_name()+"Conf.py"


    def create_conf_file(self, directory, data=[]):
        data.insert(0, "# this file is automatically created by setup.py")
        filename = os.path.join(directory, self.config_file)
        # metadata
        metanames = dir(self.metadata) + \
                    ['fullname', 'contact', 'contact_email']
        for name in metanames:
              method = "get_" + name
              cmd = "%s = %s" % (name, `getattr(self.metadata, method)()`)
              data.append(cmd)
        # write the config file
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)


setup (name = "LinkChecker",
       version = "1.3.0",
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
                     ('share/linkchecker',['linkchecker.bat',
		                           'linkcheckerrc',]),
		    ],
)
