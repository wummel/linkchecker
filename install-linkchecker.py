# -*- coding: iso-8859-1 -*-
# snatched from pythoncard CVS
# Documentation is at:
# http://docs.python.org/dist/postinstallation-script.html

# THIS FILE IS ONLY FOR USE WITH MS WINDOWS
# It is run as parts of the bdist_wininst installer
# Be sure to build the installer with
# 'python setup.py --install-script=install-linkchecker.py'
# or insert this into setup.cfg:
# [bdist_wininst]
# install-script=install-linkchecker.py

import sys
if not sys.platform.startswith('win'):
    # not for us
    sys.exit()
if not (hasattr(sys, 'version_info') or
        sys.version_info < (2, 5, 0, 'final', 0)):
    raise SystemExit("This program requires Python 2.5 or later.")
from __future__ import with_statement
import os
import re
import platform

# releases supporting our special .bat files
# XXX what is platform.release() on Vista?
win_bat_releases = ['NT', 'XP', '2000', '2003Server']

# path retrieving functions

def get_python_exe ():
    return os.path.join(sys.prefix, "python.exe")


def get_prg_path ():
    try:
        return get_special_folder_path("CSIDL_COMMON_PROGRAMS")
    except OSError:
        try:
            return get_special_folder_path("CSIDL_PROGRAMS")
        except OSError, reason:
            # give up - cannot install shortcuts
            print "cannot install shortcuts: %s" % reason
    sys.exit()


def get_dest_dir ():
    return os.path.join(get_prg_path(), "LinkChecker")


# install routines

def do_install ():
    fix_configdata()
    create_shortcuts()
    if platform.release() in win_bat_releases:
        script = os.path.join(sys.prefix, "Scripts", "linkchecker")
        handle_script(script)


def create_shortcuts ():
    """Create program shortcuts."""
    dest_dir = get_dest_dir()
    try:
        os.mkdir(dest_dir)
        directory_created(dest_dir)
    except OSError:
        pass
    if platform.release() in win_bat_releases:
        exe = os.path.join(sys.prefix, "Scripts", "linkchecker.bat")
        arguments = "--interactive"
    else:
        exe = get_python_exe()
        arguments = os.path.join(sys.prefix, "Scripts", "linkchecker")
        arguments += " --interactive"
    path = os.path.join(dest_dir, "Check URL.lnk")
    create_shortcut(exe, "Check URL", path, arguments)
    file_created(path)

    target = os.path.join(sys.prefix,
                          "share", "linkchecker", "doc", "documentation.html")
    path = os.path.join(dest_dir, "Documentation.lnk")
    create_shortcut(target, "Documentation", path)
    file_created(path)

    target = os.path.join(sys.prefix, "RemoveLinkChecker.exe")
    path = os.path.join(dest_dir, "Uninstall LinkChecker.lnk")
    arguments = '-u "%s"' % os.path.join(sys.prefix, "LinkChecker-wininst.log")
    create_shortcut(target, "Uninstall LinkChecker", path, arguments)
    file_created(path)
    print "See the shortcuts installed in the LinkChecker Programs Group"


def fix_configdata ():
    """Fix install and config paths in the config file."""
    name = "_linkchecker_configdata.py"
    conffile = os.path.join(sys.prefix, "Lib", "site-packages", name)
    lines = []
    for line in file(conffile):
        if line.startswith(("install_", "config_")):
            lines.append(fix_install_path(line))
        else:
            lines.append(line)
    with file(conffile, "w") as f:
        f.write("".join(lines))

# Windows install path scheme for python >= 2.3.
# Snatched from PC/bdist_wininst/install.c.
# This is used to fix install_* paths when installing on Windows.
win_path_scheme = {
    "purelib": ("PURELIB", "Lib\\site-packages\\"),
    "platlib": ("PLATLIB", "Lib\\site-packages\\"),
    # note: same as platlib because of C extensions, else it would be purelib
    "lib": ("PLATLIB", "Lib\\site-packages\\"),
    # 'Include/dist_name' part already in archive
    "headers": ("HEADERS", "."),
    "scripts": ("SCRIPTS", "Scripts\\"),
    "data": ("DATA", "."),
}

def fix_install_path (line):
    """Replace placeholders written by bdist_wininst with those specified
    in windows install path scheme."""
    key, eq, val = line.split()
    # unescape string (do not use eval())
    val = val[1:-1].replace("\\\\", "\\")
    for d in win_path_scheme.keys():
        # look for placeholders to replace
        oldpath, newpath = win_path_scheme[d]
        oldpath = "%s%s" % (os.sep, oldpath)
        if oldpath in val:
            val = val.replace(oldpath, newpath)
            val = os.path.join(sys.prefix, val)
            val = os.path.normpath(val)
    return "%s = %r%s" % (key, val, os.linesep)


# check if Python is called on the first line with this expression
first_line_re = re.compile('^#!.*python[0-9.]*([ \t].*)?$')

def handle_script (script):
    f = open(script, "r")
    first_line = f.readline()
    match = first_line_re.match(first_line)
    if match:
        post_interp = match.group(1) or ''
    else:
        post_interp = ""
    adjust(f, script, post_interp)
    f.close()


def adjust (f, script, post_interp):
    outfile = script+".bat"
    print "copying and adjusting %s -> %s" % (script, outfile)
    outf = open(outfile, "w")
    pat = '@"%s"%s -x "%%~f0" %%* & exit /b\n'
    outf.write(pat % (get_python_exe(), post_interp))
    outf.writelines(f.readlines())
    outf.close()
    file_created(outfile)


if __name__ == '__main__':
    if "-install" == sys.argv[1]:
        do_install()
    elif "-remove" == sys.argv[1]:
        # nothing to do since the created files are removed automatically
        pass

