# -*- coding: iso-8859-1 -*-
"""test html parsing"""
# Copyright (C) 2004  Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import linkcheck.HtmlParser
import linkcheck.HtmlParser.htmlsax
import linkcheck.HtmlParser.htmllib
import cStringIO as StringIO
import unittest


# list of tuples (<test pattern>, <expected parse output>)
parsetests = [
    # start tags
    ("""<a  b="c" >""", """<a b="c">"""),
    ("""<a  b='c' >""", """<a b="c">"""),
    ("""<a  b=c" >""", """<a b="c">"""),
    ("""<a  b=c' >""", """<a b="c'">"""),
    ("""<a  b="c >""", """<a  b="c >"""),
    ("""<a  b="" >""", """<a b="">"""),
    ("""<a  b='' >""", """<a b="">"""),
    ("""<a  b=>""", """<a b="">"""),
    ("""<a  b= >""", """<a b="">"""),
    ("""<a  =c>""", """<a c>"""),
    ("""<a  =c >""", """<a c>"""),
    ("""<a  =>""", """<a>"""),
    ("""<a  = >""", """<a>"""),
    ("""<a  b= "c" >""", """<a b="c">"""),
    ("""<a  b ="c" >""", """<a b="c">"""),
    ("""<a  b = "c" >""", """<a b="c">"""),
    ("""<a >""", """<a>"""),
    ("""< a>""", """<a>"""),
    ("""< a >""", """<a>"""),
    ("""<>""", """<>"""),
    ("""< >""", """< >"""),
    # reduce test
    ("""<a  b="c"><""", """<a b="c"><"""),
    ("""d>""", """d>"""),
    # numbers in tag
    ("""<h1>bla</h1>""", """<h1>bla</h1>"""),
    # more start tags
    ("""<a  b=c"><a b="c">""", """<a b="c"><a b="c">"""),
    ("""<a  b="c><a b="c">""", """<a b="c><a b=" c>"""),
    ("""<a  b=/c/></a><br>""", """<a b="/c/"></a><br>"""),
    ("""<br/>""", """<br>"""),
    ("""<a  b="50%"><br>""", """<a b="50%"><br>"""),
    # comments
    ("""<!---->< 1>""", """<!----><1>"""),
    ("""<!-- a - b -->< 2>""", """<!-- a - b --><2>"""),
    ("""<!----->< 3>""", """<!-----><3>"""),
    ("""<!------>< 4>""", """<!------><4>"""),
    ("""<!------->< 5>""", """<!-------><5>"""),
    ("""<!---- >< 6>""", """<!----><6>"""),
    ("""<!-- -->< 7>""", """<!-- --><7>"""),
    ("""<!-- -- >< 8>""", """<!-- --><8>"""),
    ("""<!---- />-->""", """<!---- />-->"""),
    ("""<!-- a-2 -->< 9>""", """<!-- a-2 --><9>"""),
    ("""<!-- --- -->< 10>""", """<!-- --- --><10>"""),
    # end tags
    ("""</a>""", """</a>"""),
    ("""</ a>""", """</a>"""),
    ("""</ a >""", """</a>"""),
    ("""</a >""", """</a>"""),
    ("""< / a>""", """</a>"""),
    ("""< /a>""", """</a>"""),
    # missing > in end tag
    ("""</td <td  a="b" >""", """</td><td a="b">"""),
    # start and end tag
    ("""<a/>""", """<a></a>"""),
    # declaration tags
    ("""<!DOCtype adrbook SYSTEM "adrbook.dtd">""",
     """<!DOCTYPE adrbook SYSTEM "adrbook.dtd">"""),
    # misc
    ("""<?xmL version="1.0" encoding="latin1"?>""",
     """<?xmL version="1.0" encoding="latin1"?>"""),
    # javascript
    ("""<script >\n</script>""", """<script>\n</script>"""),
    ("""<sCrIpt lang="a">bla </a> fasel</scripT>""",
     """<script lang="a">bla </a> fasel</script>"""),
    # line continuation (Dr. Fun webpage)
    ("<img bo\\\nrder=0 >", """<img bo rder="0">"""),
    # href with $
    ("""<a href="123$456">""", """<a href="123$456">"""),
    # quoting
    ("""<a  href=/ >""", """<a href="/">"""),
    ("""<a  href= />""", """<a href="/">"""),
    ("""<a  href= >""", """<a href="">"""),
    ("""<a  href="'" >""", """<a href="'">"""),
    ("""<a  href='"' >""", """<a href="&quot;">"""),
    ("""<a  href="bla" %]" >""", """<a href="bla">"""),
    ("""<a  href=bla" >""", """<a href="bla">"""),
    ("""<a onmouseover=MM_swapImage('nav1','',"""\
     """'/images/dwnavpoint_over.gif',1);movein(this); b="c">""",
     """<a onmouseover="MM_swapImage('nav1','',"""\
     """'/images/dwnavpoint_over.gif',1);movein(this);" b="c">"""),
    ("""<a onClick=location.href('/index.htm') b="c">""",
     """<a onclick="location.href('/index.htm')" b="c">"""),
    # entity resolving
    ("""<a  href="&#109;ailto:" >""", """<a href="mailto:">"""),
    # non-ascii characters
    ("""<Üzgür> fahr </langsamer> ¹²³¼½¬{""",
     """<Üzgür> fahr </langsamer> ¹²³¼½¬{"""),
    # mailto link
    ("""<a  href=mailto:calvin@LocalHost?subject=Hallo&to=michi>1</a>""",
    """<a href="mailto:calvin@LocalHost?subject=Hallo&amp;to=michi">1</a>"""),
]

flushtests = [
    ("<", "<"),
    ("<a", "<a"),
    ("<!a", "<!a"),
    ("<?a", "<?a"),
]


class TestParser (unittest.TestCase):
    """test html parser"""

    def setUp (self):
        """initialize two internal html parser to be used for testing"""
        self.htmlparser = linkcheck.HtmlParser.htmlsax.parser()
        self.htmlparser2 = linkcheck.HtmlParser.htmlsax.parser()

    def test_parse (self):
        """parse all test patterns in one go"""
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            self.htmlparser.handler = \
                   linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.feed(_in)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_feed (self):
        """parse all test patterns sequentially"""
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            self.htmlparser.handler = \
                    linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            for c in _in:
                self.htmlparser.feed(c)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_interwoven (self):
        """parse all test patterns on two parsers interwoven"""
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            out2 = StringIO.StringIO()
            self.htmlparser.handler = \
                   linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser2.handler = \
                   linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out2)
            for c in _in:
                self.htmlparser.feed(c)
                self.htmlparser2.feed(c)
            self.htmlparser.flush()
            self.htmlparser2.flush()
            res = out.getvalue()
            res2 = out2.getvalue()
            self.assertEqual(res, _out)
            self.assertEqual(res2, _out)
            self.htmlparser.reset()

    def test_flush (self):
        """test parser flushing"""
        for _in, _out in flushtests:
            out = StringIO.StringIO()
            self.htmlparser.handler = \
                    linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.feed(_in)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_entities (self):
        """test entity resolving"""
        for c in "abcdefghijklmnopqrstuvwxyz":
            self.assertEqual(
                   linkcheck.HtmlParser.resolve_entities("&#%d;"%ord(c)), c)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestParser))
    return suite

if __name__ == '__main__':
    unittest.main()
