#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Setup file for the distuils module.

It includes the following features:
- creation and installation of configuration files with installation data
- automatic detection and usage of GNU99 standard for C compiler
- automatic MANIFEST.in check
- automatic generation of .mo locale files
- automatic permission setting on POSIX systems for installed files

Because of all the features, this script is nasty and big.
Change it very carefully.
"""
from __future__ import print_function
import sys
if not (hasattr(sys, 'version_info') or
        sys.version_info < (2, 7, 0, 'final', 0)):
    raise SystemExit("This program requires Python 2.7 or later.")
import os
import re
import codecs
import subprocess
import stat
import glob
import shutil
try:
    unicode
except NameError:
    unicode = lambda x: x

# import Distutils stuff
from setuptools import setup
from distutils.core import Extension
from distutils.command.install_lib import install_lib
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.dir_util import remove_tree
from distutils.file_util import write_file
from distutils import util, log
from distutils.core import Distribution
from distutils.command.build import build

# the application version
AppVersion = "9.4"
# the application name
AppName = "LinkChecker"
Description = "check links in web documents or full websites"

def get_long_description():
    """Try to read long description from README.rst."""
    try:
        with open('README.rst') as f:
            return f.read()
    except:
        return Description

def normpath (path):
    """Norm a path name to platform specific notation."""
    return os.path.normpath(path)


def cnormpath (path):
    """Norm a path name to platform specific notation and make it absolute."""
    path = normpath(path)
    if os.name == 'nt':
        # replace slashes with backslashes
        path = path.replace("/", "\\")
    if not os.path.isabs(path):
        path = normpath(os.path.join(sys.prefix, path))
    return path


release_ro = re.compile(r"\(released (.+)\)")
def get_release_date ():
    """Parse and return relase date as string from doc/changelog.txt."""
    fname = os.path.join("doc", "changelog.txt")
    release_date = "unknown"
    with open(fname) as fd:
        # the release date is on the first line
        line = fd.readline()
        mo = release_ro.search(line)
        if mo:
            release_date = mo.groups(1)
    return release_date


def get_portable():
    """Return portable flag as string."""
    return os.environ.get('LINKCHECKER_PORTABLE', '0')


class MyInstallLib (install_lib, object):
    """Custom library installation."""

    def install (self):
        """Install the generated config file."""
        outs = super(MyInstallLib, self).install()
        infile = self.create_conf_file()
        outfile = os.path.join(self.install_dir, os.path.basename(infile))
        self.copy_file(infile, outfile)
        outs.append(outfile)
        return outs

    def create_conf_file (self):
        """Create configuration file."""
        cmd_obj = self.distribution.get_command_obj("install")
        cmd_obj.ensure_finalized()
        # we have to write a configuration file because we need the
        # <install_data> directory (and other stuff like author, url, ...)
        # all paths are made absolute by cnormpath()
        data = []
        for d in ['purelib', 'platlib', 'lib', 'headers', 'scripts', 'data']:
            attr = 'install_%s' % d
            if cmd_obj.root:
                # cut off root path prefix
                cutoff = len(cmd_obj.root)
                # don't strip the path separator
                if cmd_obj.root.endswith(os.sep):
                    cutoff -= 1
                val = getattr(cmd_obj, attr)[cutoff:]
            else:
                val = getattr(cmd_obj, attr)
            if attr == 'install_data':
                cdir = os.path.join(val, "share", "linkchecker")
                data.append('config_dir = %r' % cnormpath(cdir))
            elif attr == 'install_lib':
                if cmd_obj.root:
                    _drive, tail = os.path.splitdrive(val)
                    if tail.startswith(os.sep):
                        tail = tail[1:]
                    self.install_lib = os.path.join(cmd_obj.root, tail)
                else:
                    self.install_lib = val
            data.append("%s = %r" % (attr, cnormpath(val)))
        self.distribution.create_conf_file(data, directory=self.install_lib)
        return self.get_conf_output()

    def get_conf_output (self):
        """Get name of configuration file."""
        return self.distribution.get_conf_filename(self.install_lib)

    def get_outputs (self):
        """Add the generated config file to the list of outputs."""
        outs = super(MyInstallLib, self).get_outputs()
        conf_output = self.get_conf_output()
        outs.append(conf_output)
        if self.compile:
            outs.extend(self._bytecode_filenames([conf_output]))
        return outs


class MyInstallData (install_data, object):
    """Fix file permissions."""

    def run (self):
        """Adjust permissions on POSIX systems."""
        super(MyInstallData, self).run()
        self.fix_permissions()

    def fix_permissions (self):
        """Set correct read permissions on POSIX systems. Might also
        be possible by setting umask?"""
        if os.name == 'posix' and not self.dry_run:
            # Make the data files we just installed world-readable,
            # and the directories world-executable as well.
            for path in self.get_outputs():
                mode = os.stat(path)[stat.ST_MODE]
                if stat.S_ISDIR(mode):
                    mode |= 0o11
                mode |= 0o44
                os.chmod(path, mode)


class MyDistribution (Distribution, object):
    """Custom distribution class generating config file."""

    def __init__ (self, attrs):
        """Set console and windows scripts."""
        super(MyDistribution, self).__init__(attrs)
        self.console = ['linkchecker']

    def run_commands (self):
        """Generate config file and run commands."""
        cwd = os.getcwd()
        data = []
        data.append('config_dir = %r' % os.path.join(cwd, "config"))
        data.append("install_data = %r" % cwd)
        data.append("install_scripts = %r" % cwd)
        self.create_conf_file(data)
        super(MyDistribution, self).run_commands()

    def get_conf_filename (self, directory):
        """Get name for config file."""
        return os.path.join(directory, "_%s_configdata.py" % self.get_name())

    def create_conf_file (self, data, directory=None):
        """Create local config file from given data (list of lines) in
        the directory (or current directory if not given)."""
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
                     "contact_email")
        for name in metanames:
            method = "get_" + name
            val = getattr(self.metadata, method)()
            if isinstance(val, str):
                val = unicode(val)
            cmd = "%s = %r" % (name, val)
            data.append(cmd)
        data.append('release_date = "%s"' % get_release_date())
        data.append('portable = %s' % get_portable())
        # write the config file
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose >= 1, self.dry_run)


def cc_run (args):
    """Run the C compiler with a simple main program.

    @return: successful exit flag
    @rtype: bool
    """
    prog = b"int main(){}\n"
    pipe = subprocess.Popen(args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    pipe.communicate(input=prog)
    if os.WIFEXITED(pipe.returncode):
        return os.WEXITSTATUS(pipe.returncode) == 0
    return False


def cc_supports_option (cc, option):
    """Check if the given C compiler supports the given option.

    @return: True if the compiler supports the option, else False
    @rtype: bool
    """
    return cc_run([cc[0], "-E", option, "-"])


class MyBuildExt (build_ext, object):
    """Custom build extension command."""

    def build_extensions (self):
        """Add -std=gnu99 to build options if supported."""
        # For gcc >= 3 we can add -std=gnu99 to get rid of warnings.
        extra = []
        if self.compiler.compiler_type == 'unix':
            option = "-std=gnu99"
            if cc_supports_option(self.compiler.compiler, option):
                extra.append(option)
        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            for opt in extra:
                if opt not in ext.extra_compile_args:
                    ext.extra_compile_args.append(opt)
            self.build_extension(ext)


def list_message_files (package, suffix=".mo"):
    """Return list of all found message files and their installation paths."""
    for fname in glob.glob("po/*" + suffix):
        # basename (without extension) is a locale name
        localename = os.path.splitext(os.path.basename(fname))[0]
        domainname = "%s.mo" % package.lower()
        yield (fname, os.path.join(
            "share", "locale", localename, "LC_MESSAGES", domainname))


def check_manifest ():
    """Snatched from roundup.sf.net.
    Check that the files listed in the MANIFEST are present when the
    source is unpacked."""
    try:
        f = open('MANIFEST')
    except Exception:
        print('\n*** SOURCE WARNING: The MANIFEST file is missing!')
        return
    try:
        manifest = [l.strip() for l in f.readlines() if not l.startswith('#')]
    finally:
        f.close()
    err = [line for line in manifest if not os.path.exists(line)]
    if err:
        n = len(manifest)
        print('\n*** SOURCE WARNING: There are files missing (%d/%d found)!' %
            (n - len(err), n))
        print('\nMissing: '.join(err))


class MyBuild (build, object):
    """Custom build command."""

    def run (self):
        """Check MANIFEST before building."""
        check_manifest()
        build.run(self)


class MyClean (clean, object):
    """Custom clean command."""

    def run (self):
        """Remove share directory on clean."""
        if self.all:
            # remove share directory
            directory = os.path.join("build", "share")
            if os.path.exists(directory):
                remove_tree(directory, dry_run=self.dry_run)
            else:
                log.warn("'%s' does not exist -- can't clean it", directory)
        clean.run(self)


class MySdist (sdist, object):
    """Custom sdist command."""

    def get_file_list (self):
        """Add MANIFEST to the file list."""
        super(MySdist, self).get_file_list()
        self.filelist.append("MANIFEST")


# global include dirs
include_dirs = []
# global macros
define_macros = []
# compiler args
extra_compile_args = []
# library directories
library_dirs = []
# libraries
libraries = []
# scripts
scripts = ['linkchecker']

if os.name == 'nt':
    # windows does not have unistd.h
    define_macros.append(('YY_NO_UNISTD_H', None))
else:
    extra_compile_args.append("-pedantic")

if sys.platform == 'darwin':
    define_macros.extend([('HAVE_STRLCPY', None), ('HAVE_STRLCAT', None)])

myname = "Bastian Kleineidam"
myemail = "bastian.kleineidam@web.de"

data_files = [
    ('share/linkchecker',
        ['config/linkcheckerrc']),
    ('share/linkchecker/examples',
        ['cgi-bin/lconline/leer.html.en',
         'cgi-bin/lconline/leer.html.de',
         'cgi-bin/lconline/index.html',
         'cgi-bin/lconline/lc_cgi.html.en',
         'cgi-bin/lconline/lc_cgi.html.de',
         'cgi-bin/lconline/check.js',
         'cgi-bin/lc.wsgi',
         'config/linkchecker.apache2.conf',
        ]),
]

for (src, dst) in list_message_files(AppName):
    data_files.append((dst, [src]))

if os.name == 'posix':
    data_files.append(('share/man/man1', ['doc/en/linkchecker.1']))
    data_files.append(('share/man/man5', ['doc/en/linkcheckerrc.5']))
    data_files.append(('share/man/de/man1', ['doc/de/linkchecker.1']))
    data_files.append(('share/man/de/man5', ['doc/de/linkcheckerrc.5']))
    data_files.append(('share/linkchecker/examples',
              ['config/linkchecker-completion',
               'doc/examples/check_blacklist.sh',
               'doc/examples/check_for_x_errors.sh',
               'doc/examples/check_urls.sh']))
    data_files.append(('share/applications', ['doc/linkchecker.desktop']))

args = dict(
    name = AppName,
    version = AppVersion,
    description = Description,
    keywords = "link,url,site,checking,crawling,verification,validation",
    author = myname,
    author_email = myemail,
    maintainer = myname,
    maintainer_email = myemail,
    url = "http://wummel.github.io/linkchecker/",
    license = "GPL",
    long_description = get_long_description(),
    distclass = MyDistribution,
    cmdclass = {
        'install_lib': MyInstallLib,
        'install_data': MyInstallData,
        'build_ext': MyBuildExt,
        'build': MyBuild,
        'clean': MyClean,
        'sdist': MySdist,
    },
    package_dir = {
        'linkcheck_dns.dns': 'third_party/dnspython/dns',
    },
    packages = [
        'linkcheck',
        'linkcheck.bookmarks',
        'linkcheck.cache',
        'linkcheck.checker',
        'linkcheck.configuration',
        'linkcheck.director',
        'linkcheck.htmlutil',
        'linkcheck.HtmlParser',
        'linkcheck.logger',
        'linkcheck.network',
        'linkcheck.parser',
        'linkcheck.plugins',
        'linkcheck_dns.dns',
        'linkcheck_dns.dns.rdtypes',
        'linkcheck_dns.dns.rdtypes.ANY',
        'linkcheck_dns.dns.rdtypes.IN',
    ],
    ext_modules = [
        Extension('linkcheck.HtmlParser.htmlsax',
            sources = [
                'linkcheck/HtmlParser/htmllex.c',
                'linkcheck/HtmlParser/htmlparse.c',
                'linkcheck/HtmlParser/s_util.c',
            ],
            extra_compile_args = extra_compile_args,
            library_dirs = library_dirs,
            libraries = libraries,
            define_macros = define_macros + [('YY_NO_INPUT', None)],
            include_dirs = include_dirs + [normpath("linkcheck/HtmlParser")],
        ),
        Extension("linkcheck.network._network",
            sources = ["linkcheck/network/_network.c"],
            extra_compile_args = extra_compile_args,
            library_dirs = library_dirs,
            libraries = libraries,
            define_macros = define_macros,
            include_dirs = include_dirs,
        ),
    ],
    scripts = scripts,
    data_files = data_files,
    classifiers = [
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: C',
    ],
    options = {
    },
    # Requirements, usable with setuptools or the new Python packaging module.
    # Commented out since they are untested and not officially supported.
    # See also doc/install.txt for more detailed dependency documentation.
    #extra_requires = {
    #    "IP country info": ['GeoIP'], # http://www.maxmind.com/app/python
    #    "GNOME proxies": ['pygtk'], # http://www.pygtk.org/downloads.html
    #    "Bash completion": ['argcomplete'], # https://pypi.python.org/pypi/argcomplete
    #    "Memory debugging": ['meliae'], # https://launchpad.net/meliae
    #}
)
setup(**args)
