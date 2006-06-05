# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
An XML logger.
"""

import xmllog


class CustomXMLLogger (xmllog.XMLLogger):
    """
    XML custom output for easy post-processing.
    """

    def start_output (self):
        """
        Write start of checking info as xml comment.
        """
        super(CustomXMLLogger, self).start_output()
        self.xml_start_output()
        self.xml_starttag(u'linkchecker')
        self.flush()

    def log_url (self, url_data):
        """
        Log URL data in custom XML format.
        """
        self.xml_starttag(u'urldata')
        if self.has_part('url'):
            self.xml_tag(u"url", unicode(url_data.base_url or u""))
        if url_data.name and self.has_part('name'):
            self.xml_tag(u"name", unicode(url_data.name or u""))
        if url_data.parent_url and self.has_part('parenturl'):
            attrs = {
                u'line': u"%d" % url_data.line,
                u'column': u"%d" % url_data.column,
            }
            self.xml_tag(u"parent", unicode(url_data.parent_url or u""),
                         attrs=attrs)
        if url_data.base_ref and self.has_part('base'):
            self.xml_tag(u"baseref", unicode(url_data.base_ref))
        if self.has_part("realurl"):
            self.xml_tag(u"realurl", unicode(url_data.url))
        if self.has_part("extern"):
            self.xml_tag(u"extern", u"%d" % (url_data.extern[0] and 1 or 0))
        if url_data.dltime >= 0 and self.has_part("dltime"):
            self.xml_tag(u"dltime", u"%f" % url_data.dltime)
        if url_data.dlsize >= 0 and self.has_part("dlsize"):
            self.xml_tag(u"dlsize", u"%d" % url_data.dlsize)
        if url_data.checktime and self.has_part("checktime"):
            self.xml_tag(u"checktime", u"%f" % url_data.checktime)
        if url_data.info and self.has_part('info'):
            self.xml_starttag(u"infos")
            for tag, info in url_data.info:
                self.xml_tag(u"info", info)
            self.xml_endtag(u"infos")
        if url_data.warnings and self.has_part('warning'):
            self.xml_starttag(u"warnings")
            for tag, data in url_data.warnings:
                self.xml_tag(u"warning", data, attrs={u"tag": tag})
            self.xml_endtag(u"warnings")
        if self.has_part("result"):
            self.xml_tag(u"valid", u"%d" % (url_data.valid and 1 or 0))
        self.xml_endtag(u'urldata')
        self.flush()

    def end_output (self):
        """
        Write XML end tag.
        """
        self.xml_endtag(u"linkchecker")
        self.xml_end_output()
        self.close_fileoutput()
