"""
Simple decorators (usable in Python >= 2.4).
"""
import warnings

def deprecated (func):
    """
    A decorator which can be used to mark functions as deprecated.
    It emits a warning when the function is called.
    """
    def newFunc (*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


def _synchronized (lock, func):
    """
    Call function with aqcuired lock.
    """
    def newFunc (*args, **kwargs):
        lock.acquire(True) # blocking
        try:
            return func(*args, **kwargs)
        finally:
            lock.release()
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


def synchronized (lock):
    """
    A decorator calling a function with aqcuired lock.
    """
    def newFunc (func):
        return _synchronized(lock, func)
    return newFunc


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
