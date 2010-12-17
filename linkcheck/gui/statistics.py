# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010 Bastian Kleineidam
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

from ..logger import ContentTypes

def set_statistics (widget, statistics):
    widget.stats_domains.setText(u"%d" % len(statistics.domains))
    widget.stats_url_minlen.setText(u"%d" % statistics.min_url_length)
    widget.stats_url_maxlen.setText(u"%d" % statistics.max_url_length)
    widget.stats_url_avglen.setText(u"%d" % statistics.avg_url_length)
    widget.stats_valid_urls.setText(u"%d" % (statistics.number - statistics.errors))
    widget.stats_invalid_urls.setText(u"%d" % statistics.errors)
    widget.stats_warnings.setText(u"%d" % statistics.warnings)
    for key, value in statistics.link_types.items():
        getattr(widget, "stats_content_%s"%key).setText(u"%d" % value)


def clear_statistics (widget):
    widget.stats_domains.setText(u"")
    widget.stats_url_minlen.setText(u"")
    widget.stats_url_maxlen.setText(u"")
    widget.stats_url_avglen.setText(u"")
    widget.stats_valid_urls.setText(u"")
    widget.stats_invalid_urls.setText(u"")
    widget.stats_warnings.setText(u"")
    for key in ContentTypes:
        getattr(widget, "stats_content_%s"%key).setText(u"")
