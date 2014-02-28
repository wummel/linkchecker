# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011-2014 Bastian Kleineidam
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

from PyQt4 import QtCore, QtGui


def format (color, style=''):
    """Return a QTextCharFormat with the given attributes."""
    format = QtGui.QTextCharFormat()
    format.setForeground(getattr(QtCore.Qt, color))
    if 'bold' in style:
        format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        format.setFontItalic(True)
    return format


class Highlighter (QtGui.QSyntaxHighlighter):
    """Base class for all highlighters."""

    def __init__ (self, document):
        """Initialize rules and styles."""
        super(Highlighter, self).__init__(document)
        self.rules = []
        self.styles = {}

    def highlightBlock(self, text):
        """Highlight a text block."""
        for expression, format in self.rules:
            # get first match
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                # jump to next match
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)

    def addRule (self, pattern, style):
        """Add a rule pattern with given style."""
        self.rules.append((QtCore.QRegExp(pattern), self.styles[style]))


class XmlHighlighter (Highlighter):
    """XML syntax highlighter."""

    def __init__(self, document):
        """Set XML syntax rules."""
        super(XmlHighlighter, self).__init__(document)
        self.styles.update({
            'keyword': format('darkBlue'),
            'attribute': format('darkGreen'),
            'comment': format('darkYellow'),
            'string': format('darkMagenta'),
        })
        # keywords
        for reg in ('/>', '>', '<!?[a-zA-Z0-9_]+'):
            self.addRule(reg, 'keyword')
        # attributes
        self.addRule(r"\b[A-Za-z0-9_]+(?=\s*\=)", 'attribute')
        # double-quoted string, possibly containing escape sequences
        self.addRule(r'"[^"\\]*(\\.[^"\\]*)*"', 'string')
        # single-quoted string, possibly containing escape sequences
        self.addRule(r"'[^'\\]*(\\.[^'\\]*)*'", 'string')
        # comments
        self.addRule(r"<!--[^>]*-->", 'comment')

# Treat HTML as XML
HtmlHighlighter = XmlHighlighter

class IniHighlighter (Highlighter):
    """INI syntax highlighter."""

    def __init__(self, document):
        """Set INI syntax rules."""
        super(IniHighlighter, self).__init__(document)
        self.styles.update({
            'section': format('darkBlue'),
            'property': format('darkGreen'),
            'comment': format('darkYellow'),
        })
        self.addRule(r'\b\[[a-zA-Z0-9_]+\]\b', 'section')
        self.addRule(r'\b[a-zA-Z0-9_]+\](?=\s*\=)', 'property')
        self.addRule(r'#[^\n]*', 'comment')
