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

from cStringIO import StringIO
import sys
import time
import unittest

import linkcheck.dns.name
import linkcheck.dns.message
import linkcheck.dns.name
import linkcheck.dns.rdataclass
import linkcheck.dns.rdatatype
import linkcheck.dns.resolver

resolv_conf = """
    /t/t
# comment 1
; comment 2
domain foo
nameserver 10.0.0.1
nameserver 10.0.0.2
"""

message_text = """id 1234
opcode QUERY
rcode NOERROR
flags QR AA RD
;QUESTION
example. IN A
;ANSWER
example. 1 IN A 10.0.0.1
;AUTHORITY
;ADDITIONAL
"""

class TestResolver (unittest.TestCase):

    if sys.platform != 'win32':
        def testRead(self):
            f = StringIO(resolv_conf)
            r = linkcheck.dns.resolver.Resolver(f)
            self.assertEqual(r.nameservers, ['10.0.0.1', '10.0.0.2'])
            self.assertEqual(r.domain, linkcheck.dns.name.from_text('foo'))

    def testCacheExpiration(self):
        message = linkcheck.dns.message.from_text(message_text)
        name = linkcheck.dns.name.from_text('example.')
        answer = linkcheck.dns.resolver.Answer(name, linkcheck.dns.rdatatype.A, linkcheck.dns.rdataclass.IN,
                                     message)
        cache = linkcheck.dns.resolver.Cache()
        cache.put((name, linkcheck.dns.rdatatype.A, linkcheck.dns.rdataclass.IN), answer)
        time.sleep(2)
        self.assert_(cache.get((name, linkcheck.dns.rdatatype.A,
                                linkcheck.dns.rdataclass.IN)) is None)

    def testCacheCleaning(self):
        message = linkcheck.dns.message.from_text(message_text)
        name = linkcheck.dns.name.from_text('example.')
        answer = linkcheck.dns.resolver.Answer(name, linkcheck.dns.rdatatype.A, linkcheck.dns.rdataclass.IN,
                                     message)
        cache = linkcheck.dns.resolver.Cache(cleaning_interval=1.0)
        cache.put((name, linkcheck.dns.rdatatype.A, linkcheck.dns.rdataclass.IN), answer)
        time.sleep(2)
        self.assert_(cache.get((name, linkcheck.dns.rdatatype.A,
                                linkcheck.dns.rdataclass.IN)) is None)

    def testZoneForName1(self):
        name = linkcheck.dns.name.from_text('www.dnspython.org.')
        ezname = linkcheck.dns.name.from_text('dnspython.org.')
        zname = linkcheck.dns.resolver.zone_for_name(name)
        self.failUnless(zname == ezname)

    def testZoneForName2(self):
        name = linkcheck.dns.name.from_text('a.b.www.dnspython.org.')
        ezname = linkcheck.dns.name.from_text('dnspython.org.')
        zname = linkcheck.dns.resolver.zone_for_name(name)
        self.failUnless(zname == ezname)

    def testZoneForName3(self):
        name = linkcheck.dns.name.from_text('dnspython.org.')
        ezname = linkcheck.dns.name.from_text('dnspython.org.')
        zname = linkcheck.dns.resolver.zone_for_name(name)
        self.failUnless(zname == ezname)

    def testZoneForName4(self):
        def bad():
            name = linkcheck.dns.name.from_text('dnspython.org', None)
            zname = linkcheck.dns.resolver.zone_for_name(name)
        self.failUnlessRaises(linkcheck.dns.resolver.NotAbsolute, bad)


def test_suite ():
    return unittest.makeSuite(TestResolver)


if __name__ == '__main__':
    unittest.main()
