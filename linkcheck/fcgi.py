#------------------------------------------------------------------------
#               Copyright (c) 1998 by Total Control Software
#                         All Rights Reserved
#------------------------------------------------------------------------
#
# Module Name:  fcgi.py
#
# Description:  Handles communication with the FastCGI module of the
#               web server without using the FastCGI developers kit, but
#               will also work in a non-FastCGI environment, (straight CGI.)
#               This module was originally fetched from someplace on the
#               Net (I don't remember where and I can't find it now...) and
#               has been significantly modified to fix several bugs, be more
#               readable, more robust at handling large CGI data and return
#               document sizes, and also to fit the model that we had previously
#               used for FastCGI.
#
#     WARNING:  If you don't know what you are doing, don't tinker with this
#               module!
#
# Creation Date:    1/30/98 2:59:04PM
#
# License:      This is free software.  You may use this software for any
#               purpose including modification/redistribution, so long as
#               this header remains intact and that you do not claim any
#               rights of ownership or authorship of this software.  This
#               software has been tested, but no warranty is expressed or
#               implied.
#
#------------------------------------------------------------------------


import  os, sys, string, socket, errno
from    cStringIO   import StringIO
import  cgi

#---------------------------------------------------------------------------

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS=1
FCGI_MAX_CONNS = 1

# Supported version of the FastCGI protocol
FCGI_VERSION_1 = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS=0

# Record types
FCGI_BEGIN_REQUEST = 1 ; FCGI_ABORT_REQUEST = 2 ; FCGI_END_REQUEST   = 3
FCGI_PARAMS        = 4 ; FCGI_STDIN         = 5 ; FCGI_STDOUT        = 6
FCGI_STDERR        = 7 ; FCGI_DATA          = 8 ; FCGI_GET_VALUES    = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

# Types of management records
ManagementTypes = [FCGI_GET_VALUES]

FCGI_NULL_REQUEST_ID=0

# Masks for flags component of FCGI_BEGIN_REQUEST
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BEGIN_REQUEST
FCGI_RESPONDER = 1 ; FCGI_AUTHORIZER = 2 ; FCGI_FILTER = 3

# Values for protocolStatus component of FCGI_END_REQUEST
FCGI_REQUEST_COMPLETE = 0               # Request completed nicely
FCGI_CANT_MPX_CONN    = 1               # This app can't multiplex
FCGI_OVERLOADED       = 2               # New request rejected; too busy
FCGI_UNKNOWN_ROLE     = 3               # Role value not known


error = 'fcgi.error'


#---------------------------------------------------------------------------

# The following function is used during debugging; it isn't called
# anywhere at the moment

def _error(msg):
    "Append a string to /tmp/err"
    errf=open('/tmp/err', 'a+')
    errf.write(msg+'\n')
    errf.close()

#---------------------------------------------------------------------------

class record:
    "Class representing FastCGI records"
    def __init__(self):
        self.version = FCGI_VERSION_1
        self.recType = FCGI_UNKNOWN_TYPE
        self.reqId   = FCGI_NULL_REQUEST_ID
        self.content = ""

    #----------------------------------------
    def readRecord(self, sock):
        s = map(ord, sock.recv(8))
        self.version, self.recType, paddingLength = s[0], s[1], s[6]
        self.reqId, contentLength = (s[2]<<8)+s[3], (s[4]<<8)+s[5]
        self.content = ""
        while len(self.content) < contentLength:
            data = sock.recv(contentLength - len(self.content))
            self.content += data
        if paddingLength != 0:
            _padding = sock.recv(paddingLength)

        # Parse the content information
        c = self.content
        if self.recType == FCGI_BEGIN_REQUEST:
            self.role = (ord(c[0])<<8) + ord(c[1])
            self.flags = ord(c[2])

        elif self.recType == FCGI_UNKNOWN_TYPE:
            self.unknownType = ord(c[0])

        elif self.recType == FCGI_GET_VALUES or self.recType == FCGI_PARAMS:
            self.values={}
            pos=0
            while pos < len(c):
                name, value, pos = readPair(c, pos)
                self.values[name] = value
        elif self.recType == FCGI_END_REQUEST:
            b = map(ord, c[0:4])
            self.appStatus = (b[0]<<24) + (b[1]<<16) + (b[2]<<8) + b[3]
            self.protocolStatus = ord(c[4])

    #----------------------------------------
    def writeRecord(self, sock):
        content = self.content
        if self.recType == FCGI_BEGIN_REQUEST:
            content = chr(self.role>>8) + chr(self.role & 255) + chr(self.flags) + 5*'\000'

        elif self.recType == FCGI_UNKNOWN_TYPE:
            content = chr(self.unknownType) + 7*'\000'

        elif self.recType==FCGI_GET_VALUES or self.recType==FCGI_PARAMS:
            content = ""
            for i in self.values.keys():
                content += writePair(i, self.values[i])

        elif self.recType==FCGI_END_REQUEST:
            v = self.appStatus
            content = chr((v>>24)&255) + chr((v>>16)&255) + chr((v>>8)&255) +\
	              chr(v&255) + chr(self.protocolStatus) + 3*'\000'

        cLen = len(content)
        eLen = (cLen + 7) & (0xFFFF - 7)    # align to an 8-byte boundary
        padLen = eLen - cLen

        hdr = [ self.version,
                self.recType,
                self.reqId >> 8,
                self.reqId & 255,
                cLen >> 8,
                cLen & 255,
                padLen,
                0]
        hdr = ''.join(map(chr, hdr))

        sock.send(hdr + content + padLen*'\000')

