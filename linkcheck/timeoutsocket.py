"""enables a timeout on all TCP connections

This module enables a timeout mechanism on all TCP connections.  It
does this by inserting a shim on top of the socket module.  After
this module has been imported, all socket creation goes through this
shim.  As a result, every TCP connection will support a timeout.

The beauty of this method is that it immediately and transparently
enables the entire python library to support timeouts on TCP sockets.
As an example, if you wanted to SMTP connections to have a 20 second
timeout:

    import timeoutsocket
    import smtplib
    timeoutsocket.setDefaultSocketTimeout(20)


The timeout applies to the socket functions that normally block on
execution:  read, write, connect, and accept.  If any of these 
operations exceeds the specified timeout, the exception Timeout
will be raised.

The default timeout value is set to None.  As a result, importing
this module does not change the default behavior of a socket.  The
timeout mechanism only activates when the timeout has been set to
a numeric value.  (This behavior mimics the behavior of the
select.select() function.)

This module works by replacing the socket module in the sys.modules
array.  As a result, any reference to the original socket module
will instead reference this module.  Whenever any creates a TCP
socket using the socket.socket() function, this module returns an
instance of the TimeoutSocket object.  It is this object that handles
the timeouts.  

This module implements two classes: TimeoutSocket and TimeoutFile.

The TimeoutSocket class defines a socket-like object that attempts to
avoid the condition where a socket may block indefinitely.  The
TimeoutSocket class raises a Timeout exception whenever the
current operation delays too long. 

The TimeoutFile class defines a file-like object that uses the TimeoutSocket
class.  When the makefile() method of TimeoutSocket is called, it returns
an instance of a TimeoutFile.

Each of these objects adds two methods to manage the timeout value:

    get_timeout()   -->  returns the timeout of the socket or file
    set_timeout()   -->  sets the timeout of the socket or file


As an example, one might use the timeout feature to create httplib
connections that will timeout after 30 seconds:

    import timeoutsocket
    import httplib
    H = httplib.HTTP("www.python.org")
    H.sock.set_timeout(30)

Note:  When used in this manner, the connect() routine may still
block because it happens before the timeout is set.  To avoid
this, use the 'timeout.setDefaultSocketTimeout()' function.

Good Luck!

"""

#
# Revision history
#    1.4  Updated document string
#    1.3  Changed name to timeoutsocket.py on Pehr's suggestion
#    1.2  Added the silent replacement of the socket module
#    1.1. First version of safesocket.py
#

__version__ = "$Revision$"
__author__  = "Timothy O'Malley <timo@alum.mit.edu>"

#
# Imports
#
import select, errno
import string
try:
    from _timeoutsocket import *
except ImportError:
    from socket import *
    _socket = socket
    del socket

#
# Default timeout value for ALL TimeoutSockets
#
_DefaultTimeout = None
def setDefaultSocketTimeout(timeout):
    global _DefaultTimeout
    _DefaultTimeout = timeout
def getDefaultSocketTimeout():
    return _DefaultTimeout

#
# Exceptions for socket errors and timeouts
#
Error = error
class Timeout(Exception):
    pass


#
# Factory function
#
def socket(family=AF_INET, type=SOCK_STREAM, proto=None):
    if family != AF_INET or type != SOCK_STREAM:
        if proto:
            return _socket(family, type, proto)
        else:
            return _socket(family, type)
    return TimeoutSocket( _socket(family, type), _DefaultTimeout )
# end socket

