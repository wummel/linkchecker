#!/usr/bin/python2.4
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
"""
Setup file for the distuils module.
"""

import sys
if not hasattr(sys, "version_info"):
    raise SystemExit, "This program requires Python 2.4 or later."
if sys.version_info < (2, 4, 0, 'final', 0):
    raise SystemExit, "This program requires Python 2.4 or later."
import os
import popen2
import platform
import stat
import string
import glob
from distutils.core import setup, Extension, DEBUG
from distutils.spawn import find_executable
import distutils.dist
from distutils.command.bdist_wininst import bdist_wininst
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.command.build_ext import build_ext
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.dir_util import remove_tree
from distutils.file_util import write_file
from distutils.sysconfig import get_python_version
from distutils.errors import DistutilsPlatformError
from distutils import util, log

# cross compile config
cc = os.environ.get("CC")
# directory with cross compiled (for win32) python
win_python_dir = "/home/calvin/src/python23-maint-cvs/dist/src/"
# if we are compiling for or under windows
win_compiling = (os.name == 'nt') or (cc is not None and "mingw32" in cc)
# releases supporting our special .bat files
win_bat_releases = ['NT', 'XP', '2000', '2003Server']


def normpath (path):
    """
    Norm a path name to platform specific notation.
    """
    return os.path.normpath(path)


def cnormpath (path):
    """
    Norm a path name to platform specific notation, but honoring
    the win_compiling flag.
    """
    path = normpath(path)
    if win_compiling:
        # replace slashes with backslashes
        path = path.replace("/", "\\")
    if not os.path.isabs(path):
        path= normpath(os.path.join(sys.prefix, path))
    return path


class MyInstall (install, object):

    def run (self):
        super(MyInstall, self).run()
        # we have to write a configuration file because we need the
        # <install_data> directory (and other stuff like author, url, ...)
        # all paths are made absolute by cnormpath()
        data = []
        for d in ['purelib', 'platlib', 'lib', 'headers', 'scripts', 'data']:
            attr = 'install_%s' % d
            if self.root:
                # cut off root path prefix
                cutoff = len(self.root)
                # don't strip the path separator
                if self.root.endswith(os.sep):
                    cutoff -= 1
                val = getattr(self, attr)[cutoff:]
            else:
                val = getattr(self, attr)
            if attr == 'install_data':
                cdir = os.path.join(val, "share", "linkchecker")
                data.append('config_dir = %r' % cnormpath(cdir))
            data.append("%s = %r" % (attr, cnormpath(val)))
        self.distribution.create_conf_file(data, directory=self.install_lib)

    def get_outputs (self):
        """
        Add the generated config file from distribution.create_conf_file()
        to the list of outputs.
        """
        outs = super(MyInstall, self).get_outputs()
        outs.append(self.distribution.get_conf_filename(self.install_lib))
        return outs

    # compatibility bugfix for Python << 2.5, << 2.4.1, << 2.3.5
    # XXX remove this method when depending on one of the above versions
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
    """
    My own data installer to handle permissions.
    """

    def run (self):
        """
        Adjust permissions on POSIX systems.
        """
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


