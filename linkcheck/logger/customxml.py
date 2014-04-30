# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
An XML logger.
"""
from . import xmllog
from .. import strformat


class CustomXMLLogger (xmllog._XMLLogger):
    """
    XML custom output for easy post-processing.
    """

    LoggerName = "xml"

    LoggerArgs = {
        "filename": "linkchecker-out.xml",
    }

    def start_output (self):
        """
        Write start of checking info as xml comment.
        """
        super(CustomXMLLogger, self).start_output()
        self.xml_start_output()
        attrs = {"created": strformat.strtime(self.starttime)}
        self.xml_starttag(u'linkchecker', attrs)
        self.flush()

    def log_url (self, url_data):
        """
        Log URL data in custom XML format.
        """
        self.xml_starttag(u'urldata')
        if self.has_part('url'):
            self.xml_tag(u"url", unicode(url_data.base_url))
        if url_data.name and self.has_part('name'):
            self.xml_tag(u"name", unicode(url_data.name))
        if url_data.parent_url and self.has_part('parenturl'):
            attrs = {
                u'line': u"%d" % url_data.line,
                u'column': u"%d" % url_data.column,
            }
            self.xml_tag(u"parent", unicode(url_data.parent_url),
                         attrs=attrs)
        if url_data.base_ref and self.has_part('base'):
            self.xml_tag(u"baseref", unicode(url_data.base_ref))
        if self.has_part("realurl"):
            self.xml_tag(u"realurl", unicode(url_data.url))
        if self.has_part("extern"):
            self.xml_tag(u"extern", u"%d" % (1 if url_data.extern else 0))
        if url_data.dltime >= 0 and self.has_part("dltime"):
            self.xml_tag(u"dltime", u"%f" % url_data.dltime)
        if url_data.size >= 0 and self.has_part("dlsize"):
            self.xml_tag(u"dlsize", u"%d" % url_data.size)
        if url_data.checktime and self.has_part("checktime"):
            self.xml_tag(u"checktime", u"%f" % url_data.checktime)
        if self.has_part("level"):
            self.xml_tag(u"level", u"%d" % url_data.level)
        if url_data.info and self.has_part('info'):
            self.xml_starttag(u"infos")
            for info in url_data.info:
                self.xml_tag(u"info", info)
            self.xml_endtag(u"infos")
        if url_data.modified and self.has_part('modified'):
            self.xml_tag(u"modified", self.format_modified(url_data.modified))
        if url_data.warnings and self.has_part('warning'):
            self.xml_starttag(u"warnings")
            for tag, data in url_data.warnings:
                attrs = {}
                if tag:
                    attrs["tag"] = tag
                self.xml_tag(u"warning", data, attrs)
            self.xml_endtag(u"warnings")
        if self.has_part("result"):
            attrs = {}
            if url_data.result:
                attrs["result"] = url_data.result
            self.xml_tag(u"valid", u"%d" % (1 if url_data.valid else 0), attrs)
        self.xml_endtag(u'urldata')
        self.flush()

    def end_output (self, **kwargs):
        """
        Write XML end tag.
        """
        self.xml_endtag(u"linkchecker")
        self.xml_end_output()
        self.close_fileoutput()
