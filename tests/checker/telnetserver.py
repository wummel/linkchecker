# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012 Bastian Kleineidam
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
import threading
import telnetlib
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "third_party", "miniboa-r42"))
import miniboa
from . import LinkCheckTest


TIMEOUT = 5

class TelnetServerTest (LinkCheckTest):
    """Start/stop a Telnet server that can be used for testing."""

    def __init__ (self, methodName='runTest'):
        """Init test class and store default ftp server port."""
        super(TelnetServerTest, self).__init__(methodName=methodName)
        self.host = 'localhost'
        self.port = None

    def get_url(self, user=None, password=None):
        if user is not None:
            if password is not None:
                netloc = u"%s:%s@%s" % (user, password, self.host)
            else:
                netloc = u"%s@%s" % (user, self.host)
        else:
            netloc = self.host
        return u"telnet://%s:%d" % (netloc, self.port)

    def setUp (self):
        """Start a new Telnet server in a new thread."""
        self.port = start_server(self.host, 0)
        self.assertFalse(self.port is None)

    def tearDown(self):
        """Send QUIT request to telnet server."""
        try:
            stop_server(self.host, self.port)
        except Exception:
            pass


def start_server (host, port):
    # Instantiate Telnet server class and listen to host:port
    clients = []
    def on_connect(client):
        clients.append(client)
        client.send("Telnet test server\n")
    server = miniboa.TelnetServer(port=port, host=host, on_connect=on_connect)
    port = server.server_socket.getsockname()[1]
    t = threading.Thread(None, serve_forever, args=(server, clients))
    t.start()
    # wait for server to start up
    tries = 0
    while tries < 5:
        tries += 1
        try:
            client = telnetlib.Telnet(timeout=TIMEOUT)
            client.open(host, port)
            client.write("exit\n")
            break
        except:
            time.sleep(0.5)
    return port


def stop_server (host, port):
    """Stop a running FTP server."""
    client = telnetlib.Telnet(timeout=TIMEOUT)
    client.open(host, port)
    client.write("stop\n")


def serve_forever(server, clients):
    """Run poll loop for server."""
    while True:
        server.poll()
        for client in clients:
            if client.active and client.cmd_ready:
                if not handle_cmd(client):
                    return

def handle_cmd(client):
    """Handle telnet clients."""
    msg = client.get_command().lower()
    if msg == 'exit':
        client.active = False
    elif msg == 'stop':
        return False
    return True
