# -*- Mode: Python; tab-width: 4 -*-
# 	$Id$
#	Author: Sam Rushing <rushing@nightmare.com>

# A simple unix version of the asynchronous socket support.
# There are lots of problems with this still - I only wrote it to show
# that it could be done, and for my own testing purposes.
# [960206: servtest, asynfing, asynhttp, and pop3demo work, asyndns doesn't.]
# [960321: servtest, asynfing, asynhttp, pop3demo, pop3_2 work]
import select
import socket
import sys

# you need to generate ERRNO.py from Tools/scripts/h2py.py in the Python
# distribution.

try:
    import ERRNO
except ImportError:
    raise ImportError,'you need to generate ERRNO.py from Tools/scripts/h2py.py in the Python distribution'

# look what I can get away with... 8^)
socket.socket_map = {}

ALL_EVENTS = []

DEFAULT_TIMEOUT = 30.0

loop_running = 0

stop_loop_exception = "stop running the select loop"

# we want to select for read only those sockets
# to which we are already connected to, -OR- those
# sockets we are accepting on.
def readables (sock_fds):
	sm = socket.socket_map
	def readable_test (fd, sm=sm):
		sock = sm[fd]
		return sock.connected or sock.accepting
	return filter (readable_test, sock_fds)

# only those fd's we are 'write blocked' on, -OR-
# those sockets we are waiting for a connection on.
def writables (sock_fds):
	sm = socket.socket_map
	def writable_test (fd, sm=sm):
		sock = sm[fd]
		return sock.write_blocked or not sock.connected
	return filter (writable_test, sock_fds)

def loop(timeout=DEFAULT_TIMEOUT):
	loop_running = 1
	try:
		while 1:
			sock_fds = socket.socket_map.keys()

			read_fds = readables (sock_fds)
			write_fds = writables (sock_fds)
			expt_fds = sock_fds[:]

			(read_fds,
			 write_fds,
			 expt_fds) = select.select (read_fds,
										write_fds,
										expt_fds,
										timeout)
			print read_fds,write_fds,expt_fds
			try:
				for x in expt_fds:
					socket.socket_map[x].handle_expt_event()
				for x in read_fds:
					socket.socket_map[x].handle_read_event()
				for x in write_fds:
					socket.socket_map[x].handle_write_event()
			except KeyError:
				# handle_expt handle_read might remove as socket
				# from the map by calling self.close().
				pass
	except stop_loop_exception:
		print 'loop stopped'

class dispatcher:
	def __init__ (self, sock=None):
		self.debug = 0
		self.log_queue = []
		self.connected = 0
		self.accepting = 0
		self.write_blocked = 1
		if sock:
			self.socket = sock
			self.fileno = self.socket.fileno()
			# I think it should inherit this anyway
			self.socket.setblocking (0)
			self.connected = 1
			self.add_channel()

	def add_channel (self, events=ALL_EVENTS):
		self.log ('adding channel %s' % self)
		socket.socket_map [self.fileno] = self

	def del_channel (self):
		if socket.socket_map.has_key (self.fileno):
			del socket.socket_map [self.fileno]
		if not len(socket.socket_map.keys()):
			raise stop_loop_exception

	def create_socket (self, family, type):
		self.socket = socket.socket (family, type)
		self.socket.setblocking(0)
		self.fileno = self.socket.fileno()
		self.add_channel()

	def bind (self, *args):
		return apply (self.socket.bind, args)

	def go (self):
		if not loop_running:
			loop()

	def listen (self, num):
		self.accepting = 1
		self.socket.listen (num)

	def accept (self):
		return self.socket.accept()

	def connect (self, host, port):
		try:
			self.socket.connect (host, port)
		except socket.error, why:
			if type(why) == type(()) \
			   and why[0] in (ERRNO.EINPROGRESS, ERRNO.EALREADY, ERRNO.EWOULDBLOCK):
				return
			else:
				raise socket.error, why
		self.connected = 1
		self.handle_connect()

	def send (self, data):
		try:
			result = self.socket.send (data)
			if result != len(data):
				self.write_blocked = 1
			else:
				self.write_blocked = 0
			return result
		except socket.error, why:
			if type(why) == type(()) and why[0] == ERRNO.EWOULDBLOCK:
				self.write_blocked = 1
				return 0
			else:
				raise socket.error, why
			return 0

	def recv (self, buffer_size):
		data = self.socket.recv (buffer_size)
		if not data:
			self.handle_close()
			return ''
		else:
			return data

	def close (self):
		self.socket.close()
		self.del_channel()

	def shutdown (self, how):
		self.socket.shutdown (how)

	def log (self, message):
		#self.log_queue.append ('%s:%d %s' %
		#					   (self.__class__.__name__, self.fileno, message))
		print 'log:', message

	def done (self):
		self.print_log()

	def print_log (self):
		for x in self.log_queue:
			print x

	def handle_read_event (self):
		# getting a read implies that we are connected
		if not self.connected:
			self.handle_connect()
			self.connected = 1
			self.handle_read()
		elif self.accepting:
			if not self.connected:
				self.connected = 1
			self.handle_accept()
		else:
			self.handle_read()

	def more_to_send (self, yesno=1):
		self.write_blocked = yesno

	def handle_write_event (self):
		# getting a read implies that we are connected
		if not self.connected:
			self.handle_connect()
			self.connected = 1
		self.write_blocked = 0
		self.handle_write()

	def handle_expt_event (self):
		self.handle_error()

	def handle_error (self, error=0):
		self.close()

	def handle_read (self):
		self.log ('unhandled FD_READ')

	def handle_write (self):
		self.log ('unhandled FD_WRITE')

	def handle_connect (self):
		self.log ('unhandled FD_CONNECT')

	def handle_oob (self):
		self.log ('unhandled FD_OOB')

	def handle_accept (self):
		self.log ('unhandled FD_ACCEPT')

	def handle_close (self):
		self.log ('unhandled FD_CLOSE')
			
	def handle_disconnect (self, error):
		self.log ('unexpected disconnect, error:%d' % error)

# ---------------------------------------------------------------------------
# adds async send capability, useful for simple clients.
# ---------------------------------------------------------------------------

class dispatcher_with_send (dispatcher):
	def __init__ (self, sock=None):
		dispatcher.__init__ (self, sock)
		self.out_buffer = ''

	def initiate_send (self):
		while self.out_buffer:
			num_sent = 0
			num_sent = dispatcher.send (self, self.out_buffer[:512])
			self.out_buffer = self.out_buffer[num_sent:]

	def handle_write (self):
		self.initiate_send()

	def send (self, data):
		if self.debug:
			self.log ('sending %s' % repr(data))
		self.out_buffer = data
		self.initiate_send()

# ---------------------------------------------------------------------------
# used a lot when debugging
# ---------------------------------------------------------------------------

def close_all ():
	for x in socket.socket_map.items():
		x[1].socket.close()
	socket.socket_map = {}

