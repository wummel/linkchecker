# -*- coding: iso-8859-1 -*-
import unittest
import bk.url


class TestUrl (unittest.TestCase):

    def test_pathattack (self):
        url = "http://server/..%5c..%5c..%5c..%5c..%5c..%5..%5c..%5ccskin.zip"
        nurl = "http://server/cskin.zip"
        self.assertEquals(bk.url.url_quote(bk.url.url_norm(url)), nurl)

    def test_quoting (self):
        url = "http://groups.google.com/groups?hl=en&lr=&ie=UTF-8&threadm=3845B54D.E546F9BD%40monmouth.com&rnum=2&prev=/groups%3Fq%3Dlogitech%2Bwingman%2Bextreme%2Bdigital%2B3d%26hl%3Den%26lr%3D%26ie%3DUTF-8%26selm%3D3845B54D.E546F9BD%2540monmouth.com%26rnum%3D2"
        nurl = url
        self.assertEqual(bk.url.url_quote(bk.url.url_norm(url)), nurl)

    def test_fixing (self):
        url = r"http://groups.google.com\test.html"
        nurl = "http://groups.google.com/test.html"
        self.assertEqual(bk.url.url_norm(url), nurl)
        url = r"http://groups.google.com/a\test.html"
        nurl = "http://groups.google.com/a/test.html"
        self.assertEqual(bk.url.url_norm(url), nurl)
        url = r"http://groups.google.com\a\test.html"
        nurl = "http://groups.google.com/a/test.html"
        self.assertEqual(bk.url.url_norm(url), nurl)
        url = r"http://groups.google.com\a/test.html"
        nurl = "http://groups.google.com/a/test.html"
        self.assertEqual(bk.url.url_norm(url), nurl)
        url = "http://groups.google.com//a/test.html"
        nurl = "http://groups.google.com/a/test.html"
        self.assertEqual(bk.url.url_norm(url), nurl)
        url = "http://groups.google.com//a/b/"
        nurl = "http://groups.google.com/a/b/"
        self.assertEqual(bk.url.url_norm(url), nurl)

    def test_valid (self):
        self.assert_(bk.url.is_valid_url("http://www.imadoofus.com"))
        self.assert_(bk.url.is_valid_url("http://www.imadoofus.com/"))
        self.assert_(bk.url.is_valid_url("http://www.imadoofus.com/~calvin"))
        self.assert_(bk.url.is_valid_url("http://www.imadoofus.com/a,b"))
        self.assert_(bk.url.is_valid_url("http://www.imadoofus.com#anchor55"))
        self.assert_(bk.url.is_valid_js_url("http://www.imadoofus.com/?hulla=do"))


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUrl))
    return suite

if __name__ == '__main__':
    unittest.main()

