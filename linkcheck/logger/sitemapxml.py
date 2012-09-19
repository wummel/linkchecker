# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012 Bastian Kleineidam
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
A sitemap XML logger.
"""
from . import xmllog

ChangeFreqs = (
    'always',
    'hourly',
    'daily',
    'weekly',
    'monthly',
    'yearly',
    'never',
)

class SitemapXmlLogger (xmllog.XMLLogger):
    """
    Sitemap XML output according to http://www.sitemaps.org/protocol.html
    """

    def __init__ (self, **args):
        """
        Initialize graph node list and internal id counter.
        """
        super(SitemapXmlLogger, self).__init__(**args)
        # All URLs must have the given prefix, which is determined
        # by the first logged URL.
        self.prefix = None
        if 'frequency' in args:
            if args['frequency'] not in ChangeFreqs:
                raise ValueError("Invalid change frequency %r" % args['frequency'])
            self.frequency = args['frequency']
        else:
            self.frequency = 'daily'
        self.priority = None
        if 'priority' in args:
            self.priority = float(args['priority'])

    def start_output (self):
        """
        Write start of checking info as xml comment.
        """
        super(SitemapXmlLogger, self).start_output()
        self.xml_start_output()
        attrs = {u"xmlns": u"http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.xml_starttag(u'urlset', attrs)
        self.flush()

    def log_filter_url(self, url_data, do_print):
        """
        Update accounting data and determine if URL should be included in the sitemap.
        """
        self.stats.log_url(url_data, do_print)
        # ignore the do_print flag and determine ourselves if we filter the url
        if (url_data.valid and
            url_data.url.startswith((u'http:', u'https:')) and
            url_data.url.startswith(self.prefix) and
            url_data.content_type in ('text/html', "application/xhtml+xml")):
            self.log_url(url_data)

    def log_url (self, url_data):
        """
        Log URL data in sitemap format.
        """
        if self.prefix is None:
            # first URL (ie. the homepage) gets priority 1.0 per default
            self.prefix = url_data.url
            priority = 1.0
        else:
            # all other pages get priority 0.5 per default
            priority = 0.5
        if self.priority is not None:
            priority = self.priority
        self.xml_starttag(u'url')
        self.xml_tag(u'loc', url_data.url)
        if url_data.modified:
            modified = get_sitemap_modified(url_data.modified)
            if modified:
                self.xml_tag(u'lastmod', modified)
        self.xml_tag(u'changefreq', self.frequency)
        self.xml_tag(u'priority', "%.1f" % priority)
        self.xml_endtag(u'url')
        self.flush()

    def end_output (self):
        """
        Write XML end tag.
        """
        self.xml_endtag(u"urlset")
        self.xml_end_output()
        self.close_fileoutput()


def get_sitemap_modified(modified):
    """Reformat UrlData modified string into sitemap format specified at
     http://www.w3.org/TR/NOTE-datetime.
    @param modified: last modified time
    @ptype modified: datetime object with timezone information
    @return: formatted date
    @rtype: string
    """
    return modified.isoformat('T')
