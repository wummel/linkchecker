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

import cStringIO as StringIO
import sys
import time
import unittest

import bk.dns.name
import bk.dns.message
import bk.dns.name
import bk.dns.rdataclass
import bk.dns.rdatatype
import bk.dns.resolver

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
            f = StringIO.StringIO(resolv_conf)
            r = bk.dns.resolver.Resolver(f)
            self.assertEqual(r.nameservers, ['10.0.0.1', '10.0.0.2'])
            self.assertEqual(r.domain, bk.dns.name.from_text('foo'))

    def testCacheExpiration(self):
        message = bk.dns.message.from_text(message_text)
        name = bk.dns.name.from_text('example.')
        answer = bk.dns.resolver.Answer(name, bk.dns.rdatatype.A, bk.dns.rdataclass.IN,
                                     message)
        cache = bk.dns.resolver.Cache()
        cache.put((name, bk.dns.rdatatype.A, bk.dns.rdataclass.IN), answer)
        time.sleep(2)
        self.assert_(cache.get((name, bk.dns.rdatatype.A,
                                bk.dns.rdataclass.IN)) is None)

    def testCacheCleaning(self):
        message = bk.dns.message.from_text(message_text)
        name = bk.dns.name.from_text('example.')
        answer = bk.dns.resolver.Answer(name, bk.dns.rdatatype.A, bk.dns.rdataclass.IN,
                                     message)
        cache = bk.dns.resolver.Cache(cleaning_interval=1.0)
        cache.put((name, bk.dns.rdatatype.A, bk.dns.rdataclass.IN), answer)
        time.sleep(2)
        self.assert_(cache.get((name, bk.dns.rdatatype.A,
                                bk.dns.rdataclass.IN)) is None)


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResolver))
    return suite


if __name__ == '__main__':
    unittest.main()
