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
- py2exe support (including InnoScript installer generation)
- py2app support (including DMG package generation)
- cx_Freeze support
- Qt plugin installation for py2exe and py2app
- Microsoft Visual C++ DLL installation for py2exe
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

# if a frozen Unix application should be built with cx_Freeze
do_freeze = int(os.environ.get('LINKCHECKER_FREEZE', '0'))

# import Distutils stuff
try:
    # setuptools (which is needed by py2app) monkey-patches the
    # distutils.core.Command class.
    # So we need to import it before importing the distutils core
    import setuptools
except ImportError:
    # ignore when setuptools is not installed
    setuptools = None
if do_freeze:
    from cx_Freeze import setup, Executable
else:
    from distutils.core import setup
from distutils.core import Extension
from distutils.command.install_lib import install_lib
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.dir_util import remove_tree
from distutils.file_util import write_file
from distutils.spawn import find_executable
from distutils import util, log
try:
    # py2exe monkey-patches the distutils.core.Distribution class
    # So we need to import it before importing the Distribution class
    import py2exe
    has_py2exe = True
except ImportError:
    # py2exe is not installed
    has_py2exe = False
if do_freeze:
    from cx_Freeze.dist import Distribution, build, install_exe
    executables = [Executable("linkchecker"), Executable("linkchecker-gui")]
else:
    from distutils.core import Distribution
    from distutils.command.build import build
    executables = None
try:
    import py2app
    has_py2app = True
except ImportError:
    # py2app is not installed
    has_py2app = False

# the application version
AppVersion = "9.2"
# the application name
AppName = "LinkChecker"

# Microsoft Visual C++ runtime version (tested with Python 2.7.2)
MSVCP90Version = '9.0.30729.6161'
MSVCP90Suffix = 'x-ww_31a54e43'
MSVCP90Token = '1fc8b3b9a1e18e3b'

# basic includes for py2exe and py2app
py_includes = ['dns.rdtypes.IN.*', 'dns.rdtypes.ANY.*',
    'twill.extensions.*', 'twill.extensions.match_parse.*',
    'twill.other_packages.*', 'twill.other_packages._mechanize_dist.*',
    'linkcheck.logger.*',
]
# basic excludes for py2exe and py2app
py_excludes = ['doctest', 'unittest', 'argcomplete', 'Tkinter',
    'PyQt4.QtDesigner', 'PyQt4.QtNetwork', 'PyQt4.QtOpenGL',
    'PyQt4.QtScript', 'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml',
    'PyQt4.phonon',
]
# py2exe options for Windows packaging
py2exe_options = dict(
    packages=["encodings"],
    excludes=py_excludes + ['win32com.gen_py'],
    # silence py2exe error about not finding msvcp90.dll
    dll_excludes=['MSVCP90.dll'],
    # add sip so that PyQt4 works
    # add PyQt4.QtSql so that sqlite needed by QHelpCollection works
    includes=py_includes + ["sip", "PyQt4.QtSql"],
    compressed=1,
    optimize=2,
)
# py2app options for OSX packaging
py2app_options = dict(
    includes=py_includes + ['sip', 'PyQt4',
      'PyQt4.QtCore', 'PyQt4.QtGui', 'PyQt4.QtSql'],
    excludes=py_excludes,
    strip=True,
    optimize=2,
    iconfile='doc/html/favicon.icns',
    plist={
        'CFBundleIdentifier': 'org.pythonmac.%s' % AppName,
        'CFBundleIconFile': 'favicon.icns',
    },
    argv_emulation=True,
)
# cx_Freeze for Linux RPM packaging
cx_includes = [x[:-2] for x in py_includes]
cxfreeze_options = dict(
    packages=["encodings"],
    excludes=py_excludes,
    includes=cx_includes + ['sip', 'PyQt4',
      'PyQt4.QtCore', 'PyQt4.QtGui', 'PyQt4.QtSql'],
)


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


