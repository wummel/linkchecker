#!/usr/bin/env python
from distutils.core import setup
from distutils.dist import Distribution
from Template import Template
import sys,os,string

# Autodetect the existence of an SSL library (this is pretty shitty)
# Autodetect Windows platforms to include the linkchecker.bat script
class LCDistribution(Distribution):
    default_include_dirs = ['/usr/include/openssl',
                            '/usr/local/include/openssl']
    def run_commands (self):
        self.check_ssl()
        self.check_windows()
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

    def check_windows(self):
        if sys.platform=='win32':
            inst = self.find_command_obj("install")
            inst.ensure_ready()
            t = Template("linkchecker.bat.tmpl")
            f = open("linkchecker.bat","w")
	    f.write(t.fill_in({"path_to_linkchecker": inst.install_scripts}))
            f.close()
            self.scripts.append('linkchecker.bat')

    def has_ssl(self):
        incls = self.find_command_obj("build_ext").include_dirs
        incls = (incls and string.split(incls, os.pathsep)) or []
        for d in incls + self.default_include_dirs:
            if os.path.exists(os.path.join(d, "ssl.h")):
                return d
        return 0


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
o restrict link checking to your local domain
o HTTP proxy support
o give username/password for HTTP and FTP authorization
o robots.txt exclusion protocol support 
""",
       distclass = LCDistribution,
       packages = ['','DNS','linkcheck'],
       scripts = ['linkchecker'],
)