#---------------------------------------------------------------------------

def readPair(s, pos):
    nameLen=ord(s[pos])
    pos += 1
    if nameLen & 128:
        b=map(ord, s[pos:pos+3])
	pos += 3
        nameLen=((nameLen&127)<<24) + (b[0]<<16) + (b[1]<<8) + b[2]
    valueLen=ord(s[pos])
    pos += 1
    if valueLen & 128:
        b=map(ord, s[pos:pos+3])
	pos += 3
        valueLen=((valueLen&127)<<24) + (b[0]<<16) + (b[1]<<8) + b[2]
    return ( s[pos:pos+nameLen], s[pos+nameLen:pos+nameLen+valueLen],
             pos+nameLen+valueLen )

#---------------------------------------------------------------------------

def writePair(name, value):
    l=len(name)
    if l<128:
        s = chr(l)
    else:
        s = chr(128|(l>>24)&255) + chr((l>>16)&255) + chr((l>>8)&255) + chr(l&255)
    l=len(value)
    if l<128:
        s += chr(l)
    else:
        s += chr(128|(l>>24)&255) + chr((l>>16)&255) + chr((l>>8)&255) + chr(l&255)
    return s + name + value

#---------------------------------------------------------------------------

def HandleManTypes(r, conn):
    if r.recType == FCGI_GET_VALUES:
        r.recType = FCGI_GET_VALUES_RESULT
        v={}
        vars={'FCGI_MAX_CONNS' : FCGI_MAX_CONNS,
              'FCGI_MAX_REQS'  : FCGI_MAX_REQS,
              'FCGI_MPXS_CONNS': FCGI_MPXS_CONNS}
        for i in r.values.keys():
            if vars.has_key(i): v[i]=vars[i]
        r.values=vars
        r.writeRecord(conn)

#---------------------------------------------------------------------------

class FastCGIWriter:
    def __init__(self, rec, conn):
        self.record = rec
        self.conn = conn
        self.closed = 0

    def close(self):
	if not self.closed:
	    self.closed = 1
            self.record.content=""
            self.record.writeRecord(self.conn)

    def isatty(self):
	if self.closed:
            raise ValueError, "I/O operation on closed file"
	return 0

    def seek(self, pos, mode=0):
	if self.closed:
	    raise ValueError, "I/O operation on closed file"

    def tell(self):
	if self.closed:
            raise ValueError, "I/O operation on closed file"
	return 0

    def read(self, n=-1):
	if self.closed:
	    raise ValueError, "I/O operation on closed file"
	return ""

    def readline(self, length=None):
	if self.closed:
		raise ValueError, "I/O operation on closed file"
	return ""

    def readlines(self):
	if self.closed:
		raise ValueError, "I/O operation on closed file"
	return []

    def write(self, s):
	if self.closed:
	    raise ValueError, "I/O operation on closed file"
        while s:
            chunk, s = self.getNextChunk(s)
            self.record.content = chunk
            self.record.writeRecord(self.conn)

    def getNextChunk(self, data):
        chunk = data[:8192]
        data = data[8192:]
        return chunk, data

    def writelines(self, lines):
	self.write(''.join(lines))

    def flush(self):
	if self.closed:
	    raise ValueError, "I/O operation on closed file"

#---------------------------------------------------------------------------


_isFCGI = 1         # assume it is until we find out for sure

def isFCGI():
    global _isFCGI
    return _isFCGI



#---------------------------------------------------------------------------


_init = None
_sock = None