def get_nt_platform_vars ():
    """Return program file path and architecture for NT systems."""
    platform = util.get_platform()
    if platform == "win-amd64":
        # the Visual C++ runtime files are installed in the x86 directory
        progvar = "%ProgramFiles(x86)%"
        architecture = "amd64"
    elif platform == "win32":
        progvar = "%ProgramFiles%"
        architecture = "x86"
    else:
        raise ValueError("Unsupported platform %r" % platform)
    return os.path.expandvars(progvar), architecture


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


def get_qt_plugin_dir_win ():
    """Get Qt plugin dir on Windows systems."""
    import PyQt4
    return os.path.join(os.path.dirname(PyQt4.__file__), "plugins")


def get_qt_plugin_dir_osx ():
    """Get Qt plugin dir on OSX systems."""
    # note: works on Qt installed with homebrew
    qtbindir = os.path.dirname(os.path.realpath(find_executable("qmake")))
    return os.path.join(os.path.dirname(qtbindir), "plugins")


def add_qt_plugin_file (files, plugin_dir, dirname, filename):
    """Add one Qt plugin file to list of data files."""
    files.append((dirname, [os.path.join(plugin_dir, dirname, filename)]))


def add_qt_plugin_files (files):
    """Add needed Qt plugins to list of data files. Filename prefix and
    suffix are different for Windows and OSX."""
    if os.name == 'nt':
        plugin_dir = get_qt_plugin_dir_win()
        args = ("", "4.dll")
    elif sys.platform == 'darwin':
        plugin_dir = get_qt_plugin_dir_osx()
        args = ("lib", ".dylib")
    else:
        raise ValueError("unsupported qt plugin platform")
    # Copy needed sqlite plugin files to distribution directory.
    add_qt_plugin_file(files, plugin_dir, "sqldrivers", "%sqsqlite%s" % args)
    # Copy needed gif image plugin files to distribution directory.
    add_qt_plugin_file(files, plugin_dir, "imageformats", "%sqgif%s" % args)


def fix_qt_plugins_py2app (dist_dir):
    """Fix Qt plugin files installed in data_dir by moving them to
    app_dir/Plugins and change the install_name."""
    app_dir = os.path.join(dist_dir, '%s.app' % AppName, 'Contents')
    plugin_dir = os.path.join(app_dir, 'Plugins')
    data_dir = os.path.join(app_dir, 'Resources')
    qt_lib_dir = os.path.join(os.path.dirname(get_qt_plugin_dir_osx()), 'lib')
    # make target plugin directory
    os.mkdir(plugin_dir)
    qt_plugins = ('sqldrivers', 'imageformats')
    qt_modules = ('QtCore', 'QtGui', 'QtSql')
    for plugin in qt_plugins:
        target_dir = os.path.join(plugin_dir, plugin)
        # move libraries
        os.rename(os.path.join(data_dir, plugin), target_dir)
        # fix libraries
        for library in glob.glob("%s/*.dylib" % target_dir):
            for module in qt_modules:
                libpath = "%s.framework/Versions/4/%s" % (module, module)
                oldpath = os.path.join(qt_lib_dir, libpath)
                newpath = '@executable_path/../Frameworks/%s' % libpath
                args = ['install_name_tool', '-change', oldpath, newpath, library]
                subprocess.check_call(args)


def generate_dmg_image (dist_dir):
    """Generate .dmg image."""
    imgPath = os.path.join(dist_dir, "%s-%s.dmg" % (AppName, AppVersion))
    tmpImgPath = os.path.join(dist_dir, "%s.tmp.dmg" % AppName)
    print("*** generating temporary DMG image ***")
    args = ['hdiutil', 'create', '-srcfolder', dist_dir, '-fs', 'HFSX',
            '-volname', AppName, '-format', 'UDZO', tmpImgPath]
    subprocess.check_call(args)
    print("*** generating final DMG image ***")
    args = ['hdiutil', 'convert', tmpImgPath, '-format', 'UDZO',
            '-imagekey', 'zlib-level=9', '-o', imgPath]
    subprocess.check_call(args)
    os.remove(tmpImgPath)


