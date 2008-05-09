# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
"""
A dummy logger.
"""
from . import Logger


class NoneLogger (Logger):
    """
    Dummy logger printing nothing.
    """

    def comment (self, s, **args):
        """
        Do nothing.
        """
        pass

    def start_output (self):
        """
        Do nothing.
        """
        pass

    def log_filter_url (self, url_data, do_filter):
        """
        Do nothing.
        """
        pass

    def end_output (self):
        """
        Do nothing.
        """
        pass
