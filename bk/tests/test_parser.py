# -*- coding: iso-8859-1 -*-

import bk.HtmlParser
import bk.HtmlParser.htmlsax
import bk.HtmlParser.htmllib
import cStringIO as StringIO
import unittest


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
    ("""<!---->""", """<!---->"""),
    ("""<!-- a - b -->< br>""", """<!-- a - b --><br>"""),
    ("""<!----->""", """<!----->"""),
    ("""<!------>""", """<!------>"""),
    ("""<!------->""", """<!------->"""),
    ("""<!---- >""", """<!----->"""),
    ("""<!-- -->""", """<!-- -->"""),
    ("""<!-- -- >""", """<!-- --->"""),
    ("""<!---- />-->""", """<!---- />-->"""),
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
    ("""<!DOCtype adrbook SYSTEM "adrbook.dtd">""", """<!DOCTYPE adrbook SYSTEM "adrbook.dtd">"""),
    # misc
    ("""<?xmL version="1.0" encoding="latin1"?>""", """<?xmL version="1.0" encoding="latin1"?>"""),
    # javascript
    ("""<script >\n</script>""", """<script>\n</script>"""),
    ("""<sCrIpt lang="a">bla </a> fasel</scripT>""", """<script lang="a">bla </a> fasel</script>"""),
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
    ("""<a onmouseover=MM_swapImage('nav1','','/images/dwnavpoint_over.gif',1);movein(this); b="c">""",
     """<a onmouseover="MM_swapImage('nav1','','/images/dwnavpoint_over.gif',1);movein(this);" b="c">"""),
    ("""<a onClick=location.href('/index.htm') b="c">""",
     """<a onclick="location.href('/index.htm')" b="c">"""),
    # entities
    ("""<a  href="&#109;ailto:" >""", """<a href="mailto:">"""),
    # non-ascii characters
    ("""<Üzgür> fahr </langsamer> ¹²³¼½¬{""",
     """<Üzgür> fahr </langsamer> ¹²³¼½¬{"""),
]

flushtests = [
    ("<", "<"),
    ("<a", "<a"),
    ("<!a", "<!a"),
    ("<?a", "<?a"),
]


class TestParser (unittest.TestCase):

    def setUp (self):
        # list of tuples (<test pattern>, <expected parse output>)
        self.htmlparser = bk.HtmlParser.htmlsax.parser()
        self.htmlparser2 = bk.HtmlParser.htmlsax.parser()

    def test_parse (self):
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            self.htmlparser.handler = bk.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.feed(_in)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_feed (self):
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            self.htmlparser.handler = bk.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            for c in _in:
                self.htmlparser.feed(c)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_interwoven (self):
        for _in, _out in parsetests:
            out = StringIO.StringIO()
            out2 = StringIO.StringIO()
            self.htmlparser.handler = bk.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser2.handler = bk.HtmlParser.htmllib.HtmlPrettyPrinter(out2)
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
        for _in, _out in flushtests:
            out = StringIO.StringIO()
            self.htmlparser.handler = bk.HtmlParser.htmllib.HtmlPrettyPrinter(out)
            self.htmlparser.feed(_in)
            self.htmlparser.flush()
            res = out.getvalue()
            self.assertEqual(res, _out)
            self.htmlparser.reset()

    def test_entities (self):
        for c in "abcdefghijklmnopqrstuvwxyz":
            self.assertEqual(bk.HtmlParser.resolve_entities("&#%d;"%ord(c)), c)


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestParser))
    return suite

if __name__ == '__main__':
    unittest.main()

