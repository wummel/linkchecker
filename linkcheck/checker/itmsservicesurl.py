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
Handle itms-services URLs.
"""

from . import urlbase
from .. import log, LOG_CHECK


class ItmsServicesUrl(urlbase.UrlBase):
    """Apple iOS application download URLs."""

    def check_syntax(self):
        """Only logs that this URL is unknown."""
        super(ItmsServicesUrl, self).check_syntax()
        if u"url=" not in self.urlparts[3]:
            self.set_result(_("Missing required url parameter"), valid=False)

    def local_check(self):
        """Disable content checks."""
        log.debug(LOG_CHECK, "Checking %s", unicode(self))
        pass

    def check_content(self):
        """Allow recursion to check the url CGI param."""
        return True

    def is_parseable(self):
        """This URL is parseable."""
        return True
