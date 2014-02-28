# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
    """Write URL data values into widget text fields."""
    if data.base_url and data.url:
        widget.prop_url.setText(u'<a href="%(url)s">%(base_url)s</a>' % \
                              dict(url=data.url, base_url=data.base_url))
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
    if data.size >= 0:
        widget.prop_size.setText(strformat.strsize(data.size))
    else:
        widget.prop_size.setText(u"")
    if data.modified:
        widget.prop_modified.setText(data.modified.isoformat(" "))
    else:
        widget.prop_modified.setText(u"")
    widget.prop_info.setText(wrap(data.info, 65))
    warning_msgs = [x[1] for x in data.warnings]
    widget.prop_warning.setText(wrap(warning_msgs, 65))
    if data.valid:
        result = u"Valid"
    else:
        result = u"Error"
    if data.result:
        result += u": %s" % data.result
    widget.prop_result.setText(result)


def clear_properties (widget):
    """Reset URL data values in widget text fields."""
    widget.prop_url.setText(u"")
    widget.prop_name.setText(u"")
    widget.prop_parenturl.setText(u"")
    widget.prop_base.setText(u"")
    widget.prop_checktime.setText(u"")
    widget.prop_dltime.setText(u"")
    widget.prop_size.setText(u"")
    widget.prop_info.setText(u"")
    widget.prop_warning.setText(u"")
    widget.prop_result.setText(u"")


def wrap (lines, width):
    """Format lines with given line-width."""
    sep = os.linesep+os.linesep
    text = sep.join(lines)
    kwargs = dict(break_long_words=False, break_on_hyphens=False)
    return strformat.wrap(text, width, **kwargs)
