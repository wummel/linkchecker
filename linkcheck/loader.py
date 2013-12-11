# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012-2013 Bastian Kleineidam
"""
Functions to load plugin modules.

Example usage:
    modules = loader.get_modules('plugins')
    plugins = loader.get_plugins(modules, PluginClass)
"""
from __future__ import print_function
import os
import sys
import zipfile
import importlib


def is_frozen ():
    """Return True if running inside a py2exe-generated executable."""
    return hasattr(sys, "frozen")


def get_modules(folder):
    """Find all valid modules in the given folder which must be in
    in the same directory as this loader.py module. A valid module
    has a .py extension, and is importable.
    @return: all loaded valid modules
    @rtype: iterator of module
    """
    if is_frozen():
        # find modules in library.zip filename
        zipname = os.path.dirname(os.path.dirname(__file__))
        with zipfile.ZipFile(zipname, 'r') as f:
            parentmodule = __loader__.fullname.split('.', 1)[0]
            parentpath = parentmodule.replace(".", "/")
            prefix = "%s/%s/" % (parentpath, folder)
            modnames = [os.path.splitext(n[len(prefix):])[0]
              for n in f.namelist()
              if n.startswith(prefix) and "__init__" not in n]
    else:
        dirname = os.path.join(os.path.dirname(__file__), folder)
        modnames = get_importable_modules(dirname)
    for modname in modnames:
        try:
            name ="..%s.%s" % (folder, modname)
            yield importlib.import_module(name, __name__)
        except ImportError as msg:
            print("ERROR: could not load module %s: %s" % (modname, msg))


def get_importable_modules(folder):
    """Find all module files in the given folder that end with '.py' and
    don't start with an underscore.
    @return module names
    @rtype: iterator of string
    """
    for fname in os.listdir(folder):
        if fname.endswith('.py') and not fname.startswith('_'):
            yield fname[:-3]


def get_plugins(modules, classobj):
    """Find all class objects in all modules.
    @param modules: the modules to search
    @ptype modules: iterator of modules
    @return: found classes
    @rytpe: iterator of class objects
    """
    for module in modules:
        for plugin in get_module_plugins(module, classobj):
            yield plugin


def get_module_plugins(module, classobj):
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
            if issubclass(obj, classobj):
                yield obj
        except TypeError:
            continue
