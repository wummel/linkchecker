# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005  Bastian Kleineidam
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
Simple decorators (usable in Python >= 2.4).

Example:

@synchronized(thread.allocate_lock())
def f ():
    "Synchronized function"
    print "i am synchronized:", f, f.__doc__

@deprecated
def g ():
    "this function is deprecated"
    pass

@notimplemented
def h ():
    "todo"
    pass

"""
import warnings
import signal
import os


def deprecated (func):
    """
    A decorator which can be used to mark functions as deprecated.
    It emits a warning when the function is called.
    """
    def newfunc (*args, **kwargs):
        """
        Print deprecated warning and execute original function.
        """
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newfunc.__name__ = func.__name__
    if func.__doc__ is not None:
        newfunc.__doc__ += func.__doc__
    newfunc.__dict__.update(func.__dict__)
    return newfunc


def signal_handler (signal_number):
    """
    From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410666

    A decorator to set the specified function as handler for a signal.
    This function is the 'outer' decorator, called with only the
    (non-function) arguments.
    If signal_number is not a valid signal (for example signal.SIGN),
    no handler is set.
    """
    # create the 'real' decorator which takes only a function as an argument
    def newfunc (function):
        """
        Register function as signal handler.
        """
        # note: actually the kill(2) function uses the signal number of 0
        # for a special case, but for signal(2) only positive integers
        # are allowed
        is_valid_signal = 0 < signal_number < signal.NSIG
        if is_valid_signal and os.name == 'posix':
            signal.signal(signal_number, function)
        return function
    return newfunc


def _synchronized (lock, func):
    """
    Call function with aqcuired lock.
    """
    def newfunc (*args, **kwargs):
        """
        Execute function synchronized.
        """
        lock.acquire(True) # blocking
        try:
            return func(*args, **kwargs)
        finally:
            lock.release()
    newfunc.__name__ = func.__name__
    if func.__doc__ is not None:
        newfunc.__doc__ += func.__doc__
    newfunc.__dict__.update(func.__dict__)
    return newfunc


def synchronized (lock):
    """
    A decorator calling a function with aqcuired lock.
    """
    def newfunc (function):
        """
        Execute function synchronized.
        """
        return _synchronized(lock, function)
    return newfunc


def notimplemented (func):
    """
    Raises a NotImplementedError if the function is called.
    def newfunc (*args, **kwargs):
    """
    def newfunc (*args, **kwargs):
        """
        Raise NotImplementedError
        """
        raise NotImplementedError("%s not implemented" % func.__name__)
    newfunc.__name__ = func.__name__
    if func.__doc__ is not None:
        newfunc.__doc__ = func.__doc__
    newfunc.__dict__.update(func.__dict__)
    return newfunc
