# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
Common CGI functions used by the CGI scripts.
"""

import sys
import os
import locale
import re
import time
import urlparse
import types
from . import configuration, strformat, checker, director
from . import add_intern_pattern, get_link_pat, init_i18n
from . import url as urlutil


_logfile = None
_supported_langs = ('de', 'C')
# map language -> locale name
lang_locale = {
    'de': 'de_DE',
    'C': 'C',
    'en': 'en_EN',
}
_is_level = re.compile(r'^(0|1|2|3|-1)$').match

class FormError (StandardError):
    """Form related errors."""
    pass


def startoutput (out=sys.stdout):
    """Print leading HTML headers to given output stream."""
    out.write("Content-type: text/html\r\n"
              "Cache-Control: no-cache\r\n"
              "Pragma: no-cache\r\n"
              "\r\n")


def checkaccess (out=sys.stdout, allowed_clients=None, allowed_servers=None,
    env=os.environ):
    """See if remote and server address is allowed to access the CGI
    interface."""
    if allowed_clients is None:
        allowed_clients = []
    if allowed_servers is None:
        allowed_servers = []
    if env.get('REMOTE_ADDR') in allowed_clients and \
       env.get('SERVER_ADDR') in allowed_servers:
        return True
    logit({}, env)
    print_error(out, u"Access denied")
    return False


def checklink (out=sys.stdout, form=None, env=os.environ):
    """Main cgi function, check the given links and print out the result."""
    if form is None:
        form = {}
    try:
        checkform(form)
    except FormError, why:
        logit(form, env)
        print_error(out, why)
        return
    config = configuration.Configuration()
    config["recursionlevel"] = int(form["level"].value)
    config["logger"] = config.logger_new('html', fd=out)
    config["threads"] = 0
    if "anchors" in form:
        config["anchors"] = True
    if "errors" not in form:
        config["verbose"] = True
    # avoid checking of local files or other nasty stuff
    pat = "!^%s$" % urlutil.safe_url_pattern
    config["externlinks"].append(get_link_pat(pat, strict=True))
    # start checking
    aggregate = director.get_aggregate(config)
    get_url_from = checker.get_url_from
    url = form["url"].value
    url_data = get_url_from(url, 0, aggregate)
    try:
        add_intern_pattern(url_data, config)
    except UnicodeError:
        logit({}, env)
        print_error(out,
                    u"URL has unparsable domain name: %s" % sys.exc_info()[1])
        return
    aggregate.urlqueue.put(url_data)
    director.check_urls(aggregate)


def get_host_name (form):
    """Return host name of given URL."""
    return urlparse.urlparse(form["url"].value)[1]


def checkform (form):
    """Check form data. throw exception on error
    Be sure to NOT print out any user-given data as HTML code, so use
    only plain strings as exception text."""
    # check lang support
    if "language" in form:
        lang = form['language'].value
        if lang in _supported_langs:
            locale.setlocale(locale.LC_ALL, lang_locale[lang])
            init_i18n()
        else:
            raise FormError(_("unsupported language"))
    # check url syntax
    if "url" in form:
        url = form["url"].value
        if not url or url == "http://":
            raise FormError(_("empty url was given"))
        if not urlutil.is_safe_url(url):
            raise FormError(_("disallowed url was given"))
    else:
        raise FormError(_("no url was given"))
    # check recursion level
    if "level" in form:
        level = form["level"].value
        if not _is_level(level):
            raise FormError(_("invalid recursion level"))
    # check options
    for option in ("anchors", "errors", "intern"):
        if option in form:
            if not form[option].value == "on":
                raise FormError(_("invalid %s option syntax") % option)


def logit (form, env):
    """Log form errors."""
    global _logfile
    if not _logfile:
        return
    elif type(_logfile) == types.StringType:
        _logfile = file(_logfile, "a")
    _logfile.write("\n" + strformat.strtime(time.time())+"\n")
    for var in ("HTTP_USER_AGENT", "REMOTE_ADDR",
                "REMOTE_HOST", "REMOTE_PORT"):
        if var in env:
            _logfile.write(var+"="+env[var]+"\n")
    for key in ("level", "url", "anchors", "errors", "intern", "language"):
        if key in form:
            _logfile.write(str(form[key])+"\n")


def print_error (out, why):
    """Print standard error page."""
    s = _("""<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>LinkChecker Online Error</title></head>
<body text=#192c83 bgcolor=#fff7e5 link=#191c83 vlink=#191c83 alink=#191c83>
<blockquote>
<b>Error: %s</b><br>
The LinkChecker Online script has encountered an error. Please ensure
that your provided URL link begins with <code>http://</code> and
contains only these characters: <code>A-Za-z0-9./_~-</code><br><br>
Errors are logged.
</blockquote>
</body>
</html>""") % why
    out.write(s.encode('iso-8859-1', 'ignore'))
