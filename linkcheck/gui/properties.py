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
import sys
from PyQt4 import QtGui
from .linkchecker_ui_properties import Ui_PropertiesDialog
from .. import strformat


class PropertiesDialog (QtGui.QDialog, Ui_PropertiesDialog):
    """Show URL properties dialog."""

    def __init__ (self, parent=None):
        super(PropertiesDialog, self).__init__(parent)
        self.setupUi(self)
        self.okButton.clicked.connect(self.close)

    def set_item (self, urlitem):
        """Write URL item values into text fields."""
        data = urlitem.url_data
        self.prop_id.setText(u"%d" % urlitem.number)
        if data.url:
            self.prop_url.setText(u'<a href="%(url)s">%(url)s</a>' % \
                                  dict(url=data.url))
        else:
            self.prop_url.setText(u"")
        self.prop_name.setText(data.name)
        if data.parent_url:
            self.prop_parenturl.setText(u'<a href="%(url)s">%(url)s</a>' % \
                                  dict(url=data.parent_url))
        else:
            self.prop_parenturl.setText(u"")
        self.prop_base.setText(data.base_ref)
        self.prop_checktime.setText(_("%.3f seconds") % data.checktime)
        if data.dltime >= 0:
            self.prop_dltime.setText(_("%.3f seconds") % data.dltime)
        else:
            self.prop_dltime.setText(u"")
        if data.dlsize >= 0:
            self.prop_size.setText(strformat.strsize(data.dlsize))
        else:
            self.prop_size.setText(u"")
        self.prop_info.setText(wrap(data.info, 65))
        self.prop_warning.setText(wrap(data.warnings, 65))
        if data.valid:
            result = u"Valid"
        else:
            result = u"Error"
        if data.result:
            result += u": %s" % data.result
        self.prop_result.setText(result)


def wrap (lines, width):
    sep = os.linesep+os.linesep
    text = sep.join(lines)
    kwargs = dict(break_long_words=False)
    if sys.version_info >= (2, 6, 0, 'final', 0):
        kwargs["break_on_hyphens"] = False
    return strformat.wrap(text, width, **kwargs)
