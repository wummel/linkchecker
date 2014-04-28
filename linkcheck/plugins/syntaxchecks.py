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
import threading
import time
import requests
from xml.dom.minidom import parseString
from . import _ContentPlugin
from .. import log, LOG_PLUGIN
from ..decorators import synchronized


_w3_time_lock = threading.Lock()


class W3Timer(object):
    """Ensure W3C apis are not hammered."""

    # every X seconds
    SleepSeconds = 2

    def __init__(self):
        """Remember last API call."""
        self.last_w3_call = 0

    @synchronized(_w3_time_lock)
    def check_w3_time (self):
        """Make sure the W3C validators are at most called once a second."""
        if time.time() - self.last_w3_call < W3Timer.SleepSeconds:
            time.sleep(W3Timer.SleepSeconds)
        self.last_w3_call = time.time()


class HtmlSyntaxCheck(_ContentPlugin):
    """Check the syntax of HTML pages with the online W3C HTML validator.
    See http://validator.w3.org/docs/api.html.
    """
    def __init__(self, config):
        """Initialize plugin."""
        super(HtmlSyntaxCheck, self).__init__(config)
        self.timer = W3Timer()

    def applies_to(self, url_data):
        """Check for HTML and extern."""
        return url_data.is_html() and not url_data.extern[0]

    def check(self, url_data):
        """Check HTML syntax of given URL."""
        self.timer.check_w3_time()
        session = url_data.session
        try:
            body = {'uri': url_data.url, 'output': 'soap12'}
            response = session.post('http://validator.w3.org/check', data=body)
            response.raise_for_status()
            if response.headers.get('x-w3c-validator-status', 'Invalid') == 'Valid':
                url_data.add_info(u"W3C Validator: %s" % _("valid HTML syntax"))
                return
            check_w3_errors(url_data, response.text, "W3C HTML")
        except requests.exceptions.RequestException:
            pass # ignore service failures
        except Exception as msg:
            log.warn(LOG_PLUGIN, _("HTML syntax check plugin error: %(msg)s ") % {"msg": msg})


class CssSyntaxCheck(_ContentPlugin):
    """Check the syntax of HTML pages with the online W3C CSS validator.
    See http://jigsaw.w3.org/css-validator/manual.html#expert.
    """

    def __init__(self, config):
        """Initialize plugin."""
        super(CssSyntaxCheck, self).__init__(config)
        self.timer = W3Timer()

    def applies_to(self, url_data):
        """Check for CSS and extern."""
        return url_data.is_css() and not url_data.extern[0]

    def check(self, url_data):
        """Check CSS syntax of given URL."""
        self.timer.check_w3_time()
        session = url_data.session
        try:
            url = 'http://jigsaw.w3.org/css-validator/validator'
            params = {
                'uri': url_data.url,
                'warning': '2',
                'output': 'soap12',
            }
            response = session.get(url, params=params)
            response.raise_for_status()
            if response.headers.get('X-W3C-Validator-Status', 'Invalid') == 'Valid':
                url_data.add_info(u"W3C Validator: %s" % _("valid CSS syntax"))
                return
            check_w3_errors(url_data, response.text, "W3C HTML")
        except requests.exceptions.RequestException:
            pass # ignore service failures
        except Exception as msg:
            log.warn(LOG_PLUGIN, _("CSS syntax check plugin error: %(msg)s ") % {"msg": msg})


def check_w3_errors (url_data, xml, w3type):
    """Add warnings for W3C HTML or CSS errors in xml format.
    w3type is either "W3C HTML" or "W3C CSS"."""
    dom = parseString(xml)
    for error in dom.getElementsByTagName('m:error'):
        warnmsg = _("%(w3type)s validation error at line %(line)s col %(column)s: %(msg)s")
        attrs = {
            "w3type": w3type,
            "line": getXmlText(error, "m:line"),
            "column": getXmlText(error, "m:col"),
            "msg": getXmlText(error, "m:message"),
        }
        url_data.add_warning(warnmsg % attrs)


def getXmlText (parent, tag):
    """Return XML content of given tag in parent element."""
    elem = parent.getElementsByTagName(tag)[0]
    # Yes, the DOM standard is awful.
    rc = []
    for node in elem.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
