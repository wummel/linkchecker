# -*- coding: iso-8859-1 -*-
"""define http test support classes for LinkChecker tests"""
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

import SimpleHTTPServer
import BaseHTTPServer
import httplib
import time

import linkcheck.ftests


class HttpServerTest (linkcheck.ftests.StandardTest):
    """start/stop an HTTP server that can be used for testing"""

    def __init__ (self, methodName='runTest'):
        """init test class and store default http server port"""
        super(HttpServerTest, self).__init__(methodName=methodName)
        self.port = 8001

    def start_server (self):
        """start a new HTTP server in a new thread"""
        try:
            import threading
        except ImportError:
            self.fail("This test needs threading support")
        t = threading.Thread(None, start_server, None, (self.port,))
        t.start()
        # wait for server to start up
        time.sleep(3)

    def stop_server (self):
        """send QUIT request to http server"""
        conn = httplib.HTTPConnection("localhost:%d"%self.port)
        conn.request("QUIT", "/")
        conn.getresponse()


class StoppableHttpRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
    """http request handler with QUIT stopping the server"""

    def do_QUIT (self):
        """send 200 OK response, and set server.stop to True"""
        self.send_response(200)
        self.end_headers()
        self.server.stop = True

    def log_message (self, format, *args):
        """logging is disabled"""
        pass


class StoppableHttpServer (BaseHTTPServer.HTTPServer):
    """http server that reacts to self.stop flag"""

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        self.stop = False
        while not self.stop:
            self.handle_request()


def start_server (port):
    """start an HTTP server on given port"""
    HandlerClass = StoppableHttpRequestHandler
    ServerClass = StoppableHttpServer
    server_address = ('', port)
    HandlerClass.protocol_version = "HTTP/1.0"
    httpd = ServerClass(server_address, HandlerClass)
    httpd.serve_forever()
