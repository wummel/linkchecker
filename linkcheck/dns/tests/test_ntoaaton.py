# -*- coding: iso-8859-1 -*-
# Copyright (C) 2003, 2004 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import unittest

import linkcheck.dns.exception
import linkcheck.dns.ipv6

class TestNtoAAtoN (unittest.TestCase):

    def test_aton1(self):
        a = linkcheck.dns.ipv6.inet_aton('::')
        self.assertEqual(a, '\x00' * 16)

    def test_aton2(self):
        a = linkcheck.dns.ipv6.inet_aton('::1')
        self.assertEqual(a, '\x00' * 15 + '\x01')

    def test_aton3(self):
        a = linkcheck.dns.ipv6.inet_aton('::10.0.0.1')
        self.assertEqual(a, '\x00' * 12 + '\x0a\x00\x00\x01')

    def test_aton4(self):
        a = linkcheck.dns.ipv6.inet_aton('abcd::dcba')
        self.assertEqual(a, '\xab\xcd' + '\x00' * 12 + '\xdc\xba')

    def test_aton5(self):
        a = linkcheck.dns.ipv6.inet_aton('1:2:3:4:5:6:7:8')
        self.assertEqual(a,
                      '00010002000300040005000600070008'.decode('hex_codec'))

    def test_bad_aton1(self):
        def bad():
            a = linkcheck.dns.ipv6.inet_aton('abcd:dcba')
        self.assertRaises(linkcheck.dns.exception.DNSSyntaxError, bad)

    def test_bad_aton2(self):
        def bad():
            a = linkcheck.dns.ipv6.inet_aton('abcd::dcba::1')
        self.assertRaises(linkcheck.dns.exception.DNSSyntaxError, bad)

    def test_bad_aton3(self):
        def bad():
            a = linkcheck.dns.ipv6.inet_aton('1:2:3:4:5:6:7:8:9')
        self.assertRaises(linkcheck.dns.exception.DNSSyntaxError, bad)

    def test_ntoa1(self):
        b = '00010002000300040005000600070008'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '1:2:3:4:5:6:7:8')

    def test_ntoa2(self):
        b = '\x00' * 16
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::')

    def test_ntoa3(self):
        b = '\x00' * 15 + '\x01'
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::1')

    def test_ntoa4(self):
        b = '\x80' + '\x00' * 15
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '8000::')

    def test_ntoa5(self):
        b = '\x01\xcd' + '\x00' * 12 + '\x03\xef'
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '1cd::3ef')

    def test_ntoa6(self):
        b = 'ffff00000000ffff000000000000ffff'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, 'ffff:0:0:ffff::ffff')

    def test_ntoa7(self):
        b = '00000000ffff000000000000ffffffff'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '0:0:ffff::ffff:ffff')

    def test_ntoa8(self):
        b = 'ffff0000ffff00000000ffff00000000'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, 'ffff:0:ffff::ffff:0:0')

    def test_ntoa9(self):
        b = '0000000000000000000000000a000001'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::10.0.0.1')

    def test_ntoa10(self):
        b = '0000000000000000000000010a000001'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::1:a00:1')

    def test_ntoa11(self):
        b = '00000000000000000000ffff0a000001'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::ffff:10.0.0.1')

    def test_ntoa12(self):
        b = '000000000000000000000000ffffffff'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::255.255.255.255')

    def test_ntoa13(self):
        b = '00000000000000000000ffffffffffff'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::ffff:255.255.255.255')

    def test_ntoa14(self):
        b = '0000000000000000000000000001ffff'.decode('hex_codec')
        t = linkcheck.dns.ipv6.inet_ntoa(b)
        self.assertEqual(t, '::0.1.255.255')

    def test_bad_ntoa1(self):
        def bad():
            a = linkcheck.dns.ipv6.inet_ntoa('')
        self.assertRaises(ValueError, bad)

    def test_bad_ntoa2(self):
        def bad():
            a = linkcheck.dns.ipv6.inet_ntoa('\x00' * 17)
        self.assertRaises(ValueError, bad)


def test_suite ():
    return unittest.makeSuite(TestNtoAAtoN)


if __name__ == '__main__':
    unittest.main()
