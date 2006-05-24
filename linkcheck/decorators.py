# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2006 Bastian Kleineidam
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
import sys
import time


def update_func_meta (fake_func, real_func):
    """
    Set meta information (eg. __doc__) of fake function to that
    of the real function.
    @return fake_func
    """
    fake_func.__module__ = real_func.__module__
    fake_func.__name__ = real_func.__name__
    fake_func.__doc__ = real_func.__doc__
    fake_func.__dict__.update(real_func.__dict__)
    return fake_func


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
    return update_func_meta(newfunc, func)


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


def synchronize (lock, func):
    """
    Return synchronized function acquiring the given lock.
    """
    def newfunc (*args, **kwargs):
        """
        Execute function synchronized.
        """
        lock.acquire()
        try:
            return func(*args, **kwargs)
        finally:
            lock.release()
    return update_func_meta(newfunc, func)


def synchronized (lock):
    """
    A decorator calling a function with aqcuired lock.
    """
    return lambda func: synchronize(lock, func)


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
    return update_func_meta(newfunc, func)


def timeit (func, log=sys.stderr, limit=2.0):
    """
    Print execution time of the function. For quick'n'dirty profiling.
    """
    def newfunc (*args, **kwargs):
        """
        Execute function and print execution time.
        """
        t = time.time()
        res = func(*args, **kwargs)
        duration = time.time() - t
        if duration > limit:
            print >> log, func.__name__, "took %0.2f seconds" % duration
            print >> log, args
            print >> log, kwargs
        return res
    return update_func_meta(newfunc, func)


class memoized (object):
    """
    Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            self.cache[args] = value = self.func(*args)
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__


class curried (object):
    """
    Decorator that returns a function that keeps returning functions
    until all arguments are supplied; then the original function is
    evaluated.
    """
    def __init__(self, func, *a):
        self.func = func
        self.args = a

    def __call__(self, *a):
        args = self.args + a
        if len(args) < self.func.func_code.co_argcount:
            return curried(self.func, *args)
        else:
            return self.func(*args)
