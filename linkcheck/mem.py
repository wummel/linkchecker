# -*- coding: iso-8859-1 -*-
# Copyright: Jean Brouwers
# License:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
Copied from the Python Cookbook recipe at
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286222

To find the memory usage in a particular section of code these
functions are typically used as follows::
    m0 = memory()
    ...
    m1 = memory(m0)
"""

import os

_proc_status = '/proc/%d/status' % os.getpid()

_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}

def _VmB (VmKey):
    """Parse /proc/<pid>/status file for given key.

    @return: requested number value of status entry
    @rtype: float
    """
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
    """Get memory usage.

    @return: memory usage in bytes
    @rtype: float
    """
    return _VmB('VmSize:') - since


def resident (since=0.0):
    """Get resident memory usage.

    @return: resident memory usage in bytes
    @rtype: float
    """
    return _VmB('VmRSS:') - since


def stacksize (since=0.0):
    """Get stack size.

    @return: stack size in bytes
    @rtype: float
    """
    return _VmB('VmStk:') - since
