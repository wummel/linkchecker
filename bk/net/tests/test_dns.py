# -*- coding: iso-8859-1 -*-
import unittest
import bk.net
from bk.net.dns.Lib import Packer, Unpacker


class TestDns (unittest.TestCase):
    """Test DNS routines"""

    def testPacker (self):
        """Test packin/unpacking (see section 4.1.4 of RFC 1035)"""
        p = Packer()
        p.addaddr('192.168.0.1')
        p.addbytes('*' * 20)
        p.addname('f.ISI.ARPA')
        p.addbytes('*' * 8)
        p.addname('Foo.F.isi.arpa')
        p.addbytes('*' * 18)
        p.addname('arpa')
        p.addbytes('*' * 26)
        p.addname('')
        u = Unpacker(p.buf)
        self.assertEqual(u.getaddr(), '192.168.0.1')
        self.assertEqual(u.getbytes(20), '*' * 20)
        self.assertEqual(u.getname(), 'f.ISI.ARPA')
        self.assertEqual(u.getbytes(8), '*' * 8)
        self.assertEqual(u.getname(), 'Foo.f.ISI.ARPA')
        self.assertEqual(u.getbytes(18), '*' * 18)
        self.assertEqual(u.getname(), 'ARPA')
        self.assertEqual(u.getbytes(26), '*' * 26)
        self.assertEqual(u.getname(), '')

    def testHostLowercase (self):
        for host in bk.net.get_localhosts():
            self.assertEqual(host, host.lower())
        config = bk.net.resolver_config()
        for host in config.nameservers:
            self.assertEqual(host, host.lower())
        for host in config.search_domains:
            self.assertEqual(host, host.lower())
        for host in config.search_patterns:
            self.assertEqual(host, host.lower())


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDns))
    return suite

if __name__ == '__main__':
    unittest.main()