class MyDistribution (distutils.dist.Distribution, object):
    """
    Custom distribution class generating config file.
    """

    def run_commands (self):
        """
        Generate config file and run commands.
        """
        cwd = os.getcwd()
        data = []
        data.append('config_dir = %r' % os.path.join(cwd, "config"))
        data.append("install_data = %r" % cwd)
        data.append("install_scripts = %r" % cwd)
        self.create_conf_file(data)
        super(MyDistribution, self).run_commands()

    def get_conf_filename (self, directory):
        """
        Get name for config file.
        """
        return os.path.join(directory, "_%s_configdata.py" % self.get_name())

    def create_conf_file (self, data, directory=None):
        """
        Create local config file from given data (list of lines) in
        the directory (or current directory if not given).
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
              val = getattr(self.metadata, method)()
              if isinstance(val, str):
                  val = unicode(val)
              cmd = "%s = %r" % (name, val)
              data.append(cmd)
        # write the config file
        data.append('appname = "LinkChecker"')
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)


class MyBdistWininst (bdist_wininst, object):
    """
    Custom bdist_wininst command supporting cross compilation.
    """

    def run (self):
        if (not win_compiling and
            (self.distribution.has_ext_modules() or
             self.distribution.has_c_libraries())):
            raise DistutilsPlatformError \
                  ("distribution contains extensions and/or C libraries; "
                   "must be compiled on a Windows 32 platform")

        if not self.skip_build:
            self.run_command('build')

        install = self.reinitialize_command('install', reinit_subcommands=1)
        install.root = self.bdist_dir
        install.skip_build = self.skip_build
        install.warn_dir = 0

        install_lib = self.reinitialize_command('install_lib')
        # we do not want to include pyc or pyo files
        install_lib.compile = 0
        install_lib.optimize = 0

        # If we are building an installer for a Python version other
        # than the one we are currently running, then we need to ensure
        # our build_lib reflects the other Python version rather than ours.
        # Note that for target_version!=sys.version, we must have skipped the
        # build step, so there is no issue with enforcing the build of this
        # version.
        target_version = self.target_version
        if not target_version:
            assert self.skip_build, "Should have already checked this"
            target_version = sys.version[0:3]
        plat_specifier = ".%s-%s" % (util.get_platform(), target_version)
        build = self.get_finalized_command('build')
        build.build_lib = os.path.join(build.build_base,
                                       'lib' + plat_specifier)

        # Use a custom scheme for the zip-file, because we have to decide
        # at installation time which scheme to use.
        for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
            value = string.upper(key)
            if key == 'headers':
                value = value + '/Include/$dist_name'
            setattr(install,
                    'install_' + key,
                    value)

        log.info("installing to %s", self.bdist_dir)
        install.ensure_finalized()

        # avoid warning of 'install_lib' about installing
        # into a directory not in sys.path
        sys.path.insert(0, os.path.join(self.bdist_dir, 'PURELIB'))

        install.run()

        del sys.path[0]

        # And make an archive relative to the root of the
        # pseudo-installation tree.
        from tempfile import mktemp
        archive_basename = mktemp()
        fullname = self.distribution.get_fullname()
        arcname = self.make_archive(archive_basename, "zip",
                                    root_dir=self.bdist_dir)
        # create an exe containing the zip-file
        self.create_exe(arcname, fullname, self.bitmap)
        # remove the zip-file again
        log.debug("removing temporary file '%s'", arcname)
        os.remove(arcname)

        if not self.keep_temp:
            remove_tree(self.bdist_dir, dry_run=self.dry_run)

    def get_exe_bytes (self):
        if win_compiling:
            # wininst-X.Y.exe is in the same directory as bdist_wininst
            directory = os.path.dirname(distutils.command.__file__)
            filename = os.path.join(directory, "wininst-7.1.exe")
            return open(filename, "rb").read()
        return super(MyBdistWininst, self).get_exe_bytes()


def cc_supports_option (cc, option):
    """
    Check if the given C compiler supports the given option.

    @return: True if the compiler supports the option, else False
    @rtype: bool
    """
    prog = "int main(){}\n"
    cc_cmd = "%s -E %s -" % (cc[0], option)
    pipe = popen2.Popen4(cc_cmd)
    pipe.tochild.write(prog)
    pipe.tochild.close()
    status = pipe.wait()
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status) == 0
    return False


def cc_remove_option (compiler, option):
    for optlist in (compiler.compiler, compiler.compiler_so):
        if option in optlist:
            optlist.remove(option)


class MyBuildExt (build_ext, object):
    """
    Custom build extension command.
    """

    def build_extensions (self):
        """
        Add -std=gnu99 to build options if supported.
        And compress extension libraries.
        """
        # For gcc >= 3 we can add -std=gnu99 to get rid of warnings.
        extra = []
        if self.compiler.compiler_type == 'unix':
            option = "-std=gnu99"
            if cc_supports_option(self.compiler.compiler, option):
                extra.append(option)
                if platform.machine() == 'm68k':
                    # work around ICE on m68k machines in gcc 4.0.1
                    cc_remove_option(self.compiler, "-O3")
        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            for opt in extra:
                if opt not in ext.extra_compile_args:
                    ext.extra_compile_args.append(opt)
            self.build_extension(ext)
        self.compress_extensions()

    def compress_extensions (self):
        """
        Run UPX compression over built extension libraries.
        """
        # currently upx supports only .dll files
        if os.name != 'nt':
            return
        upx = find_executable("upx")
        if upx is None:
            # upx not found
            return
        for filename in self.get_outputs():
            compress_library(upx, filename)


def compress_library (upx, filename):
    """
    Compresses a dynamic library file with upx (currently only .dll
    files are supported).
    """
    log.info("upx-compressing %s", filename)
    os.system('%s -q --best "%s"' % (upx, filename))


def list_message_files (package, suffix=".po"):
    """
    Return list of all found message files and their installation paths.
    """
    _files = glob.glob("po/*" + suffix)
    _list = []
    for _file in _files:
        # basename (without extension) is a locale name
        _locale = os.path.splitext(os.path.basename(_file))[0]
        _list.append((_file, os.path.join(
            "share", "locale", _locale, "LC_MESSAGES", "%s.mo" % package)))
    return _list


def check_manifest ():
    """
    Snatched from roundup.sf.net.
    Check that the files listed in the MANIFEST are present when the
    source is unpacked.
    """
    try:
        f = open('MANIFEST')
    except:
        print '\n*** SOURCE WARNING: The MANIFEST file is missing!'
        return
    try:
        manifest = [l.strip() for l in f.readlines()]
    finally:
        f.close()
    err = [line for line in manifest if not os.path.exists(line)]
    if err:
        n = len(manifest)
        print '\n*** SOURCE WARNING: There are files missing (%d/%d found)!'%(
            n-len(err), n)
        print 'Missing:', '\nMissing: '.join(err)


class MyBuild (build, object):
    """
    Custom build command.
    """

    def build_message_files (self):
        """
        For each po/*.po, build .mo file in target locale directory.
        """
        for (_src, _dst) in list_message_files(self.distribution.get_name()):
            _build_dst = os.path.join("build", _dst)
            self.mkpath(os.path.dirname(_build_dst))
            self.announce("Compiling %s -> %s" % (_src, _build_dst))
            from linkcheck import msgfmt
            msgfmt.make(_src, _build_dst)

    def run (self):
        check_manifest()
        self.build_message_files()
        build.run(self)


class MyClean (clean, object):
    """
    Custom clean command.
    """

    def run (self):
        if self.all:
            # remove share directory
            directory = os.path.join("build", "share")
            if os.path.exists(directory):
                remove_tree(directory, dry_run=self.dry_run)
            else:
                log.warn("'%s' does not exist -- can't clean it", directory)
        clean.run(self)


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
if win_compiling:
    scripts.append('install-linkchecker.py')

if os.name == 'nt':
    # windows does not have unistd.h
    define_macros.append(('YY_NO_UNISTD_H', None))
else:
    extra_compile_args.append("-pedantic")
    if win_compiling:
        # we are cross compiling with mingw
        # add directory for pyconfig.h
        include_dirs.append(win_python_dir)
        # add directory for Python.h
        include_dirs.append(os.path.join(win_python_dir, "Include"))
        # for finding libpythonX.Y.a
        library_dirs.append(win_python_dir)
        libraries.append("python%s" % get_python_version())

myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

data_files = [
         ('share/linkchecker',
             ['config/linkcheckerrc', 'config/logging.conf', ]),
         ('share/linkchecker/examples',
             ['cgi-bin/lconline/leer.html.en',
              'cgi-bin/lconline/leer.html.de',
              'cgi-bin/lconline/index.html',
              'cgi-bin/lconline/lc_cgi.html.en',
              'cgi-bin/lconline/lc_cgi.html.de',
              'cgi-bin/lconline/check.js',
              'cgi-bin/lc.cgi',
              'cgi-bin/lc.fcgi', ]),
      ]

if os.name == 'posix':
    data_files.append(('share/man/man1', ['doc/en/linkchecker.1']))
    data_files.append(('share/man/de/man1', ['doc/de/linkchecker.1']))
    data_files.append(('share/man/fr/man1', ['doc/fr/linkchecker.1']))
    data_files.append(('share/linkchecker/examples',
              ['config/linkchecker-completion', 'config/linkcheck-cron.sh']))
elif win_compiling:
    data_files.append(('share/linkchecker/doc',
             ['doc/en/documentation.html',
              'doc/en/index.html',
              'doc/en/install.html',
              'doc/en/other.html',
              'doc/en/upgrading.html',
              'doc/en/lc.css',
              'doc/en/navigation.css',
              'doc/en/shot1.png',
              'doc/en/shot2.png',
              'doc/en/shot1_thumb.jpg',
              'doc/en/shot2_thumb.jpg',
             ]))

setup (name = "linkchecker",
       version = "4.2",
       description = "check websites and HTML documents for broken links",
       keywords = "link,url,checking,verification",
       author = myname,
       author_email = myemail,
       maintainer = myname,
       maintainer_email = myemail,
       url = "http://linkchecker.sourceforge.net/",
       download_url = "http://sourceforge.net/project/showfiles.php?group_id=1913",
       license = "GPL",
       long_description = """Linkchecker features:
o recursive checking
o multithreaded
o output in colored or normal text, HTML, SQL, CSV, XML or a sitemap
  graph in different formats
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Gopher, Telnet and local
  file links support
o restrict link checking with regular expression filters for URLs
o proxy support
o username/password authorization for HTTP, FTP and Telnet
o robots.txt exclusion protocol support
o Cookie support
o i18n support
o a command line interface
o a (Fast)CGI web interface (requires HTTP server)
""",
       distclass = MyDistribution,
       cmdclass = {'install': MyInstall,
                   'install_data': MyInstallData,
                   'bdist_wininst': MyBdistWininst,
                   'build_ext': MyBuildExt,
                   'build': MyBuild,
                   'clean': MyClean,
                  },
       packages = ['linkcheck', 'linkcheck.logger', 'linkcheck.checker',
                   'linkcheck.director', 'linkcheck.configuration',
                   'linkcheck.cache',
                   'linkcheck.dns', 'linkcheck.dns.rdtypes',
                   'linkcheck.dns.rdtypes.ANY', 'linkcheck.dns.rdtypes.IN',
                   'linkcheck.HtmlParser', 'linkcheck.ftpparse', ],
       ext_modules = [Extension('linkcheck.HtmlParser.htmlsax',
                  sources = ['linkcheck/HtmlParser/htmllex.c',
                   'linkcheck/HtmlParser/htmlparse.c',
                   'linkcheck/HtmlParser/s_util.c',
                  ],
                  extra_compile_args = extra_compile_args,
                  library_dirs = library_dirs,
                  libraries = libraries,
                  define_macros = define_macros,
                  include_dirs = include_dirs + \
                                  [normpath("linkcheck/HtmlParser")],
                  ),
                  Extension("linkcheck.ftpparse._ftpparse",
                        ["linkcheck/ftpparse/_ftpparse.c",
                         "linkcheck/ftpparse/ftpparse.c"],
                  extra_compile_args = extra_compile_args,
                  library_dirs = library_dirs,
                  libraries = libraries,
                  define_macros = define_macros,
                  include_dirs = include_dirs + \
                                  [normpath("linkcheck/ftpparse")],
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
)