def sign_the_code (dist_dir):
    """Sign the OSX application code."""
    app_dir = os.path.join(dist_dir, "%s.app" % AppName)
    args = ['codesign', '-s', myname, '-v', app_dir]
    print("*** signing the application code ***")
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError, msg:
        print("WARN: codesigning failed", msg)


def add_msvc_files (files):
    """Add needed MSVC++ runtime files. Only Version 9.0.21022.8 is tested
    and can be downloaded here:
    http://www.microsoft.com/en-us/download/details.aspx?id=5582
    """
    prog_dir, architecture = get_nt_platform_vars()
    dirname = "Microsoft.VC90.CRT"
    version = "%s_%s_%s" % (MSVCP90Token, MSVCP90Version, MSVCP90Suffix)
    args = (architecture, dirname, version)
    path = r'C:\Windows\WinSxS\%s_%s_%s\*.*' % args
    files.append((dirname, glob.glob(path)))
    # Copy the manifest file into the build directory and rename it
    # because it must have the same name as the directory.
    path = r'C:\Windows\WinSxS\Manifests\%s_%s_%s.manifest' % args
    target = os.path.join(os.getcwd(), 'build', '%s.manifest' % dirname)
    shutil.copy(path, target)
    files.append((dirname, [target]))


def add_requests_cert_file(files):
    """Add Python requests .pem file for installers."""
    import requests
    filename = os.path.join(os.path.dirname(requests.__file__), 'cacert.pem')
    dirname = 'share/linkchecker'
    files.append((dirname, [filename]))


def insert_dns_path():
    """Let py2exe, py2app and cx_Freeze find the dns package."""
    lib_dir = "lib.%s-%s" % (util.get_platform(), sys.version[0:3])
    if hasattr(sys, 'gettotalrefcount'):
        lib_dir += '-pydebug'
    dnspath = os.path.abspath(os.path.join('build', lib_dir, 'linkcheck_dns'))
    if dnspath not in sys.path:
        sys.path.insert(0, dnspath)


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
    """Handle locale files and permissions."""

    def run (self):
        """Adjust permissions on POSIX systems."""
        self.add_message_files()
        super(MyInstallData, self).run()
        self.fix_permissions()

    def add_message_files (self):
        """Add locale message files to data_files list."""
        for (src, dst) in list_message_files(self.distribution.get_name()):
            dstdir = os.path.dirname(dst)
            self.data_files.append((dstdir, [os.path.join("build", dst)]))

    def fix_permissions (self):
        """Set correct read permissions on POSIX systems. Might also
        be possible by setting umask?"""
        if os.name == 'posix' and not self.dry_run:
            # Make the data files we just installed world-readable,
            # and the directories world-executable as well.
            for path in self.get_outputs():
                mode = os.stat(path)[stat.ST_MODE]
                if stat.S_ISDIR(mode):
                    mode |= 011
                mode |= 044
                os.chmod(path, mode)


# Microsoft application manifest for linkchecker-gui.exe; see also
# http://msdn.microsoft.com/en-us/library/aa374191%28VS.85%29.aspx
app_manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    type="win32"
    name="%(appname)s"
    version="%(appversion)s.0.0"
    processorArchitecture="*"
/>
<dependency>
  <dependentAssembly>
    <assemblyIdentity
      type="win32"
      name="Microsoft.VC90.CRT"
      version="%(msvcrtversion)s"
      processorArchitecture="*"
      publicKeyToken="%(msvcrttoken)s">
    </assemblyIdentity>
  </dependentAssembly>
