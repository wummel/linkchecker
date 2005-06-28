"""
Simple decorators (usable in Python >= 2.4).
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
    newfunc.__doc__ = func.__doc__
    newfunc.__dict__.update(func.__dict__)
    return newfunc


def signal_handler (signal_number):
    """
    A decorator to set the specified function as handler for a signal.
    This function is the 'outer' decorator, called with only the
    (non-function) arguments.

    From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410666
    """
    # create the 'real' decorator which takes only a function as an argument
    def newfunc (function):
        """
        Register function as signal handler.
        """
        if os.name == 'posix':
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
    newfunc.__doc__ = func.__doc__
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


if __name__ == '__main__':
    import thread
    @synchronized(thread.allocate_lock())
    def f ():
        """Just me"""
        print "i am synchronized:", f, f.__doc__
    f()
    @deprecated
    def g ():
        pass
    g()
