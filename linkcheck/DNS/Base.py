# -*- coding: iso-8859-1 -*-
"""
$Id$

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License.

    Base functionality. Request and Response classes, that sort of thing.
"""

import select, socket, re, string, types, time, asyncore, os

class DNSError (Exception): pass

import Lib, Type, Class, Opcode

defaults = {
    'protocol':'udp',
    'port':53,
    'opcode':Opcode.QUERY,
    'qtype':Type.A,
    'rd':1,
    'timing':1,
    'timeout': 30,
    'server': [],
}

def DiscoverNameServers ():
    import os
    if os.name=='posix':
        init_dns_resolver_posix()
    elif os.name=='nt':
        init_dns_resolver_nt()
    else:
        # other platforms not supported (what about Mac?)
        pass
    if not defaults['server']:
        # last fallback: localhost
        defaults['server'].append('127.0.0.1')


def init_dns_resolver_posix ():
    "Set up the DnsLookupConnection class with /etc/resolv.conf information"
    if not os.path.exists('/etc/resolv.conf'):
        return
    for line in file('/etc/resolv.conf', 'r').readlines():
        line = line.strip()
        if (not line) or line[0]==';' or line[0]=='#':
            continue
        m = re.match(r'^search\s+(\.?.+)$', line)
        if m:
            for domain in m.group(1).split():
                # domain search path not used
                pass
        m = re.match(r'^nameserver\s+(\S+)\s*$', line)
        if m:
            defaults['server'].append(m.group(1))


