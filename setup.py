#!/usr/bin/python -O

# Copyright (C) 2000-2002  Bastian Kleineidam
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

def get_nt_desktop_path (default=""):
    if os.environ.has_key("ALLUSERSPROFILE"):
        return os.path.join(os.environ["ALLUSERSPROFILE"], "Desktop")
    if os.environ.has_key("USERPROFILE"):
        return os.path.join(os.environ["USERPROFILE"], "Desktop")
    return default

class MyInstall (install):
    def run (self):
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
        if os.name=="nt":
            # copy batch file to desktop
            path = get_nt_desktop_path(default=self.install_scripts)
            path = os.path.join(path, "linkchecker.bat")
            data = open("linkchecker.bat").readlines()
            data = map(string.strip, data)
            data = map(lambda s: s.replace("$python", sys.executable), data)
            data = map(lambda s, self=self: s.replace("$install_scripts",
              self.install_scripts), data)
            self.distribution.create_file(path, data)
            # copy README file to desktop
            path = get_nt_desktop_path(default=self.install_data)
            path = os.path.join(path, "LinkChecker_Readme.txt")
            data = open("README").read()
            self.distribution.create_file(path, data)

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


class MyInstallData (install_data):
    """My own data installer to handle .man pages"""
    def copy_file (self, filename, dirname):
        (out, _) = install_data.copy_file(self, filename, dirname)
        # match for man pages
        if re.search(r'/man/man\d/.+\.\d$', out):
            return (out+".gz", _)
        return (out, _)


class MyDistribution (Distribution):
    def __init__ (self, attrs=None):
        Distribution.__init__(self, attrs=attrs)
        self.config_file = "_"+self.get_name()+"_configdata.py"

    def run_commands (self):
        cwd = os.getcwd()
        data = []
        data.append('config_dir = %s' % `os.path.join(cwd, "config")`)
        data.append("install_data = %s" % `cwd`)
        self.create_conf_file("", data)
        Distribution.run_commands(self)

    def create_conf_file (self, directory, data=[]):
        data.insert(0, "# this file is automatically created by setup.py")
        if not directory:
            directory = os.getcwd()
        filename = os.path.join(directory, self.config_file)
        # add metadata
        metanames = ("name", "version", "author", "author_email",
                         "maintainer", "maintainer_email", "url",
                         "licence", "description", "long_description",
                         "keywords", "platforms", "fullname", "contact",
                         "contact_email", "licence", "fullname")
        for name in metanames:
              method = "get_" + name
              cmd = "%s = %s" % (name, `getattr(self.metadata, method)()`)
              data.append(cmd)
        # write the config file
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)

    def create_file (self, filename, data):
        # write the file
        util.execute(write_file, (filename, data),
                 "creating %s" % filename, self.verbose>=1, self.dry_run)

if os.name=='nt':
    macros = [('YY_NO_UNISTD_H', None)]
else:
    macros = []
myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

setup (name = "linkchecker",
       version = "1.8.12",
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
o Cookie support
o i18n support
o a command line interface
o a (Fast)CGI web interface (requires HTTP server)
""",
       distclass = MyDistribution,
       cmdclass = {'install': MyInstall,
                   'install_data': MyInstallData,
                  },
       packages = ['', 'linkcheck', 'linkcheck.log',
                   'linkcheck.parser', 'linkcheck.DNS'],
       ext_modules = [Extension('linkcheck.parser.htmlsax',
                  ['linkcheck/parser/htmllex.c',
                   'linkcheck/parser/htmlparse.c'],
                  include_dirs = ["linkcheck/parser"],
                  define_macros = macros,
                  )],

       scripts = ['linkchecker'],
       data_files = [
         ('share/locale/de/LC_MESSAGES',
             ['share/locale/de/LC_MESSAGES/linkcheck.mo']),
         ('share/locale/fr/LC_MESSAGES',
             ['share/locale/fr/LC_MESSAGES/linkcheck.mo']),
         ('share/locale/nl/LC_MESSAGES',
             ['share/locale/nl/LC_MESSAGES/linkcheck.mo']),
         ('share/linkchecker', ['linkcheckerrc']),
         ('share/linkchecker/examples',
             ['lconline/leer.html.en', 'lconline/leer.html.de',
              'lconline/index.html', 'lconline/lc_cgi.html.en',
              'lconline/lc_cgi.html.de', 'lconline/check.js',
              'lc.cgi','lc.fcgi','lc.sz_fcgi','linkchecker.bat']),
         ('share/man/man1', ['linkchecker.1']),
      ],
)