#
# The TimeoutSocket class definition
#
class TimeoutSocket:
    """TimeoutSocket object
    Implements a socket-like object that raises Timeout whenever
    an operation takes too long.
    The definition of 'too long' can be changed using the
    set_timeout() method.
    """

    def __init__(self, sock, timeout):
        self._sock    = sock
        self._timeout = timeout
    # end __init__

    def __getattr__(self, key):
        return getattr(self._sock, key)
    # end __getattr__

    def get_timeout(self):
        return self._timeout
    # end set_timeout

    def set_timeout(self, timeout=None):
        self._timeout = timeout
    # end set_timeout

    def connect(self, addr, dumbhack=None):
        # In case we were called as connect(host, port)
        #if port != None:  addr = (addr, port)

        # Shortcuts
        sock    = self._sock
        timeout = self._timeout

        # First, make a non-blocking call to connect
        try:
            sock.setblocking(0)
            sock.connect(addr)
            sock.setblocking(1)
            return
        except Error, why:
            # If we are already connected, then return success
            # If we got a genuine error, re-raise it.
            errcode = why[0]
            if errcode == errno.EISCONN:
                return
            if errcode == 10035 and why[1] == 'winsock error':
                # Windows error code from G.Li@med.ge.com
                return
            vals = (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK)
            if errcode not in vals:
                raise

        # Now, wait for the connect to happen
        # ONLY if dumbhack indicates this is pass number one.
        #   If select raises an error, we pass it on.
        #   Is this the right behavior?
        if not dumbhack:
            r,w,e = select.select([], [sock], [], timeout)
            if w:
                return self.connect(addr, dumbhack=1)

        # If we get here, then we should raise Timeout
        raise Timeout("Attempted connect to %s timed out." % str(addr) )
    # end connect

    def accept(self, dumbhack=1):
        # Shortcuts
        sock    = self._sock
        timeout = self._timeout

        # First, make a non-blocking call to connect
        try:
            sock.setblocking(0)
            sa = sock.accept()
            sock.setblocking(1)
            return sa
        except Error, why:
            # If we are already connected, then return success
            # If we got a genuine error, re-raise it.
            errcode = why[0]
            vals = (errno.EAGAIN, errno.EWOULDBLOCK)
            if errcode not in vals:
                raise

        # Now, wait for the accept to happen
        # ONLY if dumbhack indicates this is pass number one.
        #   If select raises an error, we pass it on.
        #   Is this the right behavior?
        if not dumbhack:
            r,w,e = select.select([sock], [], [], timeout)
            if r:
                return self.accept(dumbhack=1)

        # If we get here, then we should raise Timeout
        raise Timeout("Attempted accept timed out.")
    # end accept

    def send(self, data, flags=0):
        sock = self._sock
        totallen = 0
        while data:
            r,w,e = select.select([],[sock], [], self._timeout)
            if not w:
                raise Timeout("Send timed out")
            sentlen = sock.send(data, flags)
            data = data[sentlen:]
            totallen += sentlen
        return totallen
    # end send

    def recv(self, bufsize, flags=0):
        sock = self._sock
        r,w,e = select.select([sock], [], [], self._timeout)
        if r:
            data = sock.recv(bufsize, flags)
            return data
        raise Timeout("Recv timed out")
    # end recv

    def makefile(self, flags="r", bufsize=-1):
        return TimeoutFile(self, flags, bufsize)
    # end makefile

# end TimeoutSocket


class TimeoutFile:
    """TimeoutFile object
    Implements a file-like object on top of TimeoutSocket.
    """

    def __init__(self, sock, mode="r", bufsize=4096):
        self._sock          = sock
        self._bufsize       = 4096
        if bufsize > 0: self._bufsize = bufsize
        if not hasattr(sock, "_inqueue"): self._sock._inqueue = ""

    # end __init__

    def __getattr__(self, key):
        return getattr(self._sock, key)
    # end __getattr__

    def write(self, data):
        self.send(data)
    # end write

    def read(self, size=-1):
        data = self._sock._inqueue
        self._sock._inqueue = ""
        while 1:
            datalen = len(data)
            if datalen >= size > 0:
                break 
            bufsize = self._bufsize
            if size > 0:
                bufsize = min(bufsize, size - datalen)
            buf = self.recv(bufsize)
            if not buf:
                break
            data += buf
        if datalen > size > 0:
            self._sock._inqueue = data[size:]
            data = data[:size]
        return data
    # end read

    def readline(self, size=-1):
        data = self._sock._inqueue
        self._sock._inqueue = ""
        while 1:
            idx = string.find(data, "\n")
            if idx >= 0:
                break
            datalen = len(data)
            if datalen >= size > 0:
                break
            bufsize = self._bufsize
            if size > 0:
                bufsize = min(bufsize, size - datalen )
            buf = self.recv(bufsize)
            if not buf:
                break
            data += buf

        if idx >= 0:
            idx += 1
            self._sock._inqueue = data[idx:]
            data = data[:idx]
        elif size > 0 and datalen > size:
            self._sock._inqueue = data[size:]
            data = data[:size]
        return data
    # end readline

    def readlines(self, sizehint=-1):
        result = []
        while 1:
            line = self.readline()
            if not line: break
            result.append(line)
        return line
    # end readlines

    def flush(self):  pass

# end TimeoutFile


#
# Silently replace the standard socket module
#
import sys
if sys.modules["socket"].__name__ != __name__:
    me = sys.modules[__name__]
    sys.modules["_timeoutsocket"] = sys.modules["socket"]
    sys.modules["socket"]  = me
    for mod in sys.modules.values():
        if hasattr(mod, "socket") and type(mod.socket) == type(me):
            mod.socket = me

# Finis
