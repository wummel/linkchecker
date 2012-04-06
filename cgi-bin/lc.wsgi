#!/usr/bin/python
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

from cStringIO import StringIO
import cgi
import linkcheck
import linkcheck.lc_cgi

def application(environ, start_response):
    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    # When the method is POST the query string will be sent
    # in the HTTP request body which is passed by the WSGI server
    # in the file like wsgi.input environment variable.
    request_body = environ['wsgi.input'].read(request_body_size)
    form = cgi.parse_qs(request_body)

    status = '200 OK'
    start_response(status, linkcheck.lc_cgi.get_response_headers())
    output = StringIO()
    # XXX this is slow since it checks the whole site before showing
    # any out.
    # Instead check in a separate thread and yield output as soon
    # as it is available.
    linkcheck.lc_cgi.checklink(form=form, out=output, env=environ)
    return [output.getvalue()]
