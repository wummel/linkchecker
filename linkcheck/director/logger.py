# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2007 Bastian Kleineidam
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
"""Logger for aggregator instances"""
import threading
from linkcheck.decorators import synchronized

_lock = threading.Lock()


class Logger (object):
    """
    Thread safe multi-logger class used by aggregator instances.
    """

    def __init__ (self, config):
        self.logs = [config['logger']]
        self.logs.extend(config['fileoutput'])
        self.ignorewarnings = config["ignorewarnings"]
        self.verbose = config["verbose"]
        self.warnings = config["warnings"]

    def start_log_output (self):
        """
        Start output of all configured loggers.
        """
        for logger in self.logs:
            logger.start_output()

    def end_log_output (self):
        """
        End output of all configured loggers.
        """
        for logger in self.logs:
            logger.end_output()

    @synchronized(_lock)
    def log_url (self, url_data):
        """
        Send new url to all configured loggers.
        """
        has_warnings = False
        for tag, content in url_data.warnings:
            if tag not in self.ignorewarnings:
                has_warnings = True
                break
        do_print = self.verbose or not url_data.valid or \
            (has_warnings and self.warnings)
        for log in self.logs:
            log.log_filter_url(url_data, do_print)
