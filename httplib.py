#
# HTTP/1.1 client library
#
# Copyright (C) 1998-1999 Guido van Rossum. All Rights Reserved.
# Written by Greg Stein. Given to Guido. Licensed using the Python license.
#
# This module is maintained by Greg and is available at:
#    http://www.lyra.org/greg/python/httplib.py
#
# Since this isn't in the Python distribution yet, we'll use the CVS ID
# for tracking:
#   $Id$
#

import socket,string,mimetools,httplib


error = __name__ + '.error'

HTTP_PORT = 80

class HTTPResponse(mimetools.Message):
    def __init__(self, fp, version, errcode):
        mimetools.Message.__init__(self, fp, 0)

        if version == 'HTTP/1.0':
            self.version = 10
        elif version[:7] == 'HTTP/1.':
             self.version = 11	# use HTTP/1.1 code for HTTP/1.x where x>=1
        else:
            raise error, 'unknown HTTP protocol'

        # are we using the chunked-style of transfer encoding?
        tr_enc = self.getheader('transfer-encoding')
        if tr_enc:
            if string.lower(tr_enc) != 'chunked':
                raise error, 'unknown transfer-encoding'
            self.chunked = 1
            self.chunk_left = None
        else:
            self.chunked = 0

        # will the connection close at the end of the response?
        conn = self.getheader('connection')
        if conn:
            conn = string.lower(conn)
            # a "Connection: close" will always close the connection. if we
            # don't see that and this is not HTTP/1.1, then the connection will
            # close unless we see a Keep-Alive header.
            self.will_close = string.find(conn, 'close') != -1 or \
                        ( self.version != 11 and \
                          not self.getheader('keep-alive') )
        else:
            # for HTTP/1.1, the connection will always remain open
            # otherwise, it will remain open IFF we see a Keep-Alive header
            self.will_close = self.version != 11 and \
			  not self.getheader('keep-alive')

        # do we have a Content-Length?
        # NOTE: RFC 2616, S4.4, #3 states we ignore this if tr_enc is "chunked"
        length = self.getheader('content-length')
        if length and not self.chunked:
            self.length = int(length)
        else:
            self.length = None

        # does the body have a fixed length? (of zero)
        if (errcode == 204 or		# No Content
            errcode == 304 or		# Not Modified
            100 <= errcode < 200):		# 1xx codes
            self.length = 0

        # if the connection remains open, and we aren't using chunked, and
        # a content-length was not provided, then assume that the connection
        # WILL close.
        if not self.will_close and \
           not self.chunked and \
           self.length is None:
            self.will_close = 1


    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None


    def isclosed(self):
        # NOTE: it is possible that we will not ever call self.close(). This
        #       case occurs when will_close is TRUE, length is None, and we
        #       read up to the last byte, but NOT past it.
        #
        # IMPLIES: if will_close is FALSE, then self.close() will ALWAYS be
        #          called, meaning self.isclosed() is meaningful.
        return self.fp is None


    def read(self, amt=None):
        if not self.fp:
            return ''

        if self.chunked:
            chunk_left = self.chunk_left
            value = ''
            while 1:
                if not chunk_left:
                    line = self.fp.readline()
                    i = string.find(line, ';')
                    if i >= 0:
                        line = line[:i]	# strip chunk-extensions
                    chunk_left = string.atoi(line, 16)
                    if chunk_left == 0:
                        break
                if not amt:
                    value = value + self.fp.read(chunk_left)
                elif amt < chunk_left:
                    value = value + self.fp.read(amt)
                    self.chunk_left = chunk_left - amt
                    return value
                elif amt == chunk_left:
                    value = value + self.fp.read(amt)
                    self.fp.read(2)	# toss the CRLF at the end of the chunk
                    self.chunk_left = None
                    return value
                else:
                    value = value + self.fp.read(chunk_left)
                    amt = amt - chunk_left

                # we read the whole chunk, get another
                self.fp.read(2)		# toss the CRLF at the end of the chunk
                chunk_left = None

            # read and discard trailer up to the CRLF terminator
            ### note: we shouldn't have any trailers!
            while 1:
                line = self.fp.readline()
                if line == '\r\n':
                    break

            # we read everything; close the "file"
            self.close()

            return value

        elif not amt:
            # unbounded read
            if self.will_close:
                s = self.fp.read()
            else:
                s = self.fp.read(self.length)
            self.close()	# we read everything
            return s

        if self.length is not None:
            if amt > self.length:
                # clip the read to the "end of response"
                amt = self.length
            self.length = self.length - amt

        s = self.fp.read(amt)

        # close our "file" if we know we should
        ### I'm not sure about the len(s) < amt part; we should be safe because
        ### we shouldn't be using non-blocking sockets
        if self.length == 0 or len(s) < amt:
            self.close()

        return s


