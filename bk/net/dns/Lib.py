# -*- coding: iso-8859-1 -*-
"""
 This file is part of the pydns project.
 Homepage: http://pydns.sourceforge.net

 This code is covered by the standard Python License.

 Library code. Largely this is packers and unpackers for various types.
"""

#
# See RFC 1035:
# ------------------------------------------------------------------------
# Network Working Group                                     P. Mockapetris
# Request for Comments: 1035                                           ISI
#                                                            November 1987
# Obsoletes: RFCs 882, 883, 973
#
#             DOMAIN NAMES - IMPLEMENTATION AND SPECIFICATION
# ------------------------------------------------------------------------


import types
import Type
import Class
import Opcode
import Status


class DNSError (Exception):
    """basic DNS error class"""
    pass


class UnpackError (DNSError):
    """DNS packet unpacking error"""
    pass


class PackError (DNSError):
    """DNS packet packing error"""
    pass


# Low-level 16 and 32 bit integer packing and unpacking

from struct import pack as struct_pack
from struct import unpack as struct_unpack


def pack16bit (n):
    return struct_pack('!H', n)


def pack32bit (n):
    return struct_pack('!L', n)


def pack128bit (n):
    return struct_pack('!LLLL', n)


def unpack16bit (s):
    return struct_unpack('!H', s)[0]


def unpack32bit (s):
    return struct_unpack('!L', s)[0]


def unpack128bit (s):
    return struct_unpack('!LLLL', s)[0]


def addr2bin (addr):
    if type(addr) == type(0):
        return addr
    bytes = addr.split('.')
    if len(bytes) != 4: raise ValueError, 'bad IP address'
    n = 0L
    for byte in bytes:
        n = n<<8 | int(byte)
    return n


def bin2addr (n):
    return '%d.%d.%d.%d' % ((n>>24)&0xFF, (n>>16)&0xFF,
                  (n>>8)&0xFF, n&0xFF)


# Packing class

class Packer (object):
    " packer base class. supports basic byte/16bit/32bit/addr/string/name "

    def __init__ (self):
        self.buf = ''
        self.index = {}


    def getbuf (self):
        return self.buf


    def addbyte (self, c):
        if len(c) != 1: raise TypeError, 'one character expected'
        self.buf += c


    def addbytes (self, bytes):
        self.buf += bytes


    def add16bit (self, n):
        self.buf += pack16bit(n)


    def add32bit (self, n):
        self.buf += pack32bit(n)


    def addaddr (self, addr):
        n = addr2bin(addr)
        self.buf += pack32bit(n)


    def addaddr6 (self, addr):
        n = addr2bin(addr)
        self.buf += pack128bit(n)


    def addstring (self, s):
        if len(s) > 255:
            raise ValueError, "Can't encode string of length "+ \
                            "%s (> 255)"%(len(s))
        self.addbyte(chr(len(s)))
        self.addbytes(s)


    def addname (self, name):
        """Domain name packing (section 4.1.4)
           Add a domain name to the buffer, possibly using pointers.
           The case of the first occurrence of a name is preserved.
           Redundant dots are ignored.
        """
        lst = []
        for label in name.split('.'):
            if label:
                if len(label) > 63:
                    raise PackError, 'label too long'
                lst.append(label)
        keys = []
        for i in range(len(lst)):
            key = '.'.join(lst[i:]).upper()
            keys.append(key)
            if self.index.has_key(key):
                pointer = self.index[key]
                break
        else:
            i = len(lst)
            pointer = None
        # Do it into temporaries first so exceptions don't
        # mess up self.index and self.buf
        buf = ''
        offset = len(self.buf)
        index = []
        for j in range(i):
            label = lst[j]
            n = len(label)
            if offset + len(buf) < 0x3FFF:
                index.append((keys[j], offset + len(buf)))
            else:
                print 'DNS.Lib.Packer.addname:',
                print 'warning: pointer too big'
            buf += (chr(n) + label)
        if pointer:
            buf += pack16bit(pointer | 0xC000)
        else:
            buf += '\0'
        self.buf += buf
        for key, value in index:
            self.index[key] = value


    def dump (self):
        """print string dump of packer data"""
        keys = self.index.keys()
        keys.sort()
        print '-'*40
        for key in keys:
            print '%20s %3d' % (key, self.index[key])
        print '-'*40
        space = 1
        for i in range(0, len(self.buf)+1, 2):
            if self.buf[i:i+2] == '**':
                if not space: print
                space = 1
                continue
            space = 0
            print '%4d' % i,
            for c in self.buf[i:i+2]:
                if ' ' < c < '\177':
                    print ' %c' % c,
                else:
                    print '%2d' % ord(c),
            print
        print '-'*40


