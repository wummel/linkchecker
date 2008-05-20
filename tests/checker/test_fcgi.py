# -*- coding: iso-8859-1 -*-
"""
Test container routines.
"""

import unittest
import os

import linkcheck.fcgi

class TestFcgi (unittest.TestCase):
    """
    Test FastCGI request parsing routines.
    """

    def _test_non_fcgi_env (self):
        os.environ = {}
        req = linkcheck.fcgi.FCGI()
        fs = req.getFieldStorage()
        doc = ['<HTML><HEAD><TITLE>FCGI TestApp</TITLE></HEAD>\n'
               '<BODY>\n']
        doc.append('<H2>FCGI TestApp</H2><P>')
        if 'CONTENT_LENGTH' in req.env:
            cl = int(req.env['CONTENT_LENGTH'])
            doc.append('<br><b>POST data (%s):</b><br><pre>' % cl)
            keys = fs.keys()
            keys.sort()
            for k in keys:
                val = fs[k]
                if type(val) == type([]):
                    doc.append('    <b>%-15s :</b>  %s\n' %
                               (k, val))
                else:
                    doc.append('    <b>%-15s :</b>  %s\n' %
                               (k, val.value))
            doc.append('</pre>')
        doc.append('<P><HR><P><pre>')
        keys = req.env.keys()
        keys.sort()
        for k in keys:
            doc.append('<b>%-20s :</b>  %s\n' % (k, req.env[k]))
        doc.append('\n</pre><P><HR>\n')
        doc.append('</BODY></HTML>\n')
        doc = ''.join(doc)
        req.out.write('Content-length: %s\r\n'
                      'Content-type: text/html\r\n'
                      'Cache-Control: no-cache\r\n'
                      '\r\n'
                          % len(doc))
        req.out.write(doc)
        req.finish()

    def _test_fcgi (self):
        """
        Test FastCGI request parsing routines.
        """
        counter = 0
        while linkcheck.fcgi.isFCGI():
            req = linkcheck.fcgi.FCGI()
            counter += 1
            fs = req.getFieldStorage()
            size = int(fs['size'].value)
            doc = ['*' * size]
            doc = ''.join(doc)
            req.out.write('Content-length: %s\r\n'
                        'Content-type: text/html\r\n'
                        'Cache-Control: no-cache\r\n'
                        '\r\n'
                            % len(doc))
            req.out.write(doc)
            req.finish()


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestFcgi)


if __name__ == '__main__':
    unittest.main()
