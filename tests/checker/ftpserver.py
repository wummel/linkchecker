# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
import os
import time
import threading
import pytest
from ftplib import FTP
from . import LinkCheckTest


TIMEOUT = 5

class FtpServerTest (LinkCheckTest):
    """Start/stop an FTP server that can be used for testing."""

    def __init__ (self, methodName='runTest'):
        """Init test class and store default ftp server port."""
        super(FtpServerTest, self).__init__(methodName=methodName)
        self.host = 'localhost'
        self.port = None

    def setUp (self):
        """Start a new FTP server in a new thread."""
        self.port = start_server(self.host, 0)
        self.assertFalse(self.port is None)

    def tearDown (self):
        """Send stop request to server."""
        try:
            stop_server(self.host, self.port)
        except Exception:
            pass


def start_server (host, port):
    def line_logger(msg):
        if "kill" in msg:
            raise KeyboardInterrupt()

    try:
        from pyftpdlib import ftpserver
    except ImportError:
        pytest.skip("pyftpdlib is not available")
        return
    authorizer = ftpserver.DummyAuthorizer()
    datadir = os.path.join(os.path.dirname(__file__), 'data')
    authorizer.add_anonymous(datadir)

    # Instantiate FTP handler class
    ftp_handler = ftpserver.FTPHandler
    ftp_handler.authorizer = authorizer
    ftp_handler.timeout = TIMEOUT
    ftpserver.logline = line_logger

    # Define a customized banner (string returned when client connects)
    ftp_handler.banner = "pyftpdlib %s based ftpd ready." % ftpserver.__ver__

    # Instantiate FTP server class and listen to host:port
    address = (host, port)
    server = ftpserver.FTPServer(address, ftp_handler)
    port = server.address[1]
    t = threading.Thread(None, server.serve_forever)
    t.start()
    # wait for server to start up
    tries = 0
    while tries < 5:
        tries += 1
        try:
            ftp = FTP()
            ftp.connect(host, port, TIMEOUT)
            ftp.login()
            ftp.close()
            break
        except:
            time.sleep(0.5)
    return port


def stop_server (host, port):
    """Stop a running FTP server."""
    ftp = FTP()
    ftp.connect(host, port, TIMEOUT)
    ftp.login()
    try:
        ftp.sendcmd("kill")
    except EOFError:
        pass
    ftp.close()