</dependency>
</assembly>
""" % dict(appversion=AppVersion, appname=AppName,
           msvcrtversion=MSVCP90Version, msvcrttoken=MSVCP90Token)

class MyDistribution (Distribution, object):
    """Custom distribution class generating config file."""

    def __init__ (self, attrs):
        """Set console and windows scripts."""
        super(MyDistribution, self).__init__(attrs)
        self.console = ['linkchecker']
        self.windows = [{
            "script": "linkchecker-gui",
            "icon_resources": [(1, "doc/html/favicon.ico")],
            "other_resources": [(24, 1, app_manifest)],
        }]

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
    prog = "int main(){}\n"
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


def list_message_files (package, suffix=".po"):
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

    def build_message_files (self):
        """For each po/*.po, build .mo file in target locale directory."""
        # msgfmt.py is in the po/ subdirectory
        sys.path.append('po')
        import msgfmt
        for (src, dst) in list_message_files(self.distribution.get_name()):
            build_dst = os.path.join("build", dst)
            self.mkpath(os.path.dirname(build_dst))
            self.announce("Compiling %s -> %s" % (src, build_dst))
            msgfmt.make(src, build_dst)

    def run (self):
        """Check MANIFEST and build message files before building."""
        check_manifest()
        self.build_message_files()
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
scripts = ['linkchecker', 'linkchecker-gui']

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
        ['config/linkcheckerrc',
        'doc/html/lccollection.qhc', 'doc/html/lcdoc.qch']),
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

if os.name == 'posix':
    data_files.append(('share/man/man1', ['doc/en/linkchecker.1', 'doc/en/linkchecker-gui.1']))
    data_files.append(('share/man/man5', ['doc/en/linkcheckerrc.5']))
    data_files.append(('share/man/de/man1', ['doc/de/linkchecker.1', 'doc/de/linkchecker-gui.1']))
    data_files.append(('share/man/de/man5', ['doc/de/linkcheckerrc.5']))
    data_files.append(('share/linkchecker/examples',
              ['config/linkchecker-completion',
               'doc/examples/check_blacklist.sh',
               'doc/examples/check_for_x_errors.sh',
               'doc/examples/check_urls.sh']))
    data_files.append(('share/applications', ['doc/linkchecker.desktop']))
    data_files.append(('share/applications', ['doc/linkchecker-gui.desktop']))
if 'py2app' in sys.argv[1:]:
    if not has_py2app:
        raise SystemExit("py2app module could not be imported.")
    # add Qt plugins which are later fixed by fix_qt_plugins_py2app()
    add_qt_plugin_files(data_files)
    # needed for Qt to load the plugins
    data_files.append(('', ['osx/qt.conf']))
    add_requests_cert_file(data_files)
    insert_dns_path()
elif 'py2exe' in sys.argv[1:]:
    if not has_py2exe:
        raise SystemExit("py2exe module could not be imported")
    add_qt_plugin_files(data_files)
    add_msvc_files(data_files)
    add_requests_cert_file(data_files)
    insert_dns_path()
elif do_freeze:
    class MyInstallExe (install_exe, object):
        """Install cx_Freeze executables."""
        def run (self):
            """Add generated configuration to output files."""
            super(MyInstallExe, self).run()
            cmd_obj = self.distribution.get_command_obj("install_lib")
            cmd_obj.ensure_finalized()
            self.outfiles.append(cmd_obj.get_conf_output()+"c")
    insert_dns_path()


class InnoScript:
    """Class to generate INNO script."""

    def __init__(self, lib_dir, dist_dir, windows_exe_files=[],
                 console_exe_files=[], service_exe_files=[],
                 comserver_files=[], lib_files=[]):
        """Store INNO script infos."""
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = AppName
        self.version = AppVersion
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.console_exe_files = [self.chop(p) for p in console_exe_files]
        self.service_exe_files = [self.chop(p) for p in service_exe_files]
        self.comserver_files = [self.chop(p) for p in comserver_files]
        self.lib_files = [self.chop(p) for p in lib_files]
        self.icon = os.path.abspath(r'doc\html\favicon.ico')

    def chop(self, pathname):
        """Remove distribution directory from path name."""
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]

    def create(self, pathname=r"dist\omt.iss"):
        """Create Inno script."""
        self.pathname = pathname
        self.distfilebase = "%s-%s" % (self.name, self.version)
        self.distfile = self.distfilebase + ".exe"
        with codecs.open(self.pathname, "w", 'utf-8-sig', 'strict') as fd:
            self.write_inno_script(fd)

    def write_inno_script (self, fd):
        """Write Inno script contents."""
        print("; WARNING: This script has been created by py2exe. Changes to this script", file=fd)
        print("; will be overwritten the next time py2exe is run!", file=fd)
        print("[Setup]", file=fd)
        print("AppName=%s" % self.name, file=fd)
        print("AppVerName=%s %s" % (self.name, self.version), file=fd)
        print(r"DefaultDirName={pf}\%s" % self.name, file=fd)
        print("DefaultGroupName=%s" % self.name, file=fd)
        print("OutputBaseFilename=%s" % self.distfilebase, file=fd)
        print("OutputDir=..", file=fd)
        print("SetupIconFile=%s" % self.icon, file=fd)
        print("UninstallDisplayIcon=%s" % self.icon, file=fd)
        print(file=fd)
        # Customize some messages
        print("[Messages]", file=fd)
        print("ConfirmUninstall=Are you sure you want to remove %1? Note that user-specific configuration files of %1 are not removed.", file=fd)
        print("BeveledLabel=DON'T PANIC", file=fd)
        print(file=fd)
        # List of source files
        files = self.windows_exe_files + \
                self.console_exe_files + \
                self.service_exe_files + \
                self.comserver_files + \
                self.lib_files
        print('[Files]', file=fd)
        for path in files:
            print(r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path)), file=fd)
        print(file=fd)
        # Set icon filename
        print('[Icons]', file=fd)
        for path in self.windows_exe_files:
            print(r'Name: "{group}\%s"; Filename: "{app}\%s"' % \
                  (self.name, path), file=fd)
        print(r'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name, file=fd)
        print(file=fd)
        # Uninstall registry keys
        print('[Registry]', file=fd)
        print(r'Root: HKCU; Subkey: "Software\Bastian\LinkChecker"; Flags: uninsdeletekey', file=fd)
        print(file=fd)
        # Uninstall optional log files
        print('[UninstallDelete]', file=fd)
        for path in (self.windows_exe_files + self.console_exe_files):
            exename = os.path.basename(path)
            print(r'Type: files; Name: "{pf}\%s\%s.log"' % (self.name, exename), file=fd)
        print(file=fd)

    def compile (self):
        """Compile Inno script with iscc.exe."""
        progpath = get_nt_platform_vars()[0]
        cmd = r'%s\Inno Setup 5\iscc.exe' % progpath
        subprocess.check_call([cmd, self.pathname])

    def sign (self):
        """Sign InnoSetup installer with local self-signed certificate."""
        print("*** signing the inno setup installer ***")
        pfxfile = r'windows\linkchecker.pfx'
        if os.path.isfile(pfxfile):
            path = get_windows_sdk_path()
            signtool = os.path.join(path, "bin", "signtool.exe")
            if os.path.isfile(signtool):
                cmd = [signtool, 'sign', '/f', pfxfile, self.distfile]
                subprocess.check_call(cmd)
            else:
                print("No signed installer: signtool.exe not found.")
        else:
            print("No signed installer: certificate %s not found." % pfxfile)

def get_windows_sdk_path():
    """Return path of Microsoft Windows SDK installation, or None if
    not found."""
    try:
        import _winreg as winreg
    except ImportError:
        import winreg
    sub_key = r"Software\Microsoft\Microsoft SDKs\Windows"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key) as key:
        name = "CurrentInstallFolder"
        return winreg.QueryValueEx(key, name)[0]
    return None

try:
    from py2exe.build_exe import py2exe as py2exe_build

    class MyPy2exe (py2exe_build):
        """First builds the exe file(s), then creates a Windows installer.
        Needs InnoSetup to be installed."""

        def run (self):
            """Generate py2exe installer."""
            # First, let py2exe do it's work.
            py2exe_build.run(self)
            print("*** preparing the inno setup script ***")
            lib_dir = self.lib_dir
            dist_dir = self.dist_dir
            # create the Installer, using the files py2exe has created.
            script = InnoScript(lib_dir, dist_dir, self.windows_exe_files,
                self.console_exe_files, self.service_exe_files,
                self.comserver_files, self.lib_files)
            print("*** creating the inno setup script ***")
            script.create()
            print("*** compiling the inno setup script ***")
            script.compile()
            script.sign()
except ImportError:
    class MyPy2exe:
        """Dummy py2exe class."""
        pass


try:
    from py2app.build_app import py2app as py2app_build

    class MyPy2app (py2app_build):
        """First builds the app file(s), then creates a DMG installer.
        Needs hdiutil to be installed."""

        def run (self):
            """Generate py2app installer."""
            # First, let py2app do it's work.
            py2app_build.run(self)
            # Fix install names for Qt plugin libraries.
            fix_qt_plugins_py2app(self.dist_dir)
            sign_the_code(self.dist_dir)
            generate_dmg_image(self.dist_dir)

except ImportError:
    class MyPy2app:
        """Dummy py2app class."""
        pass


args = dict(
    name = AppName,
    version = AppVersion,
    description = "check links in web documents or full websites",
    keywords = "link,url,site,checking,crawling,verification,validation",
    author = myname,
    author_email = myemail,
    maintainer = myname,
    maintainer_email = myemail,
    url = "http://wummel.github.io/linkchecker/",
    license = "GPL",
    long_description = """Linkchecker features:

o recursive and multithreaded checking and site crawling
o output in colored or normal text, HTML, SQL, CSV, XML or a sitemap graph in different formats
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Telnet and local file links support
o restrict link checking with regular expression filters for URLs
o proxy support
o username/password authorization for HTTP, FTP and Telnet
o honors robots.txt exclusion protocol
o Cookie support
o HTML5 support
o HTML and CSS syntax check
o Antivirus check
o a command line, GUI and web interface

""",
    distclass = MyDistribution,
    cmdclass = {
        'install_lib': MyInstallLib,
        'install_data': MyInstallData,
        'build_ext': MyBuildExt,
        'build': MyBuild,
        'clean': MyClean,
        'sdist': MySdist,
        'py2exe': MyPy2exe,
        'py2app': MyPy2app,
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
        'linkcheck.gui',
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
        "py2exe": py2exe_options,
        "py2app": py2app_options,
        "build_exe": cxfreeze_options,
    },
    # Requirements, usable with setuptools or the new Python packaging module.
    # Commented out since they are untested and not officially supported.
    # See also doc/install.txt for more detailed dependency documentation.
    #extra_requires = {
    #    "IP country info": ['GeoIP'], # http://www.maxmind.com/app/python
    #    "Login form": ['twill'], # http://twill.idyll.org/
    #    "GNOME proxies": ['pygtk'], # http://www.pygtk.org/downloads.html
    #    "Bash completion": ['argcomplete'], # https://pypi.python.org/pypi/argcomplete
    #    "Memory debugging": ['meliae'], # https://launchpad.net/meliae
    #}
)
if sys.platform == 'darwin':
    args["app"] = ['linkchecker-gui']
if executables:
    args["executables"] = executables
    args["cmdclass"]["install_exe"] = MyInstallExe
if setuptools is not None:
    args['install_requires'] = [
        'requests >= 2.2.0',
    ]
setup(**args)
