# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2014 Bastian Kleineidam
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

from logging import Handler
from ..logger import _Logger


class GuiLogHandler (Handler, object):
    """Delegate log messages to the UI."""

    def __init__ (self, signal):
        """Save widget."""
        super(GuiLogHandler, self).__init__()
        self.signal = signal

    def emit (self, record):
        """Emit a record. It gets logged in the debug widget."""
        self.signal.emit(self.format(record))


class SignalLogger (_Logger):
    """Use Qt signals for logged URLs and statistics."""

    LoggerName = "gui"

    def __init__ (self, **args):
        """Store signals for URL and statistic data."""
        super(SignalLogger, self).__init__(**args)
        self.log_url_signal = args["signal"]
        self.log_stats_signal = args["stats"]

    def start_fileoutput (self):
        """Override fileoutput handling of base class."""
        pass

    def close_fileoutput (self):
        """Override fileoutput handling of base class."""
        pass

    def log_url (self, url_data):
        """Emit URL data which gets logged in the main window."""
        self.log_url_signal.emit(url_data)

    def end_output (self, downloaded_bytes=None, num_urls=None):
        """Emit statistic data which gets logged in the main window."""
        self.stats.downloaded_bytes = downloaded_bytes
        self.log_stats_signal.emit(self.stats)


class StatusLogger (object):
    """GUI status logger, signaling to progress labels."""

    def __init__ (self, signal):
        """Store given signal object."""
        self.signal = signal

    def log_status (self, checked, in_progress, queued, duration, num_urls):
        """Emit signal with given status information."""
        self.signal.emit(checked, in_progress, queued, duration, num_urls)