class HTTPConnection:

  _http_vsn = 11
  _http_vsn_str = 'HTTP/1.1'

  response_class = HTTPResponse

  def __init__(self, host, port=None):
    self.sock = None
    self.response = None
    self._set_hostport(host, port)

  def _set_hostport(self, host, port):
    if port is None:
      i = string.find(host, ':')
      if i >= 0:
        port = int(host[i+1:])
        host = host[:i]
      else:
        port = HTTP_PORT
    self.host = host
    self.port = port

  def connect(self):
    """Connect to the host and port specified in __init__."""
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect(self.host, self.port)

  def close(self):
    """Close the connection to the HTTP server."""
    if self.sock:
      self.sock.close()	# close it manually... there may be other refs
      self.sock = None
    if self.response:
      self.response.close()
      self.response = None

  def send(self, str):
    """Send `str' to the server."""
    if not self.sock:
      self.connect()

    # send the data to the server. if we get a broken pipe, then close
    # the socket. we want to reconnect when somebody tries to send again.
    #
    # NOTE: we DO propagate the error, though, because we cannot simply
    #       ignore the error... the caller will know if they can retry.
    try:
      self.sock.send(str)
    except socket.error, v:
      if v[0] == 32:	# Broken pipe
        self.close()
      raise

  def putrequest(self, method, url='/'):
    """Send a request to the server.

    `method' specifies an HTTP request method, e.g. 'GET'.
    `url' specifies the object being requested, e.g.
    '/index.html'.
    """
    if self.response:
      if not self.response.isclosed():
        ### implies half-duplex!
        raise error, 'prior response has not been fully handled'
      self.response = None

    if not url:
      url = '/'
    str = '%s %s %s\r\n' % (method, url, self._http_vsn_str)

    try:
      self.send(str)
    except socket.error, v:
      if v[0] != 32:	# Broken pipe
        raise
      # try one more time (the socket was closed; this will reopen)
      self.send(str)

    self.putheader('Host', self.host)

    if self._http_vsn == 11:
      # Issue some standard headers for better HTTP/1.1 compliance

      # note: we are assuming that clients will not attempt to set these
      #       headers since *this* library must deal with the consequences.
      #       this also means that when the supporting libraries are
      #       updated to recognize other forms, then this code should be
      #       changed (removed or updated).

      # we only want a Content-Encoding of "identity" since we don't
      # support encodings such as x-gzip or x-deflate.
      self.putheader('Accept-Encoding', 'identity')

      # we can accept "chunked" Transfer-Encodings, but no others
      # NOTE: no TE header implies *only* "chunked"
      #self.putheader('TE', 'chunked')

      # if TE is supplied in the header, then it must appear in a
      # Connection header.
      #self.putheader('Connection', 'TE')

    else:
      # For HTTP/1.0, the server will assume "not chunked"
      pass

  def putheader(self, header, value):
    """Send a request header line to the server.

    For example: h.putheader('Accept', 'text/html')
    """
    str = '%s: %s\r\n' % (header, value)
    self.send(str)

  def endheaders(self):
    """Indicate that the last header line has been sent to the server."""

    self.send('\r\n')

  def request(self, method, url='/', body=None, headers={}):
    """Send a complete request to the server."""

    self.putrequest(method, url)

    if body:
      self.putheader('Content-Length', str(len(body)))
    for hdr, value in headers.items():
      self.putheader(hdr, value)
    self.endheaders()

    if body:
      self.send(body)

  def getreply(self):
    """Get a reply from the server.

    Returns a tuple consisting of:
    - server response code (e.g. '200' if all goes well)
    - server response string corresponding to response code
    - any RFC822 headers in the response from the server

    """
    file = self.sock.makefile('rb')
    line = file.readline()
    try:
      [ver, code, msg] = string.split(line, None, 2)
    except ValueError:
      try:
        [ver, code] = string.split(line, None, 1)
        msg = ""
      except ValueError:
        self.close()
        return -1, line, file
    if ver[:5] != 'HTTP/':
      self.close()
      return -1, line, file
    errcode = int(code)
    errmsg = string.strip(msg)
    response = self.response_class(file, ver, errcode)
    if response.will_close:
      # this effectively passes the connection to the response
      self.close()
    else:
      # remember this, so we can tell when it is complete
      self.response = response
    return errcode, errmsg, response


class HTTP(HTTPConnection):
  "Compatibility class with httplib.py from 1.5."

  _http_vsn = 10
  _http_vsn_str = 'HTTP/1.0'

  def __init__(self, host='', port=None):
    "Provide a default host, since the superclass requires one."

    # Note that we may pass an empty string as the host; this will throw
    # an error when we attempt to connect. Presumably, the client code
    # will call connect before then, with a proper host.
    HTTPConnection.__init__(self, host, port)
    self.debuglevel=0

  def connect(self, host=None, port=None):
    "Accept arguments to set the host/port, since the superclass doesn't."

    if host:
      self._set_hostport(host, port)
    HTTPConnection.connect(self)

  def set_debuglevel(self, debuglevel):
    self.debuglevel=debuglevel

  def getfile(self):
    "Provide a getfile, since the superclass' use of HTTP/1.1 prevents it."
    return self.file

  def putheader(self, header, *values):
    "The superclass allows only one value argument."
    HTTPConnection.putheader(self, header, string.joinfields(values,'\r\n\t'))

  def getreply(self):
    "Compensate for an instance attribute shuffling."
    errcode, errmsg, response = HTTPConnection.getreply(self)
    if errcode == -1:
      self.file = response	# response is the "file" when errcode==-1
      self.headers = None
      return -1, errmsg, None

    self.headers = response
    self.file = response.fp
    return errcode, errmsg, response
