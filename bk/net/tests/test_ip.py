# -*- coding: iso-8859-1 -*-

import unittest
import bk.net.ip


class TestIp (unittest.TestCase):

    def testNames (self):
        hosts, nets = bk.net.ip.hosts2map(["www.kampfesser.net",
                                    "q2345qwer9 u2 42ß3 i34 uq3tu ",
                                    "2.3.4", ".3.4", "3.4", ".4", "4", ""])
        for host in bk.net.ip.resolve_host("www.kampfesser.net"):
            self.assert_(bk.net.ip.host_in_set(host, hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("q2345qwer9 u2 42ß3 i34 uq3tu ", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("q2345qwer9", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("2.3.4", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set(".3.4", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("3.4", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set(".4", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("4", hosts, nets))
        self.assert_(not bk.net.ip.host_in_set("", hosts, nets))

    def testIPv4_1 (self):
        hosts, nets = bk.net.ip.hosts2map(["1.2.3.4"])
        self.assert_(bk.net.ip.host_in_set("1.2.3.4", hosts, nets))

    def testNetwork1 (self):
        hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/8"])
        for i in range(255):
            self.assert_(bk.net.ip.host_in_set("192.168.1.%d"%i, hosts, nets))

    def testNetwork2 (self):
        hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/16"])
        for i in range(255):
            for j in range(255):
                self.assert_(bk.net.ip.host_in_set("192.168.%d.%d"%(i,j), hosts, nets))

    #def testNetwork3 (self):
    #    hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/24"])
    #    for i in range(255):
    #        for j in range(255):
    #            for k in range(255):
    #                self.assert_(bk.net.ip.host_in_set("192.%d.%d.%d"%(i,j,k), hosts, nets))

    def testNetwork4 (self):
        hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/255.255.255.0"])
        for i in range(255):
            self.assert_(bk.net.ip.host_in_set("192.168.1.%d"%i, hosts, nets))

    def testNetwork5 (self):
        hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/255.255.0.0"])
        for i in range(255):
            for j in range(255):
                self.assert_(bk.net.ip.host_in_set("192.168.%d.%d"%(i,j), hosts, nets))

    #def testNetwork6 (self):
    #    hosts, nets = bk.net.ip.hosts2map(["192.168.1.1/255.0.0.0"])
    #    for i in range(255):
    #        for j in range(255):
    #            for k in range(255):
    #                self.assert_(bk.net.ip.host_in_set("192.%d.%d.%d"%(i,j,k), hosts, nets))

    def testIPv6_1 (self):
        hosts, nets = bk.net.ip.hosts2map(["::0"])
        # XXX

    def testIPv6_2 (self):
        hosts, nets = bk.net.ip.hosts2map(["1::"])
        # XXX

    def testIPv6_3 (self):
        hosts, nets = bk.net.ip.hosts2map(["1::1"])
        # XXX

    def testIPv6_4 (self):
        hosts, nets = bk.net.ip.hosts2map(["fe00::0"])
        # XXX

    def testNetmask (self):
        for i in range(32):
            hosts, nets = bk.net.ip.hosts2map(["144.145.146.1/%d"%i])


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIp))
    return suite

if __name__ == '__main__':
    unittest.main()

