# -*- coding: iso-8859-1 -*-
""" Copied from the Python Cookbook recipe at
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286222

    To find the memory usage in a particular section of code these
    functions are typically used as follows:

    m0 = memory()
    ...
    m1 = memory(m0)
"""

import os

_proc_status = '/proc/%d/status' % os.getpid()

_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}

def _VmB (VmKey):
    '''Parse /proc/<pid>/status file for given key.'''
    if os.name != 'posix':
        # not supported
        return 0.0
    global _proc_status, _scale
    # get pseudo file /proc/<pid>/status
    try:
        t = open(_proc_status)
        v = t.read()
        t.close()
    except IOError:
        # unsupported platform (non-Linux?)
        return 0.0
    # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
    # convert Vm value to bytes
    return float(v[1]) * _scale[v[2]]


def memory (since=0.0):
    '''Return memory usage in bytes.'''
    return _VmB('VmSize:') - since


def resident (since=0.0):
    '''Return resident memory usage in bytes.'''
    return _VmB('VmRSS:') - since


def stacksize (since=0.0):
    '''Return stack size in bytes.'''
    return _VmB('VmStk:') - since
