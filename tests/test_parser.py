# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2012 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Test html parsing.
"""

import linkcheck.HtmlParser.htmlsax
import linkcheck.HtmlParser.htmllib
from io import BytesIO
import unittest


# list of tuples
# (<test pattern>, <expected parse output>)
parsetests = [
    # start tags
    ("""<a  b="c" >""", b"""<a b="c">"""),
    ("""<a  b='c' >""", b"""<a b="c">"""),
    ("""<a  b=c" >""", b"""<a b="c">"""),
    ("""<a  b=c' >""", b"""<a b="c'">"""),
    ("""<a  b="c >""", b"""<a  b="c >"""),
    ("""<a  b="" >""", b"""<a b="">"""),
    ("""<a  b='' >""", b"""<a b="">"""),
    ("""<a  b=>""", b"""<a b="">"""),
    ("""<a  b= >""", b"""<a b="">"""),
    ("""<a  =c>""", b"""<a c>"""),
    ("""<a  =c >""", b"""<a c>"""),
    ("""<a  =>""", b"""<a>"""),
    ("""<a  = >""", b"""<a>"""),
    ("""<a  b= "c" >""", b"""<a b="c">"""),
    ("""<a  b ="c" >""", b"""<a b="c">"""),
    ("""<a  b = "c" >""", b"""<a b="c">"""),
    ("""<a >""", b"""<a>"""),
    ("""< a>""", b"""<a>"""),
    ("""< a >""", b"""<a>"""),
    ("""<>""", b"""<>"""),
    ("""< >""", b"""< >"""),
    ("""<a�>""", b"""<a>"""),
    ("""<a a�="b">""", b"""<a a="b">"""),
    (u"""<a a="b�">""", b"""<a a="b&#195;&#164;">"""),
    # multiple attribute names should be ignored...
    ("""<a b="c" b="c" >""", b"""<a b="c">"""),
    # ... but which one wins - in our implementation the last one
    ("""<a b="c" b="d" >""", b"""<a b="d">"""),
    # reduce test
    ("""<a  b="c"><""", b"""<a b="c"><"""),
    ("""d>""", b"""d>"""),
    # numbers in tag
    ("""<h1>bla</h1>""", b"""<h1>bla</h1>"""),
    # more start tags
    ("""<a  b=c"><a b="c">""", b"""<a b="c"><a b="c">"""),
    ("""<a  b=/c/></a><br>""", b"""<a b="/c/"></a><br>"""),
    ("""<br/>""", b"""<br>"""),
    ("""<a  b="50%"><br>""", b"""<a b="50%"><br>"""),
    # comments
    ("""<!---->< 1>""", b"""<!----><1>"""),
    ("""<!-- a - b -->< 2>""", b"""<!-- a - b --><2>"""),
    ("""<!----->< 3>""", b"""<!-----><3>"""),
    ("""<!------>< 4>""", b"""<!------><4>"""),
    ("""<!------->< 5>""", b"""<!-------><5>"""),
    ("""<!-- -->< 7>""", b"""<!-- --><7>"""),
    ("""<!---- />-->""", b"""<!---- />-->"""),
    ("""<!-- a-2 -->< 9>""", b"""<!-- a-2 --><9>"""),
    ("""<!-- --- -->< 10>""", b"""<!-- --- --><10>"""),
    ("""<!>""", b"""<!---->"""), # empty comment
    # invalid comments
    ("""<!-- -- >< 8>""", b"""<!-- --><8>"""),
    ("""<!---- >< 6>""", b"""<!----><6>"""),
    ("""<!- blubb ->""", b"""<!-- blubb -->"""),
    ("""<! -- blubb -->""", b"""<!-- blubb -->"""),
    ("""<!-- blubb -- >""", b"""<!-- blubb -->"""),
    ("""<! blubb !>< a>""", b"""<!--blubb !--><a>"""),
    ("""<! blubb >< a>""", b"""<!--blubb --><a>"""),
    # end tags
    ("""</a>""", b"""</a>"""),
    ("""</ a>""", b"""</a>"""),
    ("""</ a >""", b"""</a>"""),
    ("""</a >""", b"""</a>"""),
    ("""< / a>""", b"""</a>"""),
    ("""< /a>""", b"""</a>"""),
    ("""</a�>""", b"""</a>"""),
    # start and end tag (HTML doctype assumed)
    ("""<a/>""", b"""<a/>"""),
    ("""<meta/>""", b"""<meta>"""),
    ("""<MetA/>""", b"""<meta>"""),
    # declaration tags
    ("""<!DOCtype adrbook SYSTEM "adrbook.dtd">""",
     b"""<!DOCTYPE adrbook SYSTEM "adrbook.dtd">"""),
    # misc
    ("""<?xmL version="1.0" encoding="latin1"?>""",
     b"""<?xmL version="1.0" encoding="latin1"?>"""),
    # javascript
    ("""<script >\n</script>""", b"""<script>\n</script>"""),
    ("""<sCrIpt lang="a">bla </a> fasel</scripT>""",
     b"""<script lang="a">bla </a> fasel</script>"""),
    ("""<script ><!--bla//-->// </script >""",
     b"""<script><!--bla//-->// </script>"""),
    # line continuation (Dr. Fun webpage)
    ("""<img bo\\\nrder=0 >""", b"""<img border="0">"""),
    ("""<img align="mid\\\ndle">""", b"""<img align="middle">"""),
    ("""<img align='mid\\\ndle'>""", b"""<img align="middle">"""),
    # href with $
    ("""<a href="123$456">""", b"""<a href="123$456">"""),
    # quoting
    ("""<a  href=/ >""", b"""<a href="/">"""),
    ("""<a  href= />""", b"""<a href="/">"""),
    ("""<a  href= >""", b"""<a href="">"""),
    ("""<a  href="'" >""", b"""<a href="'">"""),
    ("""<a  href='"' >""", b"""<a href="&quot;">"""),
    ("""<a  href="bla" %]" >""", b"""<a href="bla">"""),
    ("""<a  href=bla" >""", b"""<a href="bla">"""),
    ("""<a onmouseover=blubb('nav1','',"""\
     """'/images/nav.gif',1);move(this); b="c">""",
     b"""<a onmouseover="blubb('nav1','',"""\
     b"""'/images/nav.gif',1);move(this);" b="c">"""),
    ("""<a onClick=location.href('/index.htm') b="c">""",
     b"""<a onclick="location.href('/index.htm')" b="c">"""),
    # entity resolving
    ("""<a  href="&#6D;ailto:" >""", b"""<a href="ailto:">"""),
    ("""<a  href="&amp;ailto:" >""", b"""<a href="&amp;ailto:">"""),
    ("""<a  href="&amp;amp;ailto:" >""", b"""<a href="&amp;amp;ailto:">"""),
    ("""<a  href="&hulla;ailto:" >""", b"""<a href="ailto:">"""),
    ("""<a  href="&#109;ailto:" >""", b"""<a href="mailto:">"""),
    ("""<a  href="&#x6D;ailto:" >""", b"""<a href="mailto:">"""),
    # note that \u8156 is not valid encoding and therefore gets removed
    ("""<a  href="&#8156;ailto:" >""", b"""<a href="ailto:">"""),
    # non-ascii characters
    ("""<Üzgür> fahr </langsamer> š˛łź˝Ź{""",
     """<Üzgür> fahr </langsamer> š˛łź˝Ź{"""),
    # mailto link
    ("""<a  href=mailto:calvin@LocalHost?subject=Hallo&to=michi>1</a>""",
     b"""<a href="mailto:calvin@LocalHost?subject=Hallo&amp;to=michi">1</a>"""),
    # doctype XHTML
    ("""<!DOCTYPe html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><MeTa a="b"/>""",
     b"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><meta a="b"/>"""),
    # meta tag with charset encoding
    ("""<meta http-equiv="content-type" content>""",
     b"""<meta http-equiv="content-type" content>"""),
    ("""<meta http-equiv="content-type" content=>""",
     b"""<meta http-equiv="content-type" content="">"""),
    ("""<meta http-equiv="content-type" content="hulla">""",
     b"""<meta http-equiv="content-type" content="hulla">"""),
    ("""<meta http-equiv="content-type" content="text/html; charset=iso8859-1">""",
     b"""<meta http-equiv="content-type" content="text/html; charset=iso8859-1">"""),
    ("""<meta http-equiv="content-type" content="text/html; charset=hulla">""",
     b"""<meta http-equiv="content-type" content="text/html; charset=hulla">"""),
    # CDATA
    ("""<![CDATA[<a>hallo</a>]]>""", b"""<![CDATA[<a>hallo</a>]]>"""),
    # missing > in end tag
    ("""</td <td  a="b" >""", b"""</td><td a="b">"""),
    ("""</td<td  a="b" >""", b"""</td><td a="b">"""),
    # missing beginning quote
    ("""<td a=b">""", b"""<td a="b">"""),
    # stray < before start tag
    ("""<0.<td  a="b" >""", b"""<0.<td a="b">"""),
    # stray < before end tag
    ("""<0.</td >""", b"""<0.</td>"""),
    # missing end quote (XXX TODO)
    #("""<td a="b>\n""", b"""<td a="b">\n"""),
    #("""<td a="b></td>\na""", b"""<td a="b"></td>\na"""),
    #("""<a  b="c><a b="c>\n""", b"""<a b="c"><a b="c">\n"""),
    #("""<td a="b c="d"></td>\n""", b"""<td a="b" c="d"></td>\n"""),
    # HTML5 tags
    ("""<audio  src=bla>""", b"""<audio src="bla">"""),
    ("""<button  formaction=bla>""", b"""<button formaction="bla">"""),
    ("""<html  manifest=bla>""", b"""<html manifest="bla">"""),
    ("""<source  src=bla>""", b"""<source src="bla">"""),
    ("""<track  src=bla>""", b"""<track src="bla">"""),
    ("""<video  src=bla>""", b"""<video src="bla">"""),
]

