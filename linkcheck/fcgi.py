# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------------------
#               Copyright (c) 1998 by Total Control Software
#                         All Rights Reserved
#------------------------------------------------------------------------
"""
Module Name:  fcgi.py

Handles communication with the FastCGI module of the
web server without using the FastCGI developers kit, but
will also work in a non-FastCGI environment, (straight CGI.)
This module was originally fetched from someplace on the
Net (I don't remember where and I can't find it now...) and
has been significantly modified to fix several bugs, be more
readable, more robust at handling large CGI data and return
document sizes, and also to fit the model that we had previously
used for FastCGI.

    WARNING:  If you don't know what you are doing, don't tinker with this
              module!

Creation Date:    1/30/98 2:59:04PM

License:      This is free software.  You may use this software for any
              purpose including modification/redistribution, so long as
              this header remains intact and that you do not claim any
              rights of ownership or authorship of this software.  This
              software has been tested, but no warranty is expressed or
              implied.
"""
import os
import sys
import socket
import errno
import cgi
import cStringIO as StringIO

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS = 1
FCGI_MAX_CONNS = 1

# Supported version of the FastCGI protocol
FCGI_VERSION_1 = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS = 0

# Record types
FCGI_BEGIN_REQUEST = 1
FCGI_ABORT_REQUEST = 2
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_DATA = 8
FCGI_GET_VALUES = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

# Types of management records
ManagementTypes = [FCGI_GET_VALUES]

FCGI_NULL_REQUEST_ID = 0

# Masks for flags component of FCGI_BEGIN_REQUEST
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BEGIN_REQUEST
FCGI_RESPONDER = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER = 3

# Values for protocolStatus component of FCGI_END_REQUEST
FCGI_REQUEST_COMPLETE = 0               # Request completed nicely
FCGI_CANT_MPX_CONN = 1               # This app can't multiplex
FCGI_OVERLOADED = 2               # New request rejected; too busy
FCGI_UNKNOWN_ROLE = 3               # Role value not known


error = 'fcgi.error'


# The following function is used during debugging; it isn't called
# anywhere at the moment

def _error (msg):
    """
    Append a string to /tmp/err.
    """
    errf = file('/tmp/err', 'a+')
    errf.write(msg+'\n')
    errf.close()


class Record (object):
    """
    Class representing FastCGI records.
    """

    def __init__ (self):
        """
        Initialize record data.
        """
        self.version = FCGI_VERSION_1
        self.rec_type = FCGI_UNKNOWN_TYPE
        self.req_id = FCGI_NULL_REQUEST_ID
        self.content = ""

    def read_record (self, sock):
        """
        Read a FastCGI record from socket.
        """
        s = [ord(x) for x in sock.recv(8)]
        self.version, self.rec_type, padding_length = s[0], s[1], s[6]
        self.req_id, content_length = (s[2]<<8)+s[3], (s[4]<<8)+s[5]
        self.content = ""
        while len(self.content) < content_length:
            data = sock.recv(content_length - len(self.content))
            self.content += data
        if padding_length != 0:
            _padding = sock.recv(padding_length)

        # Parse the content information
        c = self.content
        if self.rec_type == FCGI_BEGIN_REQUEST:
            self.role = (ord(c[0])<<8) + ord(c[1])
            self.flags = ord(c[2])

        elif self.rec_type == FCGI_UNKNOWN_TYPE:
            self.unknownType = ord(c[0])

        elif self.rec_type == FCGI_GET_VALUES or self.rec_type == FCGI_PARAMS:
            self.values = {}
            pos = 0
            while pos < len(c):
                name, value, pos = read_pair(c, pos)
                self.values[name] = value
        elif self.rec_type == FCGI_END_REQUEST:
            b = [ord(x) for x in c[0:4]]
            self.app_status = (b[0]<<24) + (b[1]<<16) + (b[2]<<8) + b[3]
            self.protocolStatus = ord(c[4])

    def write_record (self, sock):
        """
        Write a FastCGI request to socket.
        """
        content = self.content
        if self.rec_type == FCGI_BEGIN_REQUEST:
            content = chr(self.role>>8) + chr(self.role & 255) + \
                      chr(self.flags) + 5*'\000'

        elif self.rec_type == FCGI_UNKNOWN_TYPE:
            content = chr(self.unknownType) + 7*'\000'

        elif self.rec_type == FCGI_GET_VALUES or self.rec_type==FCGI_PARAMS:
            content = ""
            for i in self.values.keys():
                content += write_pair(i, self.values[i])

        elif self.rec_type == FCGI_END_REQUEST:
            v = self.app_status
            content = chr((v>>24)&255) + chr((v>>16)&255) + chr((v>>8)&255) +\
                      chr(v&255) + chr(self.protocolStatus) + 3*'\000'

        c_len = len(content)
        e_len = (c_len + 7) & (0xFFFF - 7)    # align to an 8-byte boundary
        pad_len = e_len - c_len

        hdr = [ self.version,
                self.rec_type,
                self.req_id >> 8,
                self.req_id & 255,
                c_len >> 8,
                c_len & 255,
                pad_len,
                0]
        hdr = ''.join([chr(x) for x in hdr])

        sock.send(hdr + content + pad_len*'\000')


