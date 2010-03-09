# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010 Bastian Kleineidam
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
import sys
import os
import time
from . import LinkCheckTest


class FtpServerTest (LinkCheckTest):
    """Start/stop an FTP server that can be used for testing."""

    def __init__ (self, methodName='runTest'):
        """Init test class and store default ftp server port."""
        super(FtpServerTest, self).__init__(methodName=methodName)
        self.host = '127.0.0.1'
        self.port = 8888

    def start_server (self):
        """Start a new FTP server in a new thread."""
        try:
            import threading
        except ImportError:
            self.fail("This test needs threading support")
        t = threading.Thread(None, start_server, None, (self.host, self.port))
        t.start()
        # wait for server to start up
        time.sleep(3)

    def stop_server (self):
        """Send QUIT request to http server."""
        from ftplib import FTP
        ftp = FTP()
        ftp.connect(self.host, self.port)
        ftp.login()
        try:
            ftp.sendcmd("kill")
        except EOFError:
            pass
        ftp.close()


def start_server (host, port):
    def line_logger(msg):
        if "kill" in msg:
            sys.exit(0)

    from pyftpdlib import ftpserver
    authorizer = ftpserver.DummyAuthorizer()
    datadir = os.path.join(os.path.dirname(__file__), 'data')
    authorizer.add_anonymous(datadir)

    # Instantiate FTP handler class
    ftp_handler = ftpserver.FTPHandler
    ftp_handler.authorizer = authorizer
    ftpserver.logline = line_logger

    # Define a customized banner (string returned when client connects)
    ftp_handler.banner = "pyftpdlib %s based ftpd ready." % ftpserver.__ver__

    # Instantiate FTP server class and listen to host:port
    address = (host, port)
    server = ftpserver.FTPServer(address, ftp_handler)
    print 'FTP server started on port %d...' % port
    server.serve_forever()
