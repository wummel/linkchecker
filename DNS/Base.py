# $Id$
import sys
import getopt
import socket
import string
import DNS,DNS.Lib,DNS.Type,DNS.Class,DNS.Opcode
#import asyncore

defaults= { 'protocol':'udp', 'port':53, 'opcode':DNS.Opcode.QUERY, 
            'qtype':DNS.Type.A, 'rd':1, 'timing':1 }

defaults['server']=[]

def ParseResolvConf():
    "parses the /etc/resolv.conf file and sets defaults for name servers"
    import string
    global defaults
    lines=open("/etc/resolv.conf").readlines()
    for line in lines:
	line = string.strip(line)
	if (not line) or line[0]==';' or line[0]=='#':
	    continue
	fields=string.split(line)
	if fields[0]=='domain':
	    defaults['domain']=fields[1]
	if fields[0]=='search':
	    pass
	if fields[0]=='options':
	    pass
	if fields[0]=='sortlist':
	    pass
	if fields[0]=='nameserver':
	    defaults['server'].append(fields[1])



class DnsRequest:
    def __init__(self,*name,**args):
	self.donefunc=None
	self.async=None
	self.defaults = {}
	self.argparse(name,args)
	self.defaults = self.args

    def argparse(self,name,args):
	if not name and self.defaults.has_key('name'):
	    args['name'] = self.defaults['name']
	if type(name) is type(""):
	    args['name']=name
	else:
	    if len(name) == 1:
		if name[0]:
		    args['name']=name[0]
	for i in defaults.keys():
	    if not args.has_key(i):
		if self.defaults.has_key(i):
		    args[i]=self.defaults[i]
		else:
		    args[i]=defaults[i]
	if type(args['server']) == type(''):
	    args['server'] = [args['server']]
	self.args=args

    def socketInit(self,a,b):
	import socket
	self.s = socket.socket(a,b)

    def processUDPReply(self):
	import time
	self.reply = self.s.recv(1024)
	self.time_finish=time.time()
	self.args['server']=self.ns
	return self.processReply()

    def processTCPReply(self):
	import time
	self.f = self.s.makefile('r')
	header = self.f.read(2)
	if len(header) < 2:
		raise DNS.Error,'EOF'
	count = DNS.Lib.unpack16bit(header)
	self.reply = self.f.read(count)
	if len(self.reply) != count:
	    raise DNS.Error,'incomplete reply'
	self.time_finish=time.time()
	self.args['server']=self.ns
	return self.processReply()

    def processReply(self):
	import time
	self.args['elapsed']=(self.time_finish-self.time_start)*1000
	u = DNS.Lib.Munpacker(self.reply)
	r=DNS.Lib.DnsResult(u,self.args)
	r.args=self.args
	#self.args=None  # mark this DnsRequest object as used.
	return r
	#### TODO TODO TODO ####
	if protocol == 'tcp' and qtype == DNS.Type.AXFR:
	    while 1:
		header = f.read(2)
		if len(header) < 2:
		    print '========== EOF =========='
		    break
		count = DNS.Lib.unpack16bit(header)
		if not count:
		    print '========== ZERO COUNT =========='
		    break
		print '========== NEXT =========='
		reply = f.read(count)
		if len(reply) != count:
		    print '*** Incomplete reply ***'
		    break
		u = DNS.Lib.Munpacker(reply)
		DNS.Lib.dumpM(u)

    def conn(self):
	self.s.connect((self.ns,self.port))

    def req(self,*name,**args):
	import time,sys
	self.argparse(name,args)
	#if not self.args:
	#    raise DNS.Error,'reinitialize request before reuse'
	protocol = self.args['protocol']
	self.port = self.args['port']
	opcode = self.args['opcode']
	rd = self.args['rd']
	server=self.args['server']
	if type(self.args['qtype']) == type('foo'):
	    try:
		qtype = eval(string.upper(self.args['qtype']), DNS.Type.__dict__)
	    except (NameError,SyntaxError):
		raise DNS.Error,'unknown query type'
	else:
	    qtype=self.args['qtype']
	if not self.args.has_key('name'):
	    print self.args
	    raise DNS.Error,'nothing to lookup'
	qname = self.args['name']
	if qtype == DNS.Type.AXFR:
	    print 'Query type AXFR, protocol forced to TCP'
	    protocol = 'tcp'
	#print 'QTYPE %d(%s)' % (qtype, DNS.Type.typestr(qtype))
	m = DNS.Lib.Mpacker()
	m.addHeader(0,
	      0, opcode, 0, 0, rd, 0, 0, 0,
	      1, 0, 0, 0)
	m.addQuestion(qname, qtype, DNS.Class.IN)
	self.request = m.getbuf()
	if protocol == 'udp':
	    self.response=None
	    self.socketInit(socket.AF_INET, socket.SOCK_DGRAM)
	    for self.ns in server:
		try:
		    #self.s.connect((self.ns, self.port))
		    self.conn()
		    self.time_start=time.time()
		    if not self.async:
			self.s.send(self.request)
			self.response=self.processUDPReply()
		#except socket.error:
		except None:
		    continue
		break
	    if not self.response:
		if not self.async:
		    raise DNS.Error,'no working nameservers found'
	else:
	    self.response=None
	    for self.ns in server:
		try:
		    self.socketInit(socket.AF_INET, socket.SOCK_STREAM)
		    self.time_start=time.time()
		    self.conn()
		    self.s.send(DNS.Lib.pack16bit(len(self.request)) + self.request)
		    self.s.shutdown(1)
		    self.response=self.processTCPReply()
		except socket.error:
		    continue
		break
	    if not self.response:
		raise DNS.Error,'no working nameservers found'
	if not self.async:
	    return self.response

#class DnsAsyncRequest(DnsRequest,asyncore.dispatcher_with_send):
class DnsAsyncRequest(DnsRequest):
    def __init__(self,*name,**args):
	if args.has_key('done') and args['done']:
	    self.donefunc=args['done']
	else:
	    self.donefunc=self.showResult
	self.realinit(name,args)
	self.async=1
    def conn(self):
	import time
	self.connect(self.ns,self.port)
	self.time_start=time.time()
	if self.args.has_key('start') and self.args['start']:
	    asyncore.dispatcher.go(self)
    def socketInit(self,a,b):
	self.create_socket(a,b)
	asyncore.dispatcher.__init__(self)
	self.s=self
    def handle_read(self):
	if self.args['protocol'] == 'udp':
	    self.response=self.processUDPReply()
	    if self.donefunc: 
		apply(self.donefunc,(self,))
    def handle_connect(self):
	self.send(self.request)
    def handle_write(self):
	pass
    def showResult(self,*s):
	self.response.show()