# Unpacking class


class Unpacker (object):

    def __init__ (self, buf):
        self.buf = buf
        self.offset = 0


    def getbyte (self):
        if self.offset > len(self.buf):
            raise UnpackError, "Ran off end of data"
        c = self.buf[self.offset]
        self.offset += 1
        return c


    def getbytes (self, n):
        s = self.buf[self.offset : self.offset + n]
        if len(s) != n: raise UnpackError, 'not enough data left'
        self.offset +=n
        return s


    def get16bit (self):
        return unpack16bit(self.getbytes(2))


    def get32bit (self):
        return unpack32bit(self.getbytes(4))


    def get128bit (self):
        return unpack128bit(self.getbytes(16))


    def getaddr (self):
        return bin2addr(self.get32bit())


    def getaddr6 (self):
        return bin2addr(self.get128bit())


    def getstring (self):
        return self.getbytes(ord(self.getbyte()))


    def getname (self):
        # Domain name unpacking (section 4.1.4)
        c = self.getbyte()
        i = ord(c)
        if i & 0xC0 == 0xC0:
            d = self.getbyte()
            j = ord(d)
            pointer = ((i<<8) | j) & ~0xC000
            save_offset = self.offset
            try:
                self.offset = pointer
                domain = self.getname()
            finally:
                self.offset = save_offset
            return domain
        if i == 0:
            return ''
        domain = self.getbytes(i)
        remains = self.getname()
        if not remains:
            return domain
        else:
            return domain + '.' + remains


# Pack/unpack RR toplevel format (section 3.2.1)

class RRpacker (Packer):

    def __init__ (self):
        Packer.__init__(self)
        self.rdstart = None


    def addRRheader (self, name, type, klass, ttl, *rest):
        self.addname(name)
        self.add16bit(type)
        self.add16bit(klass)
        self.add32bit(ttl)
        if rest:
            if rest[1:]: raise TypeError, 'too many args'
            rdlength = rest[0]
        else:
            rdlength = 0
        self.add16bit(rdlength)
        self.rdstart = len(self.buf)


    def patchrdlength (self):
        rdlength = unpack16bit(self.buf[self.rdstart-2:self.rdstart])
        if rdlength == len(self.buf) - self.rdstart:
            return
        rdata = self.buf[self.rdstart:]
        save_buf = self.buf
        ok = 0
        try:
            self.buf = self.buf[:self.rdstart-2]
            self.add16bit(len(rdata))
            self.buf = self.buf + rdata
            ok = 1
        finally:
            if not ok: self.buf = save_buf


    def endRR (self):
        if self.rdstart is not None:
            self.patchrdlength()
        self.rdstart = None


    def getbuf (self):
        if self.rdstart is not None: self.patchrdlength()
        return Packer.getbuf(self)
    # Standard RRs (section 3.3)


    def addCNAME (self, name, klass, ttl, cname):
        self.addRRheader(name, Type.CNAME, klass, ttl)
        self.addname(cname)
        self.endRR()


    def addHINFO (self, name, klass, ttl, cpu, os):
        self.addRRheader(name, Type.HINFO, klass, ttl)
        self.addstring(cpu)
        self.addstring(os)
        self.endRR()


    def addMX (self, name, klass, ttl, preference, exchange):
        self.addRRheader(name, Type.MX, klass, ttl)
        self.add16bit(preference)
        self.addname(exchange)
        self.endRR()


    def addNS (self, name, klass, ttl, nsdname):
        self.addRRheader(name, Type.NS, klass, ttl)
        self.addname(nsdname)
        self.endRR()


    def addPTR (self, name, klass, ttl, ptrdname):
        self.addRRheader(name, Type.PTR, klass, ttl)
        self.addname(ptrdname)
        self.endRR()


    def addSOA (self, name, klass, ttl,
                mname, rname, serial, refresh, retry, expire, minimum):
        self.addRRheader(name, Type.SOA, klass, ttl)
        self.addname(mname)
        self.addname(rname)
        self.add32bit(serial)
        self.add32bit(refresh)
        self.add32bit(retry)
        self.add32bit(expire)
        self.add32bit(minimum)
        self.endRR()


    def addTXT (self, name, klass, ttl, lst):
        self.addRRheader(name, Type.TXT, klass, ttl)
        if type(lst) is types.StringType:
            lst = [lst]
        for txtdata in lst:
            self.addstring(txtdata)
        self.endRR()
    # Internet specific RRs (section 3.4) -- class = IN


    def addA (self, name, klass, ttl, address):
        self.addRRheader(name, Type.A, klass, ttl)
        self.addaddr(address)
        self.endRR()


    def addAAAA (self, name, klass, ttl, address):
        self.addRRheader(name, Type.A, klass, ttl)
        self.addaddr6(address)
        self.endRR()


    def addWKS (self, name, ttl, address, protocol, bitmap):
        self.addRRheader(name, Type.WKS, Class.IN, ttl)
        self.addaddr(address)
        self.addbyte(chr(protocol))
        self.addbytes(bitmap)
        self.endRR()


    def addSRV (self):
        raise NotImplementedError


