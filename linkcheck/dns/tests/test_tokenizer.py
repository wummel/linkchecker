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
import linkcheck.dns.tokenizer

class TestTokenizer (unittest.TestCase):

    def testQuotedString1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'"foo"')
        (ttype, value) = tok.get()
        self.assertEqual(ttype, linkcheck.dns.tokenizer.QUOTED_STRING)
        self.assertEqual(value, 'foo')

    def testQuotedString2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'""')
        (ttype, value) = tok.get()
        self.assertEqual(ttype, linkcheck.dns.tokenizer.QUOTED_STRING)
        self.assertEqual(value, '')

    def testQuotedString3(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'"\"foo\""')
        (ttype, value) = tok.get()
        self.assertEqual(ttype, linkcheck.dns.tokenizer.QUOTED_STRING)
        self.assertEqual(value, '"foo"')

    def testQuotedString4(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'"foo\010bar"')
        (ttype, value) = tok.get()
        self.assertEqual(ttype, linkcheck.dns.tokenizer.QUOTED_STRING)
        self.assertEqual(value, 'foo\x0abar')

    def testQuotedString5(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer(r'"foo')
            (ttype, value) = tok.get()
        self.assertRaises(linkcheck.dns.exception.UnexpectedEnd, bad)

    def testQuotedString6(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer(r'"foo\01')
            (ttype, value) = tok.get()
        self.assertRaises(linkcheck.dns.exception.SyntaxError, bad)

    def testQuotedString7(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer('"foo\nbar"')
            (ttype, value) = tok.get()
        self.assertRaises(linkcheck.dns.exception.SyntaxError, bad)

    def testEmpty1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('')
        (ttype, value) = tok.get()
        self.assertEqual(ttype, linkcheck.dns.tokenizer.EOF)

    def testEmpty2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('')
        (ttype1, value1) = tok.get()
        (ttype2, value2) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.EOF)
        self.assertEqual(ttype2, linkcheck.dns.tokenizer.EOF)

    def testEOL(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('\n')
        (ttype1, value1) = tok.get()
        (ttype2, value2) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.EOL)
        self.assertEqual(ttype2, linkcheck.dns.tokenizer.EOF)

    def testWS1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(' \n')
        (ttype1, value1) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.EOL)

    def testWS2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(' \n')
        (ttype1, value1) = tok.get(want_leading=True)
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.WHITESPACE)

    def testComment1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(' ;foo\n')
        (ttype1, value1) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.EOL)

    def testComment2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(' ;foo\n')
        (ttype1, value1) = tok.get(want_comment = True)
        (ttype2, value2) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.COMMENT)
        self.assertEqual(value1, 'foo')
        self.assertEqual(ttype2, linkcheck.dns.tokenizer.EOL)

    def testComment3(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(' ;foo bar\n')
        (ttype1, value1) = tok.get(want_comment = True)
        (ttype2, value2) = tok.get()
        self.assertEqual(ttype1, linkcheck.dns.tokenizer.COMMENT)
        self.assertEqual(value1, 'foo bar')
        self.assertEqual(ttype2, linkcheck.dns.tokenizer.EOL)

    def testMultiline1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('( foo\n\n bar\n)')
        tokens = list(iter(tok))
        self.assertEqual(tokens, [(linkcheck.dns.tokenizer.IDENTIFIER, 'foo'),
                                  (linkcheck.dns.tokenizer.IDENTIFIER, 'bar')])

    def testMultiline2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('( foo\n\n bar\n)\n')
        tokens = list(iter(tok))
        self.assertEqual(tokens, [(linkcheck.dns.tokenizer.IDENTIFIER, 'foo'),
                                  (linkcheck.dns.tokenizer.IDENTIFIER, 'bar'),
                                  (linkcheck.dns.tokenizer.EOL, '\n')])
    def testMultiline3(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer('foo)')
            tokens = list(iter(tok))
        self.assertRaises(linkcheck.dns.exception.SyntaxError, bad)

    def testMultiline4(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer('((foo)')
            tokens = list(iter(tok))
        self.assertRaises(linkcheck.dns.exception.SyntaxError, bad)

    def testUnget1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('foo')
        t1 = tok.get()
        tok.unget(t1)
        t2 = tok.get()
        self.assertEqual(t1, t2)
        self.assertEqual(t1, (linkcheck.dns.tokenizer.IDENTIFIER, 'foo'))

    def testUnget2(self):
        def bad():
            tok = linkcheck.dns.tokenizer.Tokenizer('foo')
            t1 = tok.get()
            tok.unget(t1)
            tok.unget(t1)
        self.assertRaises(linkcheck.dns.tokenizer.UngetBufferFull, bad)

    def testGetEOL1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('\n')
        t = tok.get_eol()
        self.assertEqual(t, '\n')

    def testGetEOL2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer('')
        t = tok.get_eol()
        self.assertEqual(t, '')

    def testEscapedDelimiter1(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'ch\ ld')
        t = tok.get()
        self.assertEqual(t, (linkcheck.dns.tokenizer.IDENTIFIER, r'ch ld'))

    def testEscapedDelimiter2(self):
        tok = linkcheck.dns.tokenizer.Tokenizer(r'ch\0ld')
        t = tok.get()
        self.assertEqual(t, (linkcheck.dns.tokenizer.IDENTIFIER, r'ch\0ld'))


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTokenizer))
    return suite


if __name__ == '__main__':
    unittest.main()