def init_dns_resolver_nt ():
    import winreg
    key = None
    try:
        key = winreg.key_handle(winreg.HKEY_LOCAL_MACHINE,
               r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
    except EnvironmentError:
        try: # for Windows ME
            key = winreg.key_handle(winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Services\VxD\MSTCP")
        except EnvironmentError:
            pass
    if key:
        for server in winreg.stringdisplay(key.get("NameServer", "")):
            if server:
                defaults['server'].append(str(server))
        for item in winreg.stringdisplay(key.get("SearchList", "")):
            if item:
                pass # domain search not used
        if not defaults['server']:
            # XXX the proper way to test this is to search for
            # the "EnableDhcp" key in the interface adapters...
            for server in winreg.stringdisplay(key.get("DhcpNameServer", "")):
                if server:
                    defaults['server'].append(str(server))
            for item in winreg.stringdisplay(key.get("DhcpDomain", "")):
                if item:
                    pass # domain search not used

    try: # search adapters
        key = winreg.key_handle(winreg.HKEY_LOCAL_MACHINE,
  r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\DNSRegisteredAdapters")
        for subkey in key.subkeys():
            count, counttype = subkey['DNSServerAddressCount']
            values, valuestype = subkey['DNSServerAddresses']
            for server in winreg.binipdisplay(values):
                if server:
                    defaults['server'].append(str(server))
    except (EnvironmentError, IndexError):
        pass

    try: # search interfaces
        key = winreg.key_handle(winreg.HKEY_LOCAL_MACHINE,
           r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces")
        for subkey in key.subkeys():
            for server in winreg.stringdisplay(subkey.get('NameServer', '')):
                if server:
                    defaults['server'].append(str(server))
    except EnvironmentError:
        pass



class DnsRequest:
    """ high level Request object """
    def __init__(self,*name,**args):
        self.donefunc=None
        self.async=None
        self.defaults = {}
        self.argparse(name,args)
        self.defaults = self.args

    def argparse(self,name,args):
        if not name and self.defaults.has_key('name'):
            args['name'] = self.defaults['name']
        if type(name) is types.StringType:
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
        if type(args['server']) == types.StringType:
            args['server'] = [args['server']]
        self.args=args

    def socketInit(self,a,b):
        self.s = socket.socket(a,b)

    def processUDPReply(self):
        if self.args['timeout'] > 0:
            r,w,e = select.select([self.s],[],[],self.args['timeout'])
            if not len(r):
                raise DNSError, 'Timeout'
        self.reply = self.s.recv(1024)
        self.time_finish=time.time()
        self.args['server']=self.ns
        return self.processReply()

    def processTCPReply(self):
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

    def processReply(self):
        self.args['elapsed']=(self.time_finish-self.time_start)*1000
        u = Lib.Munpacker(self.reply)
        r=Lib.DnsResult(u,self.args)
        r.args=self.args
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

    def conn(self):
        self.s.connect((self.ns,self.port))

    def req(self,*name,**args):
        " needs a refactoring "
        self.argparse(name,args)
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
        if not self.args.has_key('name'):
            print self.args
            raise DNSError,'nothing to lookup'
        qname = self.args['name']
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

    def sendUDPRequest(self, server):
        "refactor me"
        self.response=None
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

    def sendTCPRequest(self, server):
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

#class DnsAsyncRequest(DnsRequest):
class DnsAsyncRequest(DnsRequest,asyncore.dispatcher_with_send):
    " an asynchronous request object. out of date, probably broken "
    def __init__(self,*name,**args):
        DnsRequest.__init__(self, *name, **args)
        asyncore.dispatcher_with_send.__init__(self, *name, **args)
        # XXX todo
        if args.has_key('done') and args['done']:
            self.donefunc=args['done']
        else:
            self.donefunc=self.showResult
        #self.realinit(name,args) # XXX todo
        self.async=1
    def conn(self):
        self.connect((self.ns,self.port))
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

#
# $Log$
# Revision 1.9  2003/12/20 11:27:54  calvin
# more robust registry indexing
#
# Revision 1.8  2003/12/18 14:21:53  calvin
# missing import
#
# Revision 1.7  2003/12/18 14:20:37  calvin
# update nameserver parsing
#
# Revision 1.6  2003/07/04 14:23:22  calvin
# add coding line
#
# Revision 1.5  2003/01/05 17:39:19  calvin
# pychecker fixes
#
# Revision 1.4  2002/11/26 23:27:42  calvin
# update to Python >= 2.2.1
#
# Revision 1.12  2002/04/23 06:04:27  anthonybaxter
# attempt to refactor the DNSRequest.req method a little. after doing a bit
# of this, I've decided to bite the bullet and just rewrite the puppy. will
# be checkin in some design notes, then unit tests and then writing the sod.
#
# Revision 1.11  2002/03/19 13:05:02  anthonybaxter
# converted to class based exceptions (there goes the python1.4 compatibility :)
#
# removed a quite gross use of 'eval()'.
#
# Revision 1.10  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.9  2002/03/19 12:26:13  anthonybaxter
# death to leading tabs.
#
# Revision 1.8  2002/03/19 10:30:33  anthonybaxter
# first round of major bits and pieces. The major stuff here (summarised
# from my local, off-net CVS server :/ this will cause some oddities with
# the
#
# tests/testPackers.py:
#   a large slab of unit tests for the packer and unpacker code in DNS.Lib
#
# DNS/Lib.py:
#   placeholder for addSRV.
#   added 'klass' to addA, make it the same as the other A* records.
#   made addTXT check for being passed a string, turn it into a length 1 list.
#   explicitly check for adding a string of length > 255 (prohibited).
#   a bunch of cleanups from a first pass with pychecker
#   new code for pack/unpack. the bitwise stuff uses struct, for a smallish
#     (disappointly small, actually) improvement, while addr2bin is much
#     much faster now.
#
# DNS/Base.py:
#   added DiscoverNameServers. This automatically does the right thing
#     on unix/ win32. No idea how MacOS handles this.  *sigh*
#     Incompatible change: Don't use ParseResolvConf on non-unix, use this
#     function, instead!
#   a bunch of cleanups from a first pass with pychecker
#
# Revision 1.5  2001/08/09 09:22:28  anthonybaxter
# added what I hope is win32 resolver lookup support. I'll need to try
# and figure out how to get the CVS checkout onto my windows machine to
# make sure it works (wow, doing something other than games on the
# windows machine :)
#
# Code from Wolfgang.Strobl@gmd.de
# win32dns.py from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66260
#
# Really, ParseResolvConf() should be renamed "FindNameServers" or
# some such.
#
# Revision 1.4  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file
#
# Revision 1.3  2001/07/19 07:20:12  anthony
# Handle blank resolv.conf lines.
# Patch from Bastian Kleineidam
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added
#
#