def prettyTime (seconds):

    if seconds<60:
        return seconds,"%d seconds"%(seconds)
    if seconds<3600:
        return seconds,"%d minutes"%(seconds/60)
    if seconds<86400:
        return seconds,"%d hours"%(seconds/3600)
    if seconds<604800:
        return seconds,"%d days"%(seconds/86400)
    else:
        return seconds,"%d weeks"%(seconds/604800)


class RRunpacker (Unpacker):

    def __init__ (self, buf):
        Unpacker.__init__(self, buf)
        self.rdend = None


    def getRRheader (self):
        name = self.getname()
        rrtype = self.get16bit()
        klass = self.get16bit()
        ttl = self.get32bit()
        rdlength = self.get16bit()
        self.rdend = self.offset + rdlength
        return (name, rrtype, klass, ttl, rdlength)


    def endRR (self):
        if self.offset != self.rdend:
            raise UnpackError, 'end of RR not reached'


    def getCNAMEdata (self):
        return self.getname()


    def getHINFOdata (self):
        return self.getstring(), self.getstring()


    def getMXdata (self):
        return self.get16bit(), self.getname()


    def getNSdata (self):
        return self.getname()


    def getPTRdata (self):
        return self.getname()


    def getSOAdata (self):
        return self.getname(), \
               self.getname(), \
               ('serial',)+(self.get32bit(),), \
               ('refresh ',)+prettyTime(self.get32bit()), \
               ('retry',)+prettyTime(self.get32bit()), \
               ('expire',)+prettyTime(self.get32bit()), \
               ('minimum',)+prettyTime(self.get32bit())


    def getTXTdata (self):
        lst = []
        while self.offset != self.rdend:
            lst.append(self.getstring())
        return lst


    def getAdata (self):
        return self.getaddr()


    def getAAAAdata (self):
        return self.getaddr6()


    def getWKSdata (self):
        address = self.getaddr()
        protocol = ord(self.getbyte())
        bitmap = self.getbytes(self.rdend - self.offset)
        return address, protocol, bitmap


    def getSRVdata (self):
        """
        _Service._Proto.Name TTL Class SRV Priority Weight Port Target
        """
        priority = self.get16bit()
        weight = self.get16bit()
        port = self.get16bit()
        target = self.getname()
        #print '***priority, weight, port, target', priority, weight, port, target
        return priority, weight, port, target


# Pack/unpack Message Header (section 4.1)

class Hpacker (Packer):

    def addHeader (self, rid, qr, opcode, aa, tc, rd, ra, z, rcode,
              qdcount, ancount, nscount, arcount):
        self.add16bit(rid)
        self.add16bit((qr&1)<<15 | (opcode&0xF)<<11 | (aa&1)<<10
                  | (tc&1)<<9 | (rd&1)<<8 | (ra&1)<<7
                  | (z&7)<<4 | (rcode&0xF))
        self.add16bit(qdcount)
        self.add16bit(ancount)
        self.add16bit(nscount)
        self.add16bit(arcount)


class Hunpacker (Unpacker):

    def getHeader (self):
        rid = self.get16bit()
        flags = self.get16bit()
        qr, opcode, aa, tc, rd, ra, z, rcode = (
                  (flags>>15)&1,
                  (flags>>11)&0xF,
                  (flags>>10)&1,
                  (flags>>9)&1,
                  (flags>>8)&1,
                  (flags>>7)&1,
                  (flags>>4)&7,
                  (flags>>0)&0xF)
        qdcount = self.get16bit()
        ancount = self.get16bit()
        nscount = self.get16bit()
        arcount = self.get16bit()
        return (rid, qr, opcode, aa, tc, rd, ra, z, rcode,
                qdcount, ancount, nscount, arcount)


# Pack/unpack Question (section 4.1.2)

class Qpacker (Packer):

    def addQuestion (self, qname, qtype, qclass):
        self.addname(qname)
        self.add16bit(qtype)
        self.add16bit(qclass)


class Qunpacker (Unpacker):

    def getQuestion (self):
        return self.getname(), self.get16bit(), self.get16bit()


# Pack/unpack Message(section 4)
# NB the order of the base classes is important for __init__()!

class Mpacker (RRpacker, Qpacker, Hpacker):
    pass


class Munpacker (RRunpacker, Qunpacker, Hunpacker):
    pass

