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
Check page content with regular expression.
"""
import re
from . import _ContentPlugin
from .. import log, LOG_PLUGIN


class RegexCheck(_ContentPlugin):
    """Define a regular expression which prints a warning if it matches
    any content of the checked link. This applies only to valid pages,
    so we can get their content.

    Use this to check for pages that contain some form of error
    message, for example 'This page has moved' or 'Oracle
    Application error'.

    Note that multiple values can be combined in the regular expression,
    for example "(This page has moved|Oracle Application error)"."""

    def __init__(self, config):
        """Set warning regex from config."""
        super(RegexCheck, self).__init__(config)
        self.warningregex = None
        pattern = config["warningregex"]
        if pattern:
            try:
                self.warningregex = re.compile(pattern)
            except re.error as msg:
                log.warn(LOG_PLUGIN, "Invalid regex pattern %r: %s" % (pattern, msg))

    def applies_to(self, url_data):
        """Check for warningregex, extern flag and parseability."""
        return self.warningregex and not url_data.extern[0] and url_data.is_parseable()

    def check(self, url_data):
        """Check content."""
        log.debug(LOG_PLUGIN, "checking content for warning regex")
        content = url_data.get_content()
        # add warnings for found matches, up to the maximum allowed number
        match = self.warningregex.search(content)
        if match:
            # calculate line number for match
            line = content.count('\n', 0, match.start())
            # add a warning message
            msg = _("Found %(match)r at line %(line)d in link contents.")
            url_data.add_warning(msg % {"match": match.group(), "line": line})

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        section = cls.__name__
        option = "warningregex"
        if configparser.has_option(section, option):
            value = configparser.get(section, option)
        else:
            value = None
        config[option] = value
        return config
