# -*- coding: iso-8859-1 -*-
# snatched from pythoncard CVS

# THIS FILE IS ONLY FOR USE WITH MS WINDOWS
# It is run as parts of the bdist_wininst installer
# Be sure to build the installer with
# 'python setup.py --install-script=install-linkchecker.py'
# or insert this into setup.cfg:
# [bdist_wininst]
# install-script=install-linkchecker.py

# available functions:
# create_shortcut(target, description, filename[, arguments[,
#                 workdir[, iconpath[, iconindex]]]])
# - create shortcut
#
# file_created(path)
#  - register 'path' so that the uninstaller removes it
#
# directory_created(path)
# - register 'path' so that the uninstaller removes it
#
# get_special_folder_location(csidl_string)
# - get windows specific paths

import sys
import os
import platform

if platform.system() != 'Windows':
    # not for us
    sys.exit()

# releases supporting our special .bat files
win_bat_releases = ['NT', 'XP', '2000', '2003Server']

# path retrieving functions

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


def create_shortcuts ():
    """Create program shortcuts."""
    dest_dir = get_dest_dir()
    try:
        os.mkdir(dest_dir)
        directory_created(dest_dir)
    except OSError:
        pass
    path = os.path.join(dest_dir, "Check URL.lnk")
    script = os.path.join(sys.prefix, "Scripts", "linkchecker")
    if platform.release() in win_bat_releases:
        script += ".bat"

    arguments = "--interactive"
    create_shortcut(script, "Check URL", path, arguments)
    file_created(path)

    target = os.path.join(sys.prefix,
                          "share", "linkchecker", "doc", "documentation.html")
    path = os.path.join(dest_dir, "Documentation.lnk")
    create_shortcut(target, "Documentation", path)
    file_created(path)

    target = os.path.join(sys.prefix, "RemoveLinkChecker.exe")
    path = os.path.join(dest_dir, "Uninstall LinkChecker.lnk")
    arguments = "-u " + os.path.join(sys.prefix, "LinkChecker-wininst.log")
    create_shortcut(target, "Uninstall LinkChecker", path, arguments)
    file_created(path)
    print "See the shortcuts installed in the LinkChecker Programs Group"


def fix_configdata ():
    """
    Fix install and config paths in the config file.
    """
    name = "_linkchecker_configdata.py"
    conffile = os.path.join(sys.prefix, "Lib", "site-packages", name)
    lines = []
    for line in file(conffile):
        if line.startswith("install_") or line.startswith("config_"):
            lines.append(fix_install_path(line))
        else:
            lines.append(line)
    f = file(conffile, "w")
    f.write("".join(lines))
    f.close()

# windows install path scheme for python >= 2.3
# snatched from PC/bdist_wininst/install.c
# this is used to fix install_* paths when cross compiling for windows
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
    """
    Replace placeholders written by bdist_wininst with those specified
    in windows install path scheme.
    """
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
    return "%s = %r%s" % (key, val, os.linesep)

if __name__ == '__main__':
    if "-install" == sys.argv[1]:
        do_install()
    elif "-remove" == sys.argv[1]:
        # nothing to do since the crated shortcuts are automatically
        # removed
        pass

