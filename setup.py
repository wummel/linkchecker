#!/usr/bin/python -O
"""setup file for the distuils module"""
# -*- coding: iso-8859-1 -*-

# Copyright (C) 2000-2004  Bastian Kleineidam
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

import os
import stat
import re
import sys
import string
from types import StringType, TupleType
from distutils.core import setup, Extension, DEBUG
try:
    import py2exe
    distklass = py2exe.Distribution
except ImportError:
    import distutils.dist
    distklass = distutils.dist.Distribution
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.file_util import write_file
from distutils import util


def p (path):
    """norm a path name to platform specific notation"""
    return os.path.normpath(path)


def get_nt_desktop_path (default=""):
    if os.environ.has_key("ALLUSERSPROFILE"):
        return os.path.join(os.environ["ALLUSERSPROFILE"], "Desktop")
    if os.environ.has_key("USERPROFILE"):
        return os.path.join(os.environ["USERPROFILE"], "Desktop")
    return default


class MyInstall (install, object):

    def run (self):
        super(MyInstall, self).run()
        # we have to write a configuration file because we need the
        # <install_data> directory (and other stuff like author, url, ...)
        data = []
        for d in ['purelib', 'platlib', 'lib', 'headers', 'scripts', 'data']:
            attr = 'install_%s'%d
            if self.root:
                # cut off root path prefix
                cutoff = len(self.root)
                # don't strip the path separator
                if self.root.endswith(os.sep):
                    cutoff -= 1
                val = getattr(self, attr)[cutoff:]
            else:
                val = getattr(self, attr)
            data.append("%s = %r" % (attr, val))
            if d == 'data':
                cdir = os.path.join(val, "share", "linkchecker")
                data.append('config_dir = %r' % cdir)
	self.distribution.create_conf_file(data, directory=self.install_lib)

    def get_outputs (self):
        """add the generated config file from distribution.create_conf_file()
           to the list of outputs.
        """
        outs = super(MyInstall, self).get_outputs()
        outs.append(self.distribution.get_conf_filename(self.install_lib))
        return outs

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


class MyInstallData (install_data, object):
    """My own data installer to handle permissions"""

    def run (self):
        """adjust permissions on POSIX systems"""
        super(MyInstallData, self).run()
        if os.name == 'posix' and not self.dry_run:
            # Make the data files we just installed world-readable,
            # and the directories world-executable as well.
            for path in self.get_outputs():
                mode = os.stat(path)[stat.ST_MODE]
                if stat.S_ISDIR(mode):
                    mode |= 011
                mode |= 044
                os.chmod(path, mode)


class MyDistribution (distklass, object):
    """custom distribution class generating config file"""

    def run_commands (self):
        """generate config file and run commands"""
        cwd = os.getcwd()
        data = []
        data.append('config_dir = %r' % os.path.join(cwd, "config"))
        data.append("install_data = %r" % cwd)
        self.create_conf_file(data)
        super(MyDistribution, self).run_commands()

    def get_conf_filename (self, directory):
        """get name for config file"""
        return os.path.join(directory, "_%s_configdata.py"%self.get_name())

    def create_conf_file (self, data, directory=None):
        """create local config file from given data (list of lines) in
           the directory (or current directory if not given)
        """
        data.insert(0, "# this file is automatically created by setup.py")
        data.insert(0, "# -*- coding: iso-8859-1 -*-")
        if directory is None:
            directory = os.getcwd()
        filename = self.get_conf_filename(directory)
        # add metadata
        metanames = ("name", "version", "author", "author_email",
                     "maintainer", "maintainer_email", "url",
                     "license", "description", "long_description",
                     "keywords", "platforms", "fullname", "contact",
                     "contact_email", "fullname")
        for name in metanames:
              method = "get_" + name
              cmd = "%s = %r" % (name, getattr(self.metadata, method)())
              data.append(cmd)
        # write the config file
        data.append('appname = "LinkChecker"')
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)

    def create_file (self, filename, data):
        # write the file
        util.execute(write_file, (filename, data),
                 "creating %s" % filename, self.verbose>=1, self.dry_run)


if os.name == 'nt':
    # windows does not have unistd.h
    macros = [('YY_NO_UNISTD_H', None)]
    cargs = []
    # add post-install script for the bdist_wininst command
    scripts = ['linkchecker', 'install-linkchecker.py']
else:
    macros = []
    # for gcc 3.x we could add -std=gnu99 to get rid of warnings, but
    # that breaks other compilers
    cargs = ["-pedantic"]
    scripts = ['linkchecker']

myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

setup (name = "linkchecker",
       version = "1.13.5",
       description = "check HTML documents for broken links",
       keywords = "link,url,checking,verfication",
       author = myname,
       author_email = myemail,
       maintainer = myname,
       maintainer_email = myemail,
       url = "http://linkchecker.sourceforge.net/",
       download_url = "http://sourceforge.net/project/showfiles.php?group_id=1913",
       license = "GPL",
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
       packages = ['linkcheck', 'linkcheck.logger', 'linkcheck.checker',
                   'linkcheck.dns', 'linkcheck.dns.rdtypes',
                   'linkcheck.dns.rdtypes.ANY', 'linkcheck.dns.rdtypes.IN',
                   'linkcheck.HtmlParser', 'linkcheck.tests',
                   'linkcheck.ftests', 'linkcheck.dns.tests', ],
       ext_modules = [Extension('linkcheck.HtmlParser.htmlsax',
                  ['linkcheck/HtmlParser/htmllex.c',
                   'linkcheck/HtmlParser/htmlparse.c',
                   'linkcheck/HtmlParser/s_util.c',
                  ],
                  include_dirs = ["linkcheck/HtmlParser"],
                  define_macros = macros,
                  )],
       scripts = scripts,
       data_files = [
         ('share/locale/de/LC_MESSAGES',
             ['share/locale/de/LC_MESSAGES/linkchecker.mo']),
         ('share/locale/fr/LC_MESSAGES',
             ['share/locale/fr/LC_MESSAGES/linkchecker.mo']),
         ('share/locale/nl/LC_MESSAGES',
             ['share/locale/nl/LC_MESSAGES/linkchecker.mo']),
         ('share/linkchecker', ['config/linkcheckerrc',
                                'config/logging.conf', ]),
         ('share/linkchecker/examples',
             ['cgi/lconline/leer.html.en', 'cgi/lconline/leer.html.de',
              'cgi/lconline/index.html', 'cgi/lconline/lc_cgi.html.en',
              'cgi/lconline/lc_cgi.html.de', 'cgi/lconline/check.js',
              'cgi/lc.cgi', 'cgi/lc.fcgi',
              'config/linkchecker-completion', 'config/linkcheck-cron.sh']),
         ('share/man/man1', ['linkchecker.1']),
      ],
      classifiers = [
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: C',
      ],
)
