# @(#)httpslib.py	1.1 VMS-99/01/30	https support

import ssl,httplib,string,socket,mimetools

HTTP_PREF = 'HTTP/'
HTTPS_PORT = 443

class HTTPS(httplib.HTTP):

	def connect (self, host, port = 0):
		"""Connect to a host on a given port.

		Note:  This method is automatically invoked by __init__,
		if a host is specified during instantiation.

		"""
		if not port:
		    i = string.find(host, ':')
		    if i >= 0:
			host, port = host[:i], host[i+1:]
			try: port = string.atoi(port)
			except string.atoi_error:
			    raise socket.error, "nonnumeric port"
		if not port: port = HTTPS_PORT
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if self.debuglevel > 0: print 'connect:', (host, port)
		self.sock.connect(host, port)
		self.ssl = ssl.ssl(self.sock.fileno())

	def send (self, str):
		if self.debuglevel > 0: print 'send:', `str`
		self.ssl.write(str,len(str))

	def makefile (self, mode='r', bufsize=-1):
		return _fileobject(self.sock,self.ssl,mode,bufsize)

	def getreply (self):
		self.file = self.makefile('rb')
#		self.sock = None
		line = self.file.readline()
		if self.debuglevel > 0: print 'reply:',`line`
		try:
			[ver,code,msg] = string.split(line,None,2)
		except ValueError:
			try:
				[ver,code] = string.split(line,None,1)
				msg = ""
			except ValueError:
				ver = ""
		if ver[:len(HTTP_PREF)] != HTTP_PREF:
			self.headers = None
			return -1, line, self.headers
		self.headers = mimetools.Message(self.file,0)
		return string.atoi(code), string.strip(msg), self.headers

	def close (self):
		if self.file:
			self.file.close()
		self.file = self.sock = self.ssl = None

class _fileobject:

	def __init__ (self, sock, ssl, mode, bufsize):
		import string
		self._sock = sock
		self._ssl = ssl
		self._mode = mode
		if bufsize < 0:
			bufsize = 512
		self._rbufsize = max(1,bufsize)
		self._wbufsize = bufsize
		self._wbuf = self._rbuf = ""

	def close (self):
		try:
			if self._sock:
				self.flush()
		finally:
			self._sock = None

	def __del__ (self):
		self.close()

	def flush (self):
		if self._wbuf:
			self._sock.write(self._wbuf,len(self._wbuf))
		self._wbuf = ""

	def fileno (self):
		return self._sock.fileno()

	def write (self, data):
		self._wbuf += data
		if self._wbufsize == 1:
			if '\n' in data:
				self.flush()
		else:
			if len(self._wbuf) >= self._wbufsize:
				self.flush()

	def writelines (self, lst):
		filter(self._sock.send,lst)
		self.flush()

	def read (self, n=-1):
		if n >= 0:
			while len(self._rbuf) < n:
				new = self._ssl.read(self._rbufsize)
				if not new: break
				self._rbuf += new
			data,self._rbuf = self._rbuf[:n],self._rbuf[n:]
			return data
		while 1:
			new = self._ssl.read(self._rbufsize)
			if not new: break
			self._rbuf += new
		data,self._rbuf = self._rbuf,""
		return data

	def readline (self):
		data = ""
		i = string.find(self._rbuf,'\n')
		while i < 0:
			new = self._ssl.read(self._rbufsize)
			if not new: break
			i = string.find(new,'\n')
			if i >= 0:
			    i += len(self._rbuf)
			self._rbuf += new
		if i < 0:
		    i = len(self._rbuf)
		else:
		    i += 1
		data,self._rbuf = self._rbuf[:i],self._rbuf[i:]
		return data

	def readlines (self):
		l = []
		while 1:
			line = self.readline()
			if not line: break
			l.append(line)
		return l

def _test():
	import sys
	import getopt
	opts, args = getopt.getopt(sys.argv[1:], 'd')
	dl = 0
	for o, a in opts:
	    if o == '-d':
	        dl += 1
	if args[0:]:
	    host = args[0]
	if args[1:]:
	    selector = args[1]
	h = HTTPS()
	host = 'synergy.as.cmu.edu'
	selector = '/~geek/'
	h.set_debuglevel(dl)
	h.connect(host)
	h.putrequest('GET', selector)
	h.endheaders()
	errcode, errmsg, headers = h.getreply()
	print 'errcode =', errcode
	print 'errmsg  =', errmsg
	print "\tHEADERS:"
	if headers:
	    for header in headers.headers:
	        print string.strip(header)
	print "\tTEXT:"
	print h.getfile().read()

if __name__ == '__main__':
    _test()
