# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012-2014 Bastian Kleineidam
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
from .. import log, LOG_CHECK

ChangeFreqs = (
    'always',
    'hourly',
    'daily',
    'weekly',
    'monthly',
    'yearly',
    'never',
)

HTTP_SCHEMES = (u'http:', u'https:')
HTML_TYPES = ('text/html', "application/xhtml+xml")

class SitemapXmlLogger (xmllog._XMLLogger):
    """Sitemap XML output according to http://www.sitemaps.org/protocol.html
    """

    LoggerName = 'sitemap'

    LoggerArgs = {
        "filename": "linkchecker-out.sitemap.xml",
        "encoding": "utf-8",
    }

    def __init__ (self, **kwargs):
        """Initialize graph node list and internal id counter."""
        args = self.get_args(kwargs)
        super(SitemapXmlLogger, self).__init__(**args)
        # All URLs must have the given prefix, which is determined
        # by the first logged URL.
        self.prefix = None
        # If first URL does not have a valid HTTP scheme, disable this
        # logger
        self.disabled = False
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
        """Write start of checking info as xml comment."""
        super(SitemapXmlLogger, self).start_output()
        self.xml_start_output()
        attrs = {u"xmlns": u"http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.xml_starttag(u'urlset', attrs)
        self.flush()

    def log_filter_url(self, url_data, do_print):
        """Update accounting data and determine if URL should be included
        in the sitemap.
        """
        self.stats.log_url(url_data, do_print)
        if self.disabled:
            return
        # initialize prefix and priority
        if self.prefix is None:
            if not url_data.url.startswith(HTTP_SCHEMES):
                log.warn(LOG_CHECK, "Sitemap URL %r does not start with http: or https:.", url_data.url)
                self.disabled = True
                return
            self.prefix = url_data.url
            # first URL (ie. the homepage) gets priority 1.0 per default
            priority = 1.0
        elif url_data.url == self.prefix:
            return
        else:
            # all other pages get priority 0.5 per default
            priority = 0.5
        if self.priority is not None:
            priority = self.priority
         # ignore the do_print flag and determine ourselves if we filter the url
        if (url_data.valid
            and url_data.url.startswith(HTTP_SCHEMES)
            and url_data.url.startswith(self.prefix)
            and url_data.content_type in HTML_TYPES):
            self.log_url(url_data, priority=priority)

    def log_url (self, url_data, priority=None):
        """Log URL data in sitemap format."""
        self.xml_starttag(u'url')
        self.xml_tag(u'loc', url_data.url)
        if url_data.modified:
            self.xml_tag(u'lastmod', self.format_modified(url_data.modified, sep="T"))
        self.xml_tag(u'changefreq', self.frequency)
        self.xml_tag(u'priority', "%.2f" % priority)
        self.xml_endtag(u'url')
        self.flush()

    def end_output (self, **kwargs):
        """Write XML end tag."""
        self.xml_endtag(u"urlset")
        self.xml_end_output()
        self.close_fileoutput()