def read_pair (s, pos):
    name_len = ord(s[pos])
    pos += 1
    if name_len & 128:
        b = [ord(x) for x in s[pos:pos+3]]
        pos += 3
        name_len = ((name_len&127)<<24) + (b[0]<<16) + (b[1]<<8) + b[2]
    value_len = ord(s[pos])
    pos += 1
    if value_len & 128:
        b = [ord(x) for x in s[pos:pos+3]]
        pos += 3
        value_len = ((value_len&127)<<24) + (b[0]<<16) + (b[1]<<8) + b[2]
    return ( s[pos:pos+name_len], s[pos+name_len:pos+name_len+value_len],
             pos+name_len+value_len )


def write_pair (name, value):
    l = len(name)
    if l < 128:
        s = chr(l)
    else:
        s = chr(128|(l>>24)&255) + chr((l>>16)&255) + chr((l>>8)&255) + \
            chr(l&255)
    l = len(value)
    if l < 128:
        s += chr(l)
    else:
        s += chr(128|(l>>24)&255) + chr((l>>16)&255) + chr((l>>8)&255) + \
             chr(l&255)
    return s + name + value


def HandleManTypes (r, conn):
    if r.rec_type == FCGI_GET_VALUES:
        r.rec_type = FCGI_GET_VALUES_RESULT
        v = {}
        vars = {'FCGI_MAX_CONNS' : FCGI_MAX_CONNS,
                'FCGI_MAX_REQS'  : FCGI_MAX_REQS,
                'FCGI_MPXS_CONNS': FCGI_MPXS_CONNS}
        for i in r.values.keys():
            if vars.has_key(i): v[i]=vars[i]
        r.values = vars
        r.write_record(conn)


class FastCGIWriter (object):
    """
    File-like object writing FastCGI requests. All read operations
    return empty data.
    """

    def __init__ (self, rec, conn):
        """
        Initialize with given record and connection.
        """
        self.record = rec
        self.conn = conn
        self.closed = False

    def close (self):
        """
        Close this writer.
        """
        if not self.closed:
            self.closed = True
            self.record.content = ""
            self.record.write_record(self.conn)

    def isatty (self):
        """
        Returns False.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return False

    def seek (self, pos, mode=0):
        """
        Does nothing.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"

    def tell (self):
        """
        Return zero.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return 0

    def read (self, n=-1):
        """
        Return empty string.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return ""

    def readline (self, length=None):
        """
        Return empty string.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return ""

    def readlines (self):
        """
        Return empty list.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return []

    def write (self, s):
        """
        Write data in record for record to connection.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        while s:
            chunk, s = self.get_next_chunk(s)
            self.record.content = chunk
            self.record.write_record(self.conn)

    def get_next_chunk (self, data):
        """
        Return tuple (chunk of data, newdata).
        """
        chunk = data[:8192]
        data = data[8192:]
        return chunk, data

    def writelines (self, lines):
        """
        Write given lines to the connection.
        """
        self.write(''.join(lines))

    def flush (self):
        """
        Does nothing.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"

_isFCGI = 1         # assume it is until we find out for sure

def isFCGI ():
    global _isFCGI
    return _isFCGI