class FCGI:
    def __init__(self):
        self.haveFinished = 0
        if _init is None:
            _startup()
        if not isFCGI():
            self.haveFinished = 1
            self.stdin, self.out, self.err, self.env = \
                                sys.stdin, sys.stdout, sys.stderr, os.environ
            return

        if os.environ.has_key('FCGI_WEB_SERVER_ADDRS'):
            good_addrs=map(string.strip,
	              os.environ['FCGI_WEB_SERVER_ADDRS'].split(','))
        else:
            good_addrs=None

        self.conn, addr=_sock.accept()
        # Check if the connection is from a legal address
        if good_addrs!=None and addr not in good_addrs:
            raise error('Connection from invalid server!')

        stdin = data = ""
        self.env = {}
        self.requestId=0
        remaining=1
        while remaining:
            r=record(); r.readRecord(self.conn)

            if r.recType in ManagementTypes:
                HandleManTypes(r, self.conn)

            elif r.reqId==0:
                # Oh, poopy.  It's a management record of an unknown
                # type.  Signal the error.
                r2=record()
                r2.recType=FCGI_UNKNOWN_TYPE ; r2.unknownType=r.recType
                r2.writeRecord(self.conn)
                continue                # Charge onwards

            # Ignore requests that aren't active
            elif r.reqId != self.requestId and r.recType != FCGI_BEGIN_REQUEST:
                continue

            # If we're already doing a request, ignore further BEGIN_REQUESTs
            elif r.recType == FCGI_BEGIN_REQUEST and self.requestId != 0:
                continue

            # Begin a new request
            if r.recType == FCGI_BEGIN_REQUEST:
                self.requestId = r.reqId
                if r.role == FCGI_AUTHORIZER:   remaining=1
                elif r.role == FCGI_RESPONDER:  remaining=2
                elif r.role == FCGI_FILTER:     remaining=3

            elif r.recType == FCGI_PARAMS:
                if r.content == "":
                    remaining -= 1
                else:
                    for i in r.values.keys():
                        self.env[i] = r.values[i]

            elif r.recType == FCGI_STDIN:
                if r.content == "":
                    remaining = remaining-1
                else:
                    stdin += r.content

            elif r.recType==FCGI_DATA:
                if r.content == "":
                    remaining -= 1
                else:
                    data += r.content
        # end of while remaining:

        self.stdin = sys.stdin  = StringIO(stdin)
        self.data = StringIO(data)
        r=record()
        r.recType = FCGI_STDERR
        r.reqId = self.requestId
        self.err = sys.stderr = FastCGIWriter(r, self.conn)
        r = record()
        r.recType = FCGI_STDOUT
        r.reqId = self.requestId
        self.out = sys.stdout = FastCGIWriter(r, self.conn)

    def __del__(self):
        self.Finish()

    def Finish(self, status=0):
        if not self.haveFinished:
            self.haveFinished = 1
            self.err.close()
            self.out.close()
            r=record()
            r.recType=FCGI_END_REQUEST
            r.reqId=self.requestId
            r.appStatus=status
            r.protocolStatus=FCGI_REQUEST_COMPLETE
            r.writeRecord(self.conn)
            self.conn.close()

    def getFieldStorage(self):
        method = 'GET'
        if self.env.has_key('REQUEST_METHOD'):
            method = self.env['REQUEST_METHOD'].upper()
        if method == 'GET':
            return cgi.FieldStorage(environ=self.env, keep_blank_values=1)
        else:
            return cgi.FieldStorage(fp=self.stdin, environ=self.env, keep_blank_values=1)



Accept = FCGI       # alias for backward compatibility
#---------------------------------------------------------------------------

def _startup():
    global _init
    _init = 1
    try:
        s=socket.fromfd(sys.stdin.fileno(), socket.AF_INET,
                        socket.SOCK_STREAM)
        s.getpeername()
    except socket.error, (err, errmsg):
        if err!=errno.ENOTCONN:       # must be a non-fastCGI environment
            global _isFCGI
            _isFCGI = 0
            return

    global _sock
    _sock = s


#---------------------------------------------------------------------------

def _test():
    counter=0
    try:
        while isFCGI():
            req = FCGI()
            counter += 1

            try:
                fs = req.getFieldStorage()
                size = int(fs['size'].value)
                doc = ['*' * size]
            except:
                doc = ['<HTML><HEAD><TITLE>FCGI TestApp</TITLE></HEAD>\n<BODY>\n']
                doc.append('<H2>FCGI TestApp</H2><P>')
                doc.append('<b>request count</b> = %d<br>' % counter)
                doc.append('<b>pid</b> = %s<br>' % os.getpid())
                if req.env.has_key('CONTENT_LENGTH'):
                    cl = int(req.env['CONTENT_LENGTH'])
                    doc.append('<br><b>POST data (%s):</b><br><pre>' % cl)
                    keys = fs.keys()
                    keys.sort()
                    for k in keys:
                        val = fs[k]
                        if type(val) == type([]):
                            doc.append('    <b>%-15s :</b>  %s\n' % (k, val))
                        else:
                            doc.append('    <b>%-15s :</b>  %s\n' % (k, val.value))
                    doc.append('</pre>')


                doc.append('<P><HR><P><pre>')
                keys = req.env.keys()
                keys.sort()
                for k in keys:
                    doc.append('<b>%-20s :</b>  %s\n' % (k, req.env[k]))
                doc.append('\n</pre><P><HR>\n')
                doc.append('</BODY></HTML>\n')


            doc = ''.join(doc)
            req.out.write('Content-length: %s\r\n'
                        'Content-type: text/html\r\n'
                        'Cache-Control: no-cache\r\n'
                        '\r\n'
                            % len(doc))
            req.out.write(doc)

            req.Finish()
    except:
        import traceback
        f = open('traceback', 'w')
        traceback.print_exc( file = f )
#        f.write('%s' % doc)

if __name__=='__main__':
    #import pdb
    #pdb.run('_test()')
    _test()
