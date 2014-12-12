# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
Check page content with regular expression for links.
"""
import re
from . import _ContentPlugin
from .. import log, LOG_PLUGIN


class RegexLinkCheck(_ContentPlugin):
    """Define a regular expression which matches any content.
    It will treat matched content as a url and check it. 
    This applies only to valid pages, so we can get their content.

    Use this to check for pages that contain urls that cannot 
    be found using the built-in tag finding, 
    for example if there are urls defined in a json object.

    Note that multiple values can be combined in the regular expression"."""

    def __init__(self, config):
        """Set link regex from config."""
        super(RegexLinkCheck, self).__init__(config)
        self.linkregex = None
        pattern = config["linkregex"]
        if pattern:
            try:
                self.linkregex = re.compile(pattern)
            except re.error as msg:
                log.warn(LOG_PLUGIN, "Invalid regex pattern %r: %s" % (pattern, msg))

    def applies_to(self, url_data):
        """Check for linkregex, extern flag and parseability."""
        return self.linkregex and not url_data.extern[0] and url_data.is_parseable()

    def check(self, url_data):
        """Check content."""
        log.debug(LOG_PLUGIN, "checking content for link regex")
        content = url_data.get_content()
        # add urls for found matches, up to the maximum allowed number
        match = self.linkregex.search(content)
        if match:
            url_data.add_url(match.group(1))

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        section = cls.__name__
        option = "linkregex"
        if configparser.has_option(section, option):
            value = configparser.get(section, option)
        else:
            value = None
        config[option] = value
        return config