_init = None
_sock = None

class FCGI (object):

    def __init__ (self):
        self.have_finished = 0
        if _init is None:
            _startup()
        if not isFCGI():
            self.have_finished = 1
            self.stdin, self.out, self.err, self.env = \
                                sys.stdin, sys.stdout, sys.stderr, os.environ
            return

        if os.environ.has_key('FCGI_WEB_SERVER_ADDRS'):
            addrs = os.environ['FCGI_WEB_SERVER_ADDRS'].split(',')
            good_addrs = [ addr.strip for addr in addrs ]
        else:
            good_addrs = None

        self.conn, addr = _sock.accept()
        # Check if the connection is from a legal address
        if good_addrs != None and addr not in good_addrs:
            raise error('Connection from invalid server!')

        stdin = data = ""
        self.env = {}
        self.request_id = 0
        remaining = 1
        while remaining:
            r = Record()
            r.read_record(self.conn)
            if r.rec_type in ManagementTypes:
                HandleManTypes(r, self.conn)
            elif r.req_id == 0:
                # Oh, poopy.  It's a management record of an unknown
                # type.  Signal the error.
                r2 = Record()
                r2.rec_type = FCGI_UNKNOWN_TYPE
                r2.unknownType = r.rec_type
                r2.write_record(self.conn)
                continue                # Charge onwards

            # Ignore requests that aren't active
            elif r.req_id != self.request_id and \
                 r.rec_type != FCGI_BEGIN_REQUEST:
                continue

            # If we're already doing a request, ignore further BEGIN_REQUESTs
            elif r.rec_type == FCGI_BEGIN_REQUEST and self.request_id != 0:
                continue

            # Begin a new request
            if r.rec_type == FCGI_BEGIN_REQUEST:
                self.request_id = r.req_id
                if r.role == FCGI_AUTHORIZER:
                    remaining = 1
                elif r.role == FCGI_RESPONDER:
                    remaining = 2
                elif r.role == FCGI_FILTER:
                    remaining = 3

            elif r.rec_type == FCGI_PARAMS:
                if r.content == "":
                    remaining -= 1
                else:
                    for i in r.values.keys():
                        self.env[i] = r.values[i]

            elif r.rec_type == FCGI_STDIN:
                if r.content == "":
                    remaining = remaining-1
                else:
                    stdin += r.content

            elif r.rec_type==FCGI_DATA:
                if r.content == "":
                    remaining -= 1
                else:
                    data += r.content
        # end of while remaining:

        self.stdin = sys.stdin  = StringIO.StringIO(stdin)
        self.data = StringIO.StringIO(data)
        r = Record()
        r.rec_type = FCGI_STDERR
        r.req_id = self.request_id
        self.err = sys.stderr = FastCGIWriter(r, self.conn)
        r = Record()
        r.rec_type = FCGI_STDOUT
        r.req_id = self.request_id
        self.out = sys.stdout = FastCGIWriter(r, self.conn)

    def __del__ (self):
        self.finish()

    def finish (self, status=0):
        if not self.have_finished:
            self.have_finished = 1
            self.err.close()
            self.out.close()
            r = Record()
            r.rec_type = FCGI_END_REQUEST
            r.req_id = self.request_id
            r.app_status = status
            r.protocolStatus = FCGI_REQUEST_COMPLETE
            r.write_record(self.conn)
            self.conn.close()

    def getFieldStorage (self):
        method = 'GET'
        if self.env.has_key('REQUEST_METHOD'):
            method = self.env['REQUEST_METHOD'].upper()
        if method == 'GET':
            return cgi.FieldStorage(environ=self.env, keep_blank_values=1)
        else:
            return cgi.FieldStorage(fp=self.stdin, environ=self.env,
                                    keep_blank_values=1)



Accept = FCGI       # alias for backward compatibility

def _startup ():
    global _init
    _init = 1
    try:
        s = socket.fromfd(sys.stdin.fileno(), socket.AF_INET,
                          socket.SOCK_STREAM)
        s.getpeername()
    except socket.error, (err, errmsg):
        if err != errno.ENOTCONN:   # must be a non-fastCGI environment
            global _isFCGI
            _isFCGI = 0
            return

    global _sock
    _sock = s
