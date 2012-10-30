#!/usr/bin/env python
#------------------------------------------------------------------------------
#   hello_demo.py
#   Copyright 2009 Jim Storch
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain a
#   copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#------------------------------------------------------------------------------

"""
As simple as it gets.

Launch the Telnet server on the default port and greet visitors using the
placeholder 'on_connect()' function.  Does nothing else.
"""

from miniboa import TelnetServer

server = TelnetServer()
print "\n\nStarting server on port %d.  CTRL-C to interrupt.\n" % server.port
while True:
    server.poll()
