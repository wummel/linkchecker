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
from Template import Template
import sys,os,string

def change_root_inv(root, pathname):
    """the (partially) inverse function of change_root"""
    if (not root) or \
       (len(root)<len(pathname)) or \
       (path[:len(root)]!=root):
        return pathname

    path = pathname[len(root):]
    if os.name == 'posix':
        if path[0]!='/': path = '/'+path
    elif os.name == 'nt':
        if path[0]!='\\': path = '\\'+path
        path = os.path.splitdrive(root)[0] + path
    return path

class LCDistribution(Distribution):
    default_include_dirs = ['/usr/include/openssl',
                            '/usr/local/include/openssl']
    default_library_dirs = ['/usr/lib',
                            '/usr/local/lib']
    def run_commands (self):
        self.check_ssl()
        self.additional_things()
        Distribution.run_commands(self)

    def check_ssl(self):
        ok = 0
        incldirs = self.get_build_ext().include_dirs+self.default_include_dirs
        libdirs = self.get_build_ext().library_dirs+self.default_library_dirs
        for d in incldirs:
            if os.path.exists(os.path.join(d, "ssl.h")):
                self.announce('Found %s/ssl.h' % d)
                ok = ok + 1
        for d in libdirs:
            if os.path.exists(os.path.join(d, "libssl.so")):
                self.announce('Found %s/libssl.so' % d)
                ok = ok + 1
        if ok==2:
            self.announce("Enabling SSL compilation")
            self.ext_modules = [Extension('ssl', ['ssl.c'],
                        include_dirs=[incldirs],
                        library_dirs=[libdirs],
                        libraries=['ssl'])]
        else:
            self.announce(
"""Some necessary SSL files are missing, disabling SSL compilation.
Use "python setup.py build_ext -I<inclpath> -L<libpath>"
where the path arguments point to your SSL installation.""")

    def get_build_ext(self):
        c = self.get_command_obj('build_ext')
        c.ensure_finalized()
        return c

    def additional_things(self):
        """replace path names and program information in various files"""
        self.announce("Filling template values.")
        inst = self.get_command_obj("install")
        inst.ensure_finalized()
        data = {
          'install_data': inst.install_data,
          "install_scripts": change_root_inv(inst.root, inst.install_scripts),
          "syspath": "# sys.path augmentation not needed",
          'author': self.get_author(),
          'version': self.get_version(),
          'url': self.get_url(),
          'appname': self.get_name(),
          'email': self.get_author_email(),
          'long_description': self.get_long_description(),
          'python': os.path.normpath(sys.executable),
        }
        files = [
            'linkchecker',
            'linkchecker.bat',
            'test/profiletest.py',
            'linkcheck/__init__.py',
            'linkcheck/Config.py',
            'install.py',
            'README',
        ]
        for name in files:
            t = Template(name+".tmpl")
            f = open(name,"w")
            f.write(t.fill_in(data))
            f.close()
        # append system specific files
        if os.name=='nt':
            self.scripts.append('linkchecker.bat')
        elif os.name=='posix':
            self.data_files.append(('/etc', ['linkcheckerrc']))


setup (name = "LinkChecker",
       version = "1.2.5",
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
       packages = ['','DNS','linkcheck'],
       scripts = ['linkchecker'],
       data_files = [('share/locale/de/LC_MESSAGES',
                      ['locale/de/LC_MESSAGES/linkcheck.mo',
		       'locale/de/LC_MESSAGES/linkcheck.po']),
                     ('share/locale/fr/LC_MESSAGES',
                      ['locale/fr/LC_MESSAGES/linkcheck.mo',
		       'locale/fr/LC_MESSAGES/linkcheck.po']),
		    ],
)
