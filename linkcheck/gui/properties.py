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

import os
from .. import strformat


def set_properties (widget, data):
    """Write URL data values into text fields."""
    if data.url:
        widget.prop_url.setText(u'<a href="%(url)s">%(url)s</a>' % \
                              dict(url=data.url))
    else:
        widget.prop_url.setText(u"")
    widget.prop_name.setText(data.name)
    if data.parent_url:
        widget.prop_parenturl.setText(u'<a href="%(url)s">%(url)s</a>' % \
                              dict(url=data.parent_url))
    else:
        widget.prop_parenturl.setText(u"")
    widget.prop_base.setText(data.base_ref)
    widget.prop_checktime.setText(_("%.3f seconds") % data.checktime)
    if data.dltime >= 0:
        widget.prop_dltime.setText(_("%.3f seconds") % data.dltime)
    else:
        widget.prop_dltime.setText(u"")
    if data.dlsize >= 0:
        widget.prop_size.setText(strformat.strsize(data.dlsize))
    else:
        widget.prop_size.setText(u"")
    widget.prop_info.setText(wrap(data.info, 65))
    widget.prop_warning.setText(wrap(data.warnings, 65))
    if data.valid:
        result = u"Valid"
    else:
        result = u"Error"
    if data.result:
        result += u": %s" % data.result
    widget.prop_result.setText(result)


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


def wrap (lines, width):
    sep = os.linesep+os.linesep
    text = sep.join(lines)
    kwargs = dict(break_long_words=False, break_on_hyphens=False)
    return strformat.wrap(text, width, **kwargs)
