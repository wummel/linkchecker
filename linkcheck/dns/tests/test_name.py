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
import cStringIO as StringIO

import linkcheck.dns.name

class TestName (unittest.TestCase):
    def setUp(self):
        self.origin = linkcheck.dns.name.from_text('example.')

    def testFromTextRel1(self):
        n = linkcheck.dns.name.from_text('foo.bar')
        self.assertEqual(n.labels, ('foo', 'bar', ''))

    def testFromTextRel2(self):
        n = linkcheck.dns.name.from_text('foo.bar', origin=self.origin)
        self.assertEqual(n.labels, ('foo', 'bar', 'example', ''))

    def testFromTextRel3(self):
        n = linkcheck.dns.name.from_text('foo.bar', origin=None)
        self.assertEqual(n.labels, ('foo', 'bar'))

    def testFromTextRel4(self):
        n = linkcheck.dns.name.from_text('@', origin=None)
        self.assertEqual(n, linkcheck.dns.name.empty)

    def testFromTextRel5(self):
        n = linkcheck.dns.name.from_text('@', origin=self.origin)
        self.assertEqual(n, self.origin)

    def testFromTextAbs1(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        self.assertEqual(n.labels, ('foo', 'bar', ''))

    def testTortureFromText(self):
        good = [
            r'.',
            r'a',
            r'a.',
            r'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            r'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            r'\000.\008.\010.\032.\046.\092.\099.\255',
            r'\\',
            r'\..\.',
            r'\\.\\',
            r'!"#%&/()=+-',
            r'\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255',
            ]
        bad = [
            r'..',
            r'.a',
            r'\\..',
            '\\',               # yes, we don't want the 'r' prefix!
            r'\0',
            r'\00',
            r'\00Z',
            r'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            r'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            r'\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255.\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255\255',
            ]
        for t in good:
            try:
                n = linkcheck.dns.name.from_text(t)
            except StandardError:
                self.fail("good test '%s' raised an exception" % t)
        for t in bad:
            caught = False
            try:
                n = linkcheck.dns.name.from_text(t)
            except StandardError:
                caught = True
            if not caught:
                self.fail("bad test '%s' did not raise an exception" % t)

    def testImmutable1(self):
        def bad():
            self.origin.labels = ()
        self.assertRaises(TypeError, bad)

    def testImmutable2(self):
        def bad():
            self.origin.labels[0] = 'foo'
        self.assertRaises(TypeError, bad)

    def testAbs1(self):
        self.assert_(linkcheck.dns.name.root.is_absolute())

    def testAbs2(self):
        self.assert_(not linkcheck.dns.name.empty.is_absolute())

    def testAbs3(self):
        self.assert_(self.origin.is_absolute())

    def testAbs4(self):
        n = linkcheck.dns.name.from_text('foo', origin=None)
        self.assert_(not n.is_absolute())

    def testWild1(self):
        n = linkcheck.dns.name.from_text('*.foo', origin=None)
        self.assert_(n.is_wild())

    def testWild2(self):
        n = linkcheck.dns.name.from_text('*a.foo', origin=None)
        self.assert_(not n.is_wild())

    def testWild3(self):
        n = linkcheck.dns.name.from_text('a.*.foo', origin=None)
        self.assert_(not n.is_wild())

    def testWild4(self):
        self.assert_(not linkcheck.dns.name.root.is_wild())

    def testWild5(self):
        self.assert_(not linkcheck.dns.name.empty.is_wild())

    def testHash1(self):
        n1 = linkcheck.dns.name.from_text('fOo.COM')
        n2 = linkcheck.dns.name.from_text('foo.com')
        self.assertEqual(hash(n1), hash(n2))

    def testCompare1(self):
        n1 = linkcheck.dns.name.from_text('a')
        n2 = linkcheck.dns.name.from_text('b')
        self.assert_(n1 < n2)
        self.assert_(n2 > n1)

    def testCompare2(self):
        n1 = linkcheck.dns.name.from_text('')
        n2 = linkcheck.dns.name.from_text('b')
        self.assert_(n1 < n2)
        self.assert_(n2 > n1)

    def testCompare3(self):
        self.assert_(linkcheck.dns.name.empty < linkcheck.dns.name.root)
        self.assert_(linkcheck.dns.name.root > linkcheck.dns.name.empty)

    def testCompare4(self):
        self.assertNotEqual(linkcheck.dns.name.root, 1)

    def testCompare5(self):
        self.assert_(linkcheck.dns.name.root < 1 or linkcheck.dns.name.root > 1)

    def testSubdomain1(self):
        self.assert_(not linkcheck.dns.name.empty.is_subdomain(linkcheck.dns.name.root))

    def testSubdomain2(self):
        self.assert_(not linkcheck.dns.name.root.is_subdomain(linkcheck.dns.name.empty))

    def testSubdomain3(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(n.is_subdomain(self.origin))

    def testSubdomain4(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(n.is_subdomain(linkcheck.dns.name.root))

    def testSubdomain5(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(n.is_subdomain(n))

    def testSuperdomain1(self):
        self.assert_(not linkcheck.dns.name.empty.is_superdomain(linkcheck.dns.name.root))

    def testSuperdomain2(self):
        self.assert_(not linkcheck.dns.name.root.is_superdomain(linkcheck.dns.name.empty))

    def testSuperdomain3(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(self.origin.is_superdomain(n))

    def testSuperdomain4(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(linkcheck.dns.name.root.is_superdomain(n))

    def testSuperdomain5(self):
        n = linkcheck.dns.name.from_text('foo', origin=self.origin)
        self.assert_(n.is_superdomain(n))

    def testCanonicalize1(self):
        n = linkcheck.dns.name.from_text('FOO.bar', origin=self.origin)
        c = n.canonicalize()
        self.assertEqual(c.labels, ('foo', 'bar', 'example', ''))

    def testToText1(self):
        n = linkcheck.dns.name.from_text('FOO.bar', origin=self.origin)
        t = n.to_text()
        self.assertEqual(t, 'FOO.bar.example.')

    def testToText2(self):
        n = linkcheck.dns.name.from_text('FOO.bar', origin=self.origin)
        t = n.to_text(True)
        self.assertEqual(t, 'FOO.bar.example')

    def testToText3(self):
        n = linkcheck.dns.name.from_text('FOO.bar', origin=None)
        t = n.to_text()
        self.assertEqual(t, 'FOO.bar')

    def testToText4(self):
        t = linkcheck.dns.name.empty.to_text()
        self.assertEqual(t, '@')

    def testToText5(self):
        t = linkcheck.dns.name.root.to_text()
        self.assertEqual(t, '.')

    def testToText6(self):
        n = linkcheck.dns.name.from_text('FOO bar', origin=None)
        t = n.to_text()
        self.assertEqual(t, r'FOO\032bar')

    def testToText7(self):
        n = linkcheck.dns.name.from_text(r'FOO\.bar', origin=None)
        t = n.to_text()
        self.assertEqual(t, r'FOO\.bar')

    def testToText8(self):
        n = linkcheck.dns.name.from_text(r'\070OO\.bar', origin=None)
        t = n.to_text()
        self.assertEqual(t, r'FOO\.bar')

    def testSlice1(self):
        n = linkcheck.dns.name.from_text(r'a.b.c.', origin=None)
        s = n[:]
        self.assertEqual(s, ('a', 'b', 'c', ''))

    def testSlice2(self):
        n = linkcheck.dns.name.from_text(r'a.b.c.', origin=None)
        s = n[:2]
        self.assertEqual(s, ('a', 'b'))

    def testSlice3(self):
        n = linkcheck.dns.name.from_text(r'a.b.c.', origin=None)
        s = n[2:]
        self.assertEqual(s, ('c', ''))

    def testEmptyLabel1(self):
        def bad():
            n = linkcheck.dns.name.Name(['a', '', 'b'])
        self.assertRaises(linkcheck.dns.name.EmptyLabel, bad)

    def testEmptyLabel2(self):
        def bad():
            n = linkcheck.dns.name.Name(['', 'b'])
        self.assertRaises(linkcheck.dns.name.EmptyLabel, bad)

    def testEmptyLabel3(self):
        n = linkcheck.dns.name.Name(['b', ''])
        self.assert_(n)

    def testLongLabel(self):
        n = linkcheck.dns.name.Name(['a' * 63])
        self.assert_(n)

    def testLabelTooLong(self):
        def bad():
            n = linkcheck.dns.name.Name(['a' * 64, 'b'])
        self.assertRaises(linkcheck.dns.name.LabelTooLong, bad)

    def testLongName(self):
        n = linkcheck.dns.name.Name(['a' * 63, 'a' * 63, 'a' * 63, 'a' * 62])
        self.assert_(n)

    def testNameTooLong(self):
        def bad():
            n = linkcheck.dns.name.Name(['a' * 63, 'a' * 63, 'a' * 63, 'a' * 63])
        self.assertRaises(linkcheck.dns.name.NameTooLong, bad)

    def testConcat1(self):
        n1 = linkcheck.dns.name.Name(['a', 'b'])
        n2 = linkcheck.dns.name.Name(['c', 'd'])
        e = linkcheck.dns.name.Name(['a', 'b', 'c', 'd'])
        r = n1 + n2
        self.assertEqual(r, e)

    def testConcat2(self):
        n1 = linkcheck.dns.name.Name(['a', 'b'])
        n2 = linkcheck.dns.name.Name([])
        e = linkcheck.dns.name.Name(['a', 'b'])
        r = n1 + n2
        self.assertEqual(r, e)

    def testConcat2a(self):
        n1 = linkcheck.dns.name.Name([])
        n2 = linkcheck.dns.name.Name(['a', 'b'])
        e = linkcheck.dns.name.Name(['a', 'b'])
        r = n1 + n2
        self.assertEqual(r, e)

    def testConcat3(self):
        n1 = linkcheck.dns.name.Name(['a', 'b', ''])
        n2 = linkcheck.dns.name.Name([])
        e = linkcheck.dns.name.Name(['a', 'b', ''])
        r = n1 + n2
        self.assertEqual(r, e)

    def testConcat4(self):
        n1 = linkcheck.dns.name.Name(['a', 'b'])
        n2 = linkcheck.dns.name.Name(['c', ''])
        e = linkcheck.dns.name.Name(['a', 'b', 'c', ''])
        r = n1 + n2
        self.assertEqual(r, e)

    def testConcat5(self):
        def bad():
            n1 = linkcheck.dns.name.Name(['a', 'b', ''])
            n2 = linkcheck.dns.name.Name(['c'])
            r = n1 + n2
        self.assertRaises(linkcheck.dns.name.AbsoluteConcatenation, bad)

    def testBadEscape(self):
        def bad():
            n = linkcheck.dns.name.from_text(r'a.b\0q1.c.')
            print n
        self.assertRaises(linkcheck.dns.name.BadEscape, bad)

    def testDigestable1(self):
        n = linkcheck.dns.name.from_text('FOO.bar')
        d = n.to_digestable()
        self.assertEqual(d, '\x03foo\x03bar\x00')

    def testDigestable2(self):
        n1 = linkcheck.dns.name.from_text('FOO.bar')
        n2 = linkcheck.dns.name.from_text('foo.BAR.')
        d1 = n1.to_digestable()
        d2 = n2.to_digestable()
        self.assertEqual(d1, d2)

    def testDigestable3(self):
        d = linkcheck.dns.name.root.to_digestable()
        self.assertEqual(d, '\x00')

    def testDigestable4(self):
        n = linkcheck.dns.name.from_text('FOO.bar', None)
        d = n.to_digestable(linkcheck.dns.name.root)
        self.assertEqual(d, '\x03foo\x03bar\x00')

    def testBadDigestable(self):
        def bad():
            n = linkcheck.dns.name.from_text('FOO.bar', None)
            d = n.to_digestable()
        self.assertRaises(linkcheck.dns.name.NeedAbsoluteNameOrOrigin, bad)

    def testToWire1(self):
        n = linkcheck.dns.name.from_text('FOO.bar')
        f = StringIO.StringIO()
        compress = {}
        n.to_wire(f, compress)
        self.assertEqual(f.getvalue(), '\x03FOO\x03bar\x00')

    def testToWire2(self):
        n = linkcheck.dns.name.from_text('FOO.bar')
        f = StringIO.StringIO()
        compress = {}
        n.to_wire(f, compress)
        n.to_wire(f, compress)
        self.assertEqual(f.getvalue(), '\x03FOO\x03bar\x00\xc0\x00')

    def testToWire3(self):
        n1 = linkcheck.dns.name.from_text('FOO.bar')
        n2 = linkcheck.dns.name.from_text('foo.bar')
        f = StringIO.StringIO()
        compress = {}
        n1.to_wire(f, compress)
        n2.to_wire(f, compress)
        self.assertEqual(f.getvalue(), '\x03FOO\x03bar\x00\xc0\x00')

    def testToWire4(self):
        n1 = linkcheck.dns.name.from_text('FOO.bar')
        n2 = linkcheck.dns.name.from_text('a.foo.bar')
        f = StringIO.StringIO()
        compress = {}
        n1.to_wire(f, compress)
        n2.to_wire(f, compress)
        self.assertEqual(f.getvalue(), '\x03FOO\x03bar\x00\x01\x61\xc0\x00')

    def testToWire5(self):
        n1 = linkcheck.dns.name.from_text('FOO.bar')
        n2 = linkcheck.dns.name.from_text('a.foo.bar')
        f = StringIO.StringIO()
        compress = {}
        n1.to_wire(f, compress)
        n2.to_wire(f, None)
        self.assertEqual(f.getvalue(),
                         '\x03FOO\x03bar\x00\x01\x61\x03foo\x03bar\x00')

    def testBadToWire(self):
        def bad():
            n = linkcheck.dns.name.from_text('FOO.bar', None)
            f = StringIO.StringIO()
            compress = {}
            n.to_wire(f, compress)
        self.assertRaises(linkcheck.dns.name.NeedAbsoluteNameOrOrigin, bad)

    def testSplit1(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        (prefix, suffix) = n.split(2)
        ep = linkcheck.dns.name.from_text('foo', None)
        es = linkcheck.dns.name.from_text('bar.', None)
        self.assertEqual(prefix, ep)
        self.assertEqual(suffix, es)

    def testSplit2(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        (prefix, suffix) = n.split(1)
        ep = linkcheck.dns.name.from_text('foo.bar', None)
        es = linkcheck.dns.name.from_text('.', None)
        self.assertEqual(prefix, ep)
        self.assertEqual(suffix, es)

    def testSplit3(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        (prefix, suffix) = n.split(0)
        ep = linkcheck.dns.name.from_text('foo.bar.', None)
        es = linkcheck.dns.name.from_text('', None)
        self.assertEqual(prefix, ep)
        self.assertEqual(suffix, es)

    def testSplit4(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        (prefix, suffix) = n.split(3)
        ep = linkcheck.dns.name.from_text('', None)
        es = linkcheck.dns.name.from_text('foo.bar.', None)
        self.assertEqual(prefix, ep)
        self.assertEqual(suffix, es)

    def testBadSplit1(self):
        def bad():
            n = linkcheck.dns.name.from_text('foo.bar.')
            (prefix, suffix) = n.split(-1)
        self.assertRaises(ValueError, bad)

    def testBadSplit2(self):
        def bad():
            n = linkcheck.dns.name.from_text('foo.bar.')
            (prefix, suffix) = n.split(4)
        self.assertRaises(ValueError, bad)

    def testRelativize1(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = linkcheck.dns.name.from_text('bar.', None)
        e = linkcheck.dns.name.from_text('a.foo', None)
        self.assert_(n.relativize(o) == e)

    def testRelativize2(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = n
        e = linkcheck.dns.name.empty
        self.assertEqual(n.relativize(o), e)

    def testRelativize3(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = linkcheck.dns.name.from_text('blaz.', None)
        e = n
        self.assertEqual(n.relativize(o), e)

    def testRelativize4(self):
        n = linkcheck.dns.name.from_text('a.foo', None)
        o = linkcheck.dns.name.root
        e = n
        self.assertEqual(n.relativize(o), e)

    def testDerelativize1(self):
        n = linkcheck.dns.name.from_text('a.foo', None)
        o = linkcheck.dns.name.from_text('bar.', None)
        e = linkcheck.dns.name.from_text('a.foo.bar.', None)
        self.assertEqual(n.derelativize(o), e)

    def testDerelativize2(self):
        n = linkcheck.dns.name.empty
        o = linkcheck.dns.name.from_text('a.foo.bar.', None)
        e = o
        self.assertEqual(n.derelativize(o), e)

    def testDerelativize3(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = linkcheck.dns.name.from_text('blaz.', None)
        e = n
        self.assertEqual(n.derelativize(o), e)

    def testChooseRelativity1(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = linkcheck.dns.name.from_text('bar.', None)
        e = linkcheck.dns.name.from_text('a.foo', None)
        self.assertEqual(n.choose_relativity(o, True), e)

    def testChooseRelativity2(self):
        n = linkcheck.dns.name.from_text('a.foo.bar.', None)
        o = linkcheck.dns.name.from_text('bar.', None)
        e = n
        self.assertEqual(n.choose_relativity(o, False), e)

    def testChooseRelativity3(self):
        n = linkcheck.dns.name.from_text('a.foo', None)
        o = linkcheck.dns.name.from_text('bar.', None)
        e = linkcheck.dns.name.from_text('a.foo.bar.', None)
        self.assertEqual(n.choose_relativity(o, False), e)

    def testChooseRelativity4(self):
        n = linkcheck.dns.name.from_text('a.foo', None)
        o = None
        e = n
        self.assertEqual(n.choose_relativity(o, True), e)

    def testChooseRelativity5(self):
        n = linkcheck.dns.name.from_text('a.foo', None)
        o = None
        e = n
        self.assertEqual(n.choose_relativity(o, False), e)

    def testChooseRelativity6(self):
        n = linkcheck.dns.name.from_text('a.foo.', None)
        o = None
        e = n
        self.assertEqual(n.choose_relativity(o, True), e)

    def testChooseRelativity7(self):
        n = linkcheck.dns.name.from_text('a.foo.', None)
        o = None
        e = n
        self.assertEqual(n.choose_relativity(o, False), e)

    def testFromWire1(self):
        w = '\x03foo\x00\xc0\x00'
        (n1, cused1) = linkcheck.dns.name.from_wire(w, 0)
        (n2, cused2) = linkcheck.dns.name.from_wire(w, cused1)
        en1 = linkcheck.dns.name.from_text('foo.')
        en2 = en1
        ecused1 = 5
        ecused2 = 2
        self.assertEqual(n1, en1)
        self.assertEqual(cused1, ecused1)
        self.assertEqual(n2, en2)
        self.assertEqual(cused2, ecused2)

    def testFromWire2(self):
        w = '\x03foo\x00\x01a\xc0\x00\x01b\xc0\x05'
        current = 0
        (n1, cused1) = linkcheck.dns.name.from_wire(w, current)
        current += cused1
        (n2, cused2) = linkcheck.dns.name.from_wire(w, current)
        current += cused2
        (n3, cused3) = linkcheck.dns.name.from_wire(w, current)
        en1 = linkcheck.dns.name.from_text('foo.')
        en2 = linkcheck.dns.name.from_text('a.foo.')
        en3 = linkcheck.dns.name.from_text('b.a.foo.')
        ecused1 = 5
        ecused2 = 4
        ecused3 = 4
        self.assertEqual(n1, en1)
        self.assertEqual(cused1, ecused1)
        self.assertEqual(n2, en2)
        self.assertEqual(cused2, ecused2)
        self.assertEqual(n3, en3)
        self.assertEqual(cused3, ecused3)

    def testBadFromWire1(self):
        def bad():
            w = '\x03foo\xc0\x04'
            (n, cused) = linkcheck.dns.name.from_wire(w, 0)
        self.assertRaises(linkcheck.dns.name.BadPointer, bad)

    def testBadFromWire2(self):
        def bad():
            w = '\x03foo\xc0\x05'
            (n, cused) = linkcheck.dns.name.from_wire(w, 0)
        self.assertRaises(linkcheck.dns.name.BadPointer, bad)

    def testBadFromWire3(self):
        def bad():
            w = '\xbffoo'
            (n, cused) = linkcheck.dns.name.from_wire(w, 0)
        self.assertRaises(linkcheck.dns.name.BadLabelType, bad)

    def testBadFromWire4(self):
        def bad():
            w = '\x41foo'
            (n, cused) = linkcheck.dns.name.from_wire(w, 0)
        self.assertRaises(linkcheck.dns.name.BadLabelType, bad)

    def testParent1(self):
        n = linkcheck.dns.name.from_text('foo.bar.')
        self.failUnless(n.parent() == linkcheck.dns.name.from_text('bar.'))
        self.failUnless(n.parent().parent() == linkcheck.dns.name.root)

    def testParent2(self):
        n = linkcheck.dns.name.from_text('foo.bar', None)
        self.failUnless(n.parent() == linkcheck.dns.name.from_text('bar', None))
        self.failUnless(n.parent().parent() == linkcheck.dns.name.empty)

    def testParent3(self):
        def bad():
            n = linkcheck.dns.name.root
            n.parent()
        self.failUnlessRaises(linkcheck.dns.name.NoParent, bad)

    def testParent4(self):
        def bad():
            n = linkcheck.dns.name.empty
            n.parent()
        self.failUnlessRaises(linkcheck.dns.name.NoParent, bad)


def test_suite ():
    return unittest.makeSuite(TestName)


if __name__ == '__main__':
    unittest.main()
