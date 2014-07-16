# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
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
HTML form utils
"""
from ..HtmlParser import htmlsax
from .. import log, LOG_CHECK

class Form(object):
    """Store HTML form URL and form data."""

    def __init__(self, url):
        """Set URL and empty form data."""
        self.url = url
        self.data = {}

    def add_value(self, key, value):
        """Add a form value."""
        self.data[key] = value

    def __repr__(self):
        """Return unicode representation displaying URL and form data."""
        return unicode(self)

    def __unicode__(self):
        """Return unicode string displaying URL and form data."""
        return u"<url=%s data=%s>" % (self.url, self.data)

    def __str__(self):
        """Return string displaying URL and form data."""
        return unicode(self).encode('utf-8')


class FormFinder(object):
    """Base class handling HTML start elements.
    TagFinder instances are used as HtmlParser handlers."""

    def __init__(self):
        """Initialize local variables."""
        super(FormFinder, self).__init__()
        # parser object will be initialized when it is used as
        # a handler object
        self.parser = None
        self.forms = []
        self.form = None

    def start_element(self, tag, attrs):
        """Does nothing, override in a subclass."""
        if tag == u'form':
            if u'action' in attrs:
                url = attrs['action']
                self.form = Form(url)
        elif tag == u'input':
            if self.form:
                if 'name' in attrs:
                    key = attrs['name']
                    value = attrs.get('value')
                    self.form.add_value(key, value)
                else:
                    log.warning(LOG_CHECK, "nameless form input %s" % attrs)
                    pass
            else:
                log.warning(LOG_CHECK, "formless input´%s" % attrs)
                pass

    def start_end_element(self, tag, attrs):
        """Delegate a combined start/end element (eg. <input .../>) to
        the start_element method. Ignore the end element part."""
        self.start_element(tag, attrs)

    def end_element(self, tag):
        """search for ending form values."""
        if tag == u'form':
            self.forms.append(self.form)
            self.form = None


def search_form(content, cgiuser, cgipassword, encoding='utf-8'):
    """Search for a HTML form in the given HTML content that has the given
    CGI fields. If no form is found return None.
    """
    handler = FormFinder()
    parser = htmlsax.parser(handler)
    handler.parser = parser
    parser.encoding = encoding
    # parse
    parser.feed(content)
    parser.flush()
    # break cyclic dependencies
    handler.parser = None
    parser.handler = None
    log.debug(LOG_CHECK, "Found forms %s", handler.forms)
    cginames = (cgiuser.lower(), cgipassword.lower())
    for form in handler.forms:
        for key, value in form.data.items():
            if key.lower() in cginames:
                return form
    # not found
    return None
