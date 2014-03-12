# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
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
Add HTTP server name information
"""
from . import _ConnectionPlugin


class HttpHeaderInfo(_ConnectionPlugin):
    """Add HTTP header info for each URL"""

    def __init__(self, config):
        """Initialize configuration."""
        super(HttpHeaderInfo, self).__init__(config)
        self.prefixes = tuple(config["prefixes"])

    def check(self, url_data):
        """Check content for invalid anchors."""
        if not url_data.is_http():
            # not an HTTP URL
            return
        if not self.prefixes:
            return
        headers = []
        for name, value in url_data.headers.items():
            if name.startswith(self.prefixes):
                headers.append(name)
        if headers:
            items = [u"%s=%s" % (name.capitalize(), url_data.headers[name]) for name in headers]
            info = u"HTTP headers %s" % u", ".join(items)
            url_data.add_info(info)

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        section = cls.__name__
        option = "prefixes"
        if configparser.has_option(section, option):
            value = configparser.get(section, option)
            names = [x.strip().lower() for x in value.split(",")]
        else:
            names = []
        config[option] = names
        return config

