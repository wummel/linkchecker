# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2005  Bastian Kleineidam
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
"""
Test html parsing.
"""

import linkcheck.HtmlParser
import linkcheck.HtmlParser.htmlsax
import linkcheck.HtmlParser.htmllib
import cStringIO as StringIO
import unittest
from linkcheck.tests import MsgTestCase


# list of tuples
# (<test pattern>, <expected parse output>, <no. of expected errors>)
parsetests = [
    # start tags
    ("""<a  b="c" >""", """<a b="c">""", 0),
    ("""<a  b='c' >""", """<a b="c">""", 0),
    ("""<a  b=c" >""", """<a b="c">""", 1),
    ("""<a  b=c' >""", """<a b="c'">""", 0),
    ("""<a  b="c >""", """<a  b="c >""", 0),
    ("""<a  b="" >""", """<a b="">""", 0),
    ("""<a  b='' >""", """<a b="">""", 0),
    ("""<a  b=>""", """<a b="">""", 0),
    ("""<a  b= >""", """<a b="">""", 0),
    ("""<a  =c>""", """<a c>""", 0),
    ("""<a  =c >""", """<a c>""", 0),
    ("""<a  =>""", """<a>""", 0),
    ("""<a  = >""", """<a>""", 0),
    ("""<a  b= "c" >""", """<a b="c">""", 0),
    ("""<a  b ="c" >""", """<a b="c">""", 0),
    ("""<a  b = "c" >""", """<a b="c">""", 0),
    ("""<a >""", """<a>""", 0),
    ("""< a>""", """<a>""", 0),
    ("""< a >""", """<a>""", 0),
    ("""<>""", """<>""", 0),
    ("""< >""", """< >""", 0),
    ("""<aä>""", """<a>""", 0),
    ("""<a aä="b">""", """<a a="b">""", 0),
    ("""<a a="bä">""", """<a a="bä">""", 0),
    # reduce test
    ("""<a  b="c"><""", """<a b="c"><""", 0),
    ("""d>""", """d>""", 0),
    # numbers in tag
    ("""<h1>bla</h1>""", """<h1>bla</h1>""", 0),
    # more start tags
    ("""<a  b=c"><a b="c">""", """<a b="c"><a b="c">""", 1),
    ("""<a  b=/c/></a><br>""", """<a b="/c/"></a><br>""", 0),
    ("""<br/>""", """<br>""", 0),
    ("""<a  b="50%"><br>""", """<a b="50%"><br>""", 0),
    # comments
    ("""<!---->< 1>""", """<!----><1>""", 0),
    ("""<!-- a - b -->< 2>""", """<!-- a - b --><2>""", 0),
    ("""<!----->< 3>""", """<!-----><3>""", 0),
    ("""<!------>< 4>""", """<!------><4>""", 0),
    ("""<!------->< 5>""", """<!-------><5>""", 0),
    ("""<!-- -->< 7>""", """<!-- --><7>""", 0),
    ("""<!---- />-->""", """<!---- />-->""", 0),
    ("""<!-- a-2 -->< 9>""", """<!-- a-2 --><9>""", 0),
    ("""<!-- --- -->< 10>""", """<!-- --- --><10>""", 0),
    # invalid comments
    ("""<!-- -- >< 8>""", """<!-- --><8>""", 1),
    ("""<!---- >< 6>""", """<!----><6>""", 1),
    ("""<!- blubb -->""", """<!-- blubb -->""", 1),
    ("""<!-- blubb ->""", """<!-- blubb -->""", 1),
    ("""<!- blubb ->""", """<!-- blubb -->""", 2),
    ("""<! -- blubb -->""", """<!-- blubb -->""", 1),
    ("""<!-- blubb -- >""", """<!-- blubb -->""", 1),
    # end tags
    ("""</a>""", """</a>""", 0),
    ("""</ a>""", """</a>""", 0),
    ("""</ a >""", """</a>""", 0),
    ("""</a >""", """</a>""", 0),
    ("""< / a>""", """</a>""", 0),
    ("""< /a>""", """</a>""", 0),
    ("""</aä>""", """</a>""", 0),
    # start and end tag (HTML doctype assumed)
    ("""<a/>""", """<a/>""", 0),
    ("""<meta/>""", """<meta>""", 0),
    ("""<MetA/>""", """<meta>""", 0),
    # declaration tags
    ("""<!DOCtype adrbook SYSTEM "adrbook.dtd">""",
     """<!DOCTYPE adrbook SYSTEM "adrbook.dtd">""", 0),
    # misc
    ("""<?xmL version="1.0" encoding="latin1"?>""",
     """<?xmL version="1.0" encoding="latin1"?>""", 0),
    # javascript
    ("""<script >\n</script>""", """<script>\n</script>""", 0),
    ("""<sCrIpt lang="a">bla </a> fasel</scripT>""",
     """<script lang="a">bla </a> fasel</script>""", 0),
    # line continuation (Dr. Fun webpage)
    ("<img bo\\\nrder=0 >", """<img border="0">""", 1),
    # href with $
    ("""<a href="123$456">""", """<a href="123$456">""", 0),
    # quoting
    ("""<a  href=/ >""", """<a href="/">""", 0),
    ("""<a  href= />""", """<a href="/">""", 0),
    ("""<a  href= >""", """<a href="">""", 0),
    ("""<a  href="'" >""", """<a href="'">""", 0),
    ("""<a  href='"' >""", """<a href="&quot;">""", 0),
    ("""<a  href="bla" %]" >""", """<a href="bla">""", 0),
    ("""<a  href=bla" >""", """<a href="bla">""", 1),
    ("""<a onmouseover=MM_swapImage('nav1','',"""\
     """'/images/dwnavpoint_over.gif',1);movein(this); b="c">""",
     """<a onmouseover="MM_swapImage('nav1','',"""\
     """'/images/dwnavpoint_over.gif',1);movein(this);" b="c">""", 0),
    ("""<a onClick=location.href('/index.htm') b="c">""",
     """<a onclick="location.href('/index.htm')" b="c">""", 0),
    # entity resolving
    ("""<a  href="&#109;ailto:" >""", """<a href="mailto:">""", 0),
    # non-ascii characters
    ("""<Üzgür> fahr </langsamer> ¹²³¼½¬{""",
     """<Üzgür> fahr </langsamer> ¹²³¼½¬{""", 0),
    # mailto link
    ("""<a  href=mailto:calvin@LocalHost?subject=Hallo&to=michi>1</a>""",
     """<a href="mailto:calvin@LocalHost?subject=Hallo&amp;to=michi">1</a>""", 0),
    # doctype XHTML
    ("""<!DOCTYPe html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><MeTa a="b"/>""",
     """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><meta a="b"/>""", 0),
    # missing > in end tag
    ("""</td <td  a="b" >""", """</td><td a="b">""", 1),
    ("""</td<td  a="b" >""", """</td><td a="b">""", 1),
    # missing beginning quote
    ("""<td a=b">""", """<td a="b">""", 1),
    # missing end quote (TODO)
    #("""<td a="b>""", """<td a="b">""", 1),
    #("""<td a="b></td>""", """<td a="b"></td>""", 1),
    #("""<td a="b c="d"></td>""", """<td a="b" c="d"></td>""", 1),
    #("""<a  b="c><a b="c">""", """<a b="c><a b=" c>""", 1),
]

