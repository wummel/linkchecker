# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Define http test support classes for LinkChecker tests.
"""

import SimpleHTTPServer
import BaseHTTPServer
import httplib
import time
import threading
import cgi
import urllib
from cStringIO import StringIO
from . import LinkCheckTest


class StoppableHttpRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler, object):
    """
    HTTP request handler with QUIT stopping the server.
    """

    def do_QUIT (self):
        """
        Send 200 OK response, and set server.stop to True.
        """
        self.send_response(200)
        self.end_headers()
        self.server.stop = True

    def log_message (self, format, *args):
        """
        Logging is disabled.
        """
        pass

# serve .xhtml files as application/xhtml+xml
StoppableHttpRequestHandler.extensions_map.update({
        '.xhtml': 'application/xhtml+xml',
})


class StoppableHttpServer (BaseHTTPServer.HTTPServer, object):
    """
    HTTP server that reacts to self.stop flag.
    """

    def serve_forever (self):
        """
        Handle one request at a time until stopped.
        """
        self.stop = False
        while not self.stop:
            self.handle_request()


class NoQueryHttpRequestHandler (StoppableHttpRequestHandler):
    """
    Handler ignoring the query part of requests and sending dummy directory
    listings.
    """

    def remove_path_query (self):
        """
        Remove everything after a question mark.
        """
        i = self.path.find('?')
        if i != -1:
            self.path = self.path[:i]

    def get_status(self):
        dummy, status = self.path.rsplit('/', 1)
        status = int(status)
        if status in self.responses:
             return status
        return 500

    def do_GET (self):
        """
        Removes query part of GET request.
        """
        self.remove_path_query()
        if "status/" in self.path:
            status = self.get_status()
            self.send_response(status)
            self.end_headers()
            if  status >= 200 and status not in (204, 304):
                self.wfile.write("testcontent")
        else:
            super(NoQueryHttpRequestHandler, self).do_GET()

    def do_HEAD (self):
        """
        Removes query part of HEAD request.
        """
        self.remove_path_query()
        if "status/" in self.path:
            self.send_response(self.get_status())
            self.end_headers()
        else:
            super(NoQueryHttpRequestHandler, self).do_HEAD()

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Dummy directory listing</title>\n")
        f.write("<body>\n<h2>Dummy test directory listing</h2>\n")
        f.write("<hr>\n<ul>\n")
        list = ["example1.txt", "example2.html", "example3"]
        for name in list:
            displayname = linkname = name
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = "utf-8"
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f


class HttpServerTest (LinkCheckTest):
    """
    Start/stop an HTTP server that can be used for testing.
    """

    def __init__ (self, methodName='runTest'):
        """
        Init test class and store default http server port.
        """
        super(HttpServerTest, self).__init__(methodName=methodName)
        self.port = None
        self.handler = NoQueryHttpRequestHandler

    def setUp(self):
        """Start a new HTTP server in a new thread."""
        self.port = start_server(self.handler)
        assert self.port is not None

    def tearDown(self):
        """Send QUIT request to http server."""
        stop_server(self.port)

    def get_url(self, filename):
        """Get HTTP URL for filename."""
        return u"http://localhost:%d/tests/checker/data/%s" % (self.port, filename)



def start_server (handler):
    """Start an HTTP server thread and return its port number."""
    server_address = ('localhost', 0)
    handler.protocol_version = "HTTP/1.0"
    httpd = StoppableHttpServer(server_address, handler)
    port = httpd.server_port
    t = threading.Thread(None, httpd.serve_forever)
    t.start()
    # wait for server to start up
    while True:
        try:
            conn = httplib.HTTPConnection("localhost:%d" % port)
            conn.request("GET", "/")
            conn.getresponse()
            break
        except:
            time.sleep(0.5)
    return port


def stop_server (port):
    """Stop an HTTP server thread."""
    conn = httplib.HTTPConnection("localhost:%d" % port)
    conn.request("QUIT", "/")
    conn.getresponse()


def get_cookie (maxage=2000):
    data = (
        ("Comment", "justatest"),
        ("Max-Age", "%d" % maxage),
        ("Path", "/"),
        ("Version", "1"),
        ("Foo", "Bar"),
    )
    return "; ".join('%s="%s"' % (key, value) for key, value in data)


class CookieRedirectHttpRequestHandler (NoQueryHttpRequestHandler):
    """Handler redirecting certain requests, and setting cookies."""

    def end_headers (self):
        """Send cookie before ending headers."""
        self.send_header("Set-Cookie", get_cookie())
        self.send_header("Set-Cookie", get_cookie(maxage=0))
        super(CookieRedirectHttpRequestHandler, self).end_headers()

    def redirect (self):
        """Redirect request."""
        path = self.path.replace("redirect", "newurl")
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def redirect_newhost (self):
        """Redirect request to a new host."""
        path = "http://www.example.com/"
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def redirect_newscheme (self):
        """Redirect request to a new scheme."""
        if "file" in self.path:
            path = "file:README.md"
        else:
            path = "ftp://example.com/"
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET (self):
        """Handle redirections for GET."""
        if "redirect_newscheme" in self.path:
            self.redirect_newscheme()
        elif "redirect_newhost" in self.path:
            self.redirect_newhost()
        elif "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_GET()

    def do_HEAD (self):
        """Handle redirections for HEAD."""
        if "redirect_newscheme" in self.path:
            self.redirect_newscheme()
        elif "redirect_newhost" in self.path:
            self.redirect_newhost()
        elif "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_HEAD()