flushtests = [
    ("<", b"<"),
    ("<a", b"<a"),
    ("<!a", b"<!a"),
    ("<?a", b"<?a"),
]


class TestParser (unittest.TestCase):
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
        # Parse all test patterns in one go.
        for _in, _out in parsetests:
            out = BytesIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            self.htmlparser.feed(_in)
            self.check_results(self.htmlparser, _in, _out, out)

    def check_results (self, htmlparser, _in, _out, out):
        """
        Check parse results.
        """
        htmlparser.flush()
        res = out.getvalue()
        msg = "Test error; in: %r, out: %r, expect: %r" % \
           (_in, res, _out)
        self.assertEqual(res, _out, msg=msg)
        htmlparser.reset()

    def test_feed (self):
        # Parse all test patterns sequentially.
        for _in, _out in parsetests:
            out = BytesIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            for c in _in:
                self.htmlparser.feed(c)
            self.check_results(self.htmlparser, _in, _out, out)

    def test_interwoven (self):
        # Parse all test patterns on two parsers interwoven.
        for _in, _out in parsetests:
            out = BytesIO()
            out2 = BytesIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            handler2 = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out2)
            self.htmlparser2.handler = handler2
            for c in _in:
                self.htmlparser.feed(c)
                self.htmlparser2.feed(c)
            self.check_results(self.htmlparser, _in, _out, out)
            self.check_results(self.htmlparser2, _in, _out, out2)

    def test_handler (self):
        for _in, _out in parsetests:
            out = BytesIO()
            out2 = BytesIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrinter(out)
            self.htmlparser.handler = handler
            handler2 = linkcheck.HtmlParser.htmllib.HtmlPrinter(out2)
            self.htmlparser2.handler = handler2
            for c in _in:
                self.htmlparser.feed(c)
                self.htmlparser2.feed(c)
            self.assertEqual(out.getvalue(), out2.getvalue())

    def test_flush (self):
        # Test parser flushing.
        for _in, _out in flushtests:
            out = BytesIO()
            handler = linkcheck.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.handler = handler
            self.htmlparser.feed(_in)
            self.check_results(self.htmlparser, _in, _out, out)

    def test_entities (self):
        # Test entity resolving.
        resolve = linkcheck.HtmlParser.resolve_entities
        for c in "abcdefghijklmnopqrstuvwxyz":
            self.assertEqual(resolve("&#%d;" % ord(c)), c)
        self.assertEqual(resolve("&#1114112;"), u"")

    def test_peek (self):
        # Test peek() parser function
        data = '<a href="test.html">name</a>'

        class NamePeeker (object):

            def start_element (self_handler, tag, attrs):
                # use self reference of TestParser instance
                self.assertRaises(TypeError, self.htmlparser.peek, -1)
                self.assertEqual(self.htmlparser.peek(0), b"")
                self.assertEqual(self.htmlparser.peek(4), b"name")

        self.htmlparser.handler = NamePeeker()
        self.htmlparser.feed(data)

    def test_encoding_detection (self):
        html = '<meta http-equiv="content-type" content="text/html; charset=UTF-8">'
        self.encoding_test(html, b"utf-8")
        html = '<meta charset="UTF-8">'
        self.encoding_test(html, b"utf-8")
        html = '<meta charset="hulla">'
        self.encoding_test(html, b"iso8859-1")
        html = '<meta http-equiv="content-type" content="text/html; charset=blabla">'
        self.encoding_test(html, b"iso8859-1")

    def encoding_test (self, html, expected):
        parser = linkcheck.HtmlParser.htmlsax.parser()
        self.assertEqual(parser.encoding, b"iso8859-1")
        parser.feed(html)
        self.assertEqual(parser.encoding, expected)