flushtests = [
    ("<", "<", 0),
    ("<a", "<a", 0),
    ("<!a", "<!a", 0),
    ("<?a", "<?a", 0),
]


class TestParser (MsgTestCase):
    """
    Test html parser.
    """

    def setUp (self):
        """
        Initialize two internal html parsers to be used for testing.
        """
        self.htmlparser = linkcheck.HtmlParser.htmlsax.parser()
        self.htmlparser2 = linkcheck.HtmlParser.htmlsax.parser()

    def test_parse (self):
        """
        Parse all test patterns in one go.
        """
        for _in, _out, _errs in parsetests:
            out = StringIO.StringIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            self.htmlparser.feed(_in)
            self.check_results(self.htmlparser, _in, _out, _errs, out)

    def check_results (self, htmlparser, _in, _out, _errs, out):
        """
        Check parse results.
        """
        htmlparser.flush()
        res = out.getvalue()
        msg = "Test error; in: %r, out: %r, expect: %r" % \
           (_in, res, _out)
        self.assertEqual(res, _out, msg=msg)
        num = len(htmlparser.handler.errors)
        errors = ", ".join(htmlparser.handler.errors)
        msg = "Number of errors parsing %r: %d, expected: %d\nErrors: %s" % \
              (_in, num, _errs, errors)
        self.assertEqual(num, _errs, msg=msg)
        htmlparser.reset()

    def test_feed (self):
        """
        Parse all test patterns sequentially.
        """
        for _in, _out, _errs in parsetests:
            out = StringIO.StringIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            for c in _in:
                self.htmlparser.feed(c)
            self.check_results(self.htmlparser, _in, _out, _errs, out)

    def test_interwoven (self):
        """
        Parse all test patterns on two parsers interwoven.
        """
        for _in, _out, _errs in parsetests:
            out = StringIO.StringIO()
            out2 = StringIO.StringIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            handler2 = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out2)
            self.htmlparser2.handler = handler2
            for c in _in:
                self.htmlparser.feed(c)
                self.htmlparser2.feed(c)
            self.check_results(self.htmlparser, _in, _out, _errs, out)
            self.check_results(self.htmlparser2, _in, _out, _errs, out2)

    def test_flush (self):
        """
        Test parser flushing.
        """
        for _in, _out, _errs in flushtests:
            out = StringIO.StringIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            self.htmlparser.feed(_in)
            self.check_results(self.htmlparser, _in, _out, _errs, out)

    def test_entities (self):
        """
        Test entity resolving.
        """
        for c in "abcdefghijklmnopqrstuvwxyz":
            self.assertEqual(
                   linkcheck.HtmlParser.resolve_entities("&#%d;" % ord(c)), c)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestParser)


if __name__ == '__main__':
    unittest.main()
