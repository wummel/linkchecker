# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012-2014 Bastian Kleineidam
"""
Functions to load plugin modules.

Example usage:
    modules = loader.get_package_modules('plugins')
    plugins = loader.get_plugins(modules, PluginClass)
"""
from __future__ import print_function
import os
import sys
import zipfile
import importlib
import imp
from .fileutil import is_writable_by_others


def is_frozen ():
    """Return True if running inside a py2exe- or py2app-generated
    executable."""
    return hasattr(sys, "frozen")


def check_writable_by_others(filename):
    """Check if file is writable by others on POSIX systems.
    On non-POSIX systems the check is ignored."""
    if os.name != 'posix':
        # XXX on non-posix systems other bits are relevant
        return
    return is_writable_by_others(filename)


def get_package_modules(packagename):
    """Find all valid modules in the given package which must be a folder
    in the same directory as this loader.py module. A valid module has
    a .py extension, and is importable.
    @return: all loaded valid modules
    @rtype: iterator of module
    """
    if is_frozen():
        # find modules in library.zip filename
        zipname = os.path.dirname(os.path.dirname(__file__))
        parentmodule = os.path.basename(os.path.dirname(__file__))
        with zipfile.ZipFile(zipname, 'r') as f:
            prefix = "%s/%s/" % (parentmodule, packagename)
            modnames = [os.path.splitext(n[len(prefix):])[0]
              for n in f.namelist()
              if n.startswith(prefix) and "__init__" not in n]
    else:
        dirname = os.path.join(os.path.dirname(__file__), packagename)
        modnames = [x[:-3] for x in get_importable_files(dirname)]
    for modname in modnames:
        try:
            name ="..%s.%s" % (packagename, modname)
            yield importlib.import_module(name, __name__)
        except ImportError as msg:
            print("WARN: could not load module %s: %s" % (modname, msg))


def get_folder_modules(folder, parentpackage):
    """."""
    if check_writable_by_others(folder):
        print("ERROR: refuse to load modules from world writable folder %r" % folder)
        return
    for filename in get_importable_files(folder):
        fullname = os.path.join(folder, filename)
        modname = parentpackage+"."+filename[:-3]
        try:
            yield imp.load_source(modname, fullname)
        except ImportError as msg:
            print("WARN: could not load file %s: %s" % (fullname, msg))


def get_importable_files(folder):
    """Find all module files in the given folder that end with '.py' and
    don't start with an underscore.
    @return module names
    @rtype: iterator of string
    """
    for fname in os.listdir(folder):
        if fname.endswith('.py') and not fname.startswith('_'):
            fullname = os.path.join(folder, fname)
            if check_writable_by_others(fullname):
                print("ERROR: refuse to load module from world writable file %r" % fullname)
            else:
                yield fname


def get_plugins(modules, classes):
    """Find all given (sub-)classes in all modules.
    @param modules: the modules to search
    @ptype modules: iterator of modules
    @return: found classes
    @rytpe: iterator of class objects
    """
    for module in modules:
        for plugin in get_module_plugins(module, classes):
            yield plugin


def get_module_plugins(module, classes):
    """Return all subclasses of a class in the module.
    If the module defines __all__, only those entries will be searched,
    otherwise all objects not starting with '_' will be searched.
    """
    try:
        names = module.__all__
    except AttributeError:
        names = [x for x in vars(module) if not x.startswith('_')]
    for name in names:
        try:
            obj = getattr(module, name)
        except AttributeError:
            continue
        try:
            for classobj in classes:
                if issubclass(obj, classobj):
                    yield obj
        except TypeError:
            continue
