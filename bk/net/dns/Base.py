# -*- coding: iso-8859-1 -*-
"""
This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License.

Base functionality. Request and Response classes, that sort of thing.
"""

import select
import socket
import string
import types
import time
import asyncore
import os

class DNSError (Exception):
    pass

import Lib
import Type
import Class
import Opcode


defaults = {
    'protocol':'udp',
    'port':53,
    'opcode':Opcode.QUERY,
    'qtype':Type.A,
    'rd':1,
    'timing':1,
    'timeout': 30,
}

class DnsRequest (object):
    """ high level Request object """

    def __init__ (self, name, config, **args):
        self.donefunc = None
        self.async = None
        self.defaults = {}
        self.argparse(name, config, args)
        self.defaults = self.args

    def argparse (self, name, config, args):
        self.name = name
        self.config = config
        for i in defaults.keys():
            if not args.has_key(i):
                if self.defaults.has_key(i):
                    args[i]=self.defaults[i]
                else:
                    args[i]=defaults[i]
        self.args=args

    def socketInit (self, a, b):
        self.s = socket.socket(a,b)

    def processUDPReply (self):
        if self.args['timeout'] > 0:
            r,w,e = select.select([self.s],[],[],self.args['timeout'])
            if not len(r):
                raise DNSError, 'Timeout'
        self.reply = self.s.recv(1024)
        self.time_finish=time.time()
        self.args['server']=self.ns
        return self.processReply()

    def processTCPReply (self):
        self.f = self.s.makefile('r')
        header = self.f.read(2)
        if len(header) < 2:
            raise DNSError,'EOF'
        count = Lib.unpack16bit(header)
        self.reply = self.f.read(count)
        if len(self.reply) != count:
            raise DNSError,'incomplete reply'
        self.time_finish=time.time()
        self.args['server']=self.ns
        return self.processReply()

    def processReply (self):
        self.args['elapsed']=(self.time_finish-self.time_start)*1000
        u = Lib.Munpacker(self.reply)
        r = Lib.DnsResult(u,self.args)
        r.args = self.args
        #self.args=None  # mark this DnsRequest object as used.
        return r
        #### TODO TODO TODO ####
#        if protocol == 'tcp' and qtype == Type.AXFR:
#            while 1:
#                header = f.read(2)
#                if len(header) < 2:
#                    print '========== EOF =========='
#                    break
#                count = Lib.unpack16bit(header)
#                if not count:
#                    print '========== ZERO COUNT =========='
#                    break
#                print '========== NEXT =========='
#                reply = f.read(count)
#                if len(reply) != count:
#                    print '*** Incomplete reply ***'
#                    break
#                u = Lib.Munpacker(reply)
#                Lib.dumpM(u)

    def conn (self):
        self.s.connect((self.ns, self.port))

    def req (self, name, config, **args):
        " needs a refactoring "
        self.argparse(name, config, args)
        #if not self.args:
        #    raise DNSError,'reinitialize request before reuse'
        protocol = self.args['protocol']
        self.port = self.args['port']
        opcode = self.args['opcode']
        rd = self.args['rd']
        server=self.args['server']
        if type(self.args['qtype']) == types.StringType:
            try:
                qtype = getattr(Type, string.upper(self.args['qtype']))
            except AttributeError:
                raise DNSError,'unknown query type'
        else:
            qtype=self.args['qtype']
        qname = self.name
        if qtype == Type.AXFR:
            print 'Query type AXFR, protocol forced to TCP'
            protocol = 'tcp'
        #print 'QTYPE %d(%s)' % (qtype, Type.typestr(qtype))
        m = Lib.Mpacker()
        # jesus. keywords and default args would be good. TODO.
        m.addHeader(0,
              0, opcode, 0, 0, rd, 0, 0, 0,
              1, 0, 0, 0)
        m.addQuestion(qname, qtype, Class.IN)
        self.request = m.getbuf()
        if protocol == 'udp':
            self.sendUDPRequest(server)
        else:
            self.sendTCPRequest(server)
        if self.async:
            return None
        else:
            return self.response

    def sendUDPRequest (self, server):
        "refactor me"
        self.response = None
        self.socketInit(socket.AF_INET, socket.SOCK_DGRAM)
        for self.ns in server:
            try:
                # TODO. Handle timeouts &c correctly (RFC)
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
                raise DNSError,'no working nameservers found'

    def sendTCPRequest (self, server):
        " do the work of sending a TCP request "
        self.response=None
        for self.ns in server:
            try:
                self.socketInit(socket.AF_INET, socket.SOCK_STREAM)
                self.time_start=time.time()
                self.conn()
                self.s.send(Lib.pack16bit(len(self.request))+self.request)
                self.s.shutdown(1)
                self.response=self.processTCPReply()
            except socket.error:
                continue
            break
        if not self.response:
            raise DNSError,'no working nameservers found'


class DnsAsyncRequest (DnsRequest, asyncore.dispatcher_with_send):
    " an asynchronous request object. out of date, probably broken "

    def __init__ (self,*name,**args):
        DnsRequest.__init__(self, *name, **args)
        asyncore.dispatcher_with_send.__init__(self, *name, **args)
        # XXX todo
        if args.has_key('done') and args['done']:
            self.donefunc = args['done']
        else:
            self.donefunc=self.showResult
        #self.realinit(name,args) # XXX todo
        self.async=1

    def conn (self):
        self.connect((self.ns,self.port))
        self.time_start=time.time()
        if self.args.has_key('start') and self.args['start']:
            asyncore.dispatcher.go(self)

    def socketInit (self,a,b):
        self.create_socket(a,b)
        asyncore.dispatcher.__init__(self)
        self.s=self

    def handle_read (self):
        if self.args['protocol'] == 'udp':
            self.response=self.processUDPReply()
            if self.donefunc:
                self.donefunc(*self)

    def handle_connect (self):
        self.send(self.request)

    def handle_write (self):
        pass

    def showResult (self,*s):
        self.response.show()

