# -*- coding: iso-8859-1 -*-
# snatched from pythoncard CVS

# THIS FILE IS ONLY FOR USE WITH MS WINDOWS
# It is run as parts of the bdist_wininst installer
# Be sure to build the installer with
# 'python setup.py --install-script=install-linkchecker.py'
# or insert this into setup.cfg:
# [bdist_wininst]
# install-script=install-linkchecker.py

import sys
import os
from distutils.sysconfig import get_python_lib

if not sys.platform.startswith('win'):
    sys.exit()

try:
    prg = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
except OSError:
    try:
        prg = get_special_folder_path("CSIDL_PROGRAMS")
    except OSError, reason:
        # give up - cannot install shortcuts
        print "cannot install shortcuts: %s" % reason
        sys.exit()

lib_dir = get_python_lib(plat_specific=1)
dest_dir = os.path.join(prg, "LinkChecker")
python_exe = os.path.join(sys.prefix, "python.exe")

import linkcheck

def do_install ():
    """create_shortcut(target, description, filename[, arguments[, \
                     workdir[, iconpath[, iconindex]]]])

       file_created(path)
         - register 'path' so that the uninstaller removes it

       directory_created(path)
         - register 'path' so that the uninstaller removes it

       get_special_folder_location(csidl_string)
    """
    try:
        os.mkdir(dest_dir)
        directory_created(dest_dir)
    except OSError:
        pass
    path = os.path.join(dest_dir, "Check URL.lnk")
    script_dir = linkcheck.configdata.install_scripts
    arguments = os.path.join(script_dir, "linkchecker")
    arguments += " --interactive"
    create_shortcut(python_exe, "Check URL", path, arguments)
    file_created(path)

    #target = os.path.join(lib_dir,
    #                      "PythonCard\\docs\\html\\index.html")
    #path = os.path.join(dest_dir, "Documentation.lnk")
    #create_shortcut(target, "Documentation", path)
    #file_created(path)

    target = os.path.join(sys.prefix, "RemoveLinkChecker.exe")
    path = os.path.join(dest_dir, "Uninstall LinkChecker.lnk")
    arguments = "-u " + os.path.join(sys.prefix, "LinkChecker-wininst.log")
    create_shortcut(target, "Uninstall LinkChecker", path, arguments)
    file_created(path)
    print "See the shortcuts installed in the LinkChecker Programs Group"


if __name__ == '__main__':
    if "-install" == sys.argv[1]:
        do_install()
    elif "-remove" == sys.argv[1]:
        pass
