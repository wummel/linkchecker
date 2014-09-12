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
Functions used by the WSGI script.
"""

import cgi
import os
import threading
import locale
import re
import time
try:
    import urlparse
except ImportError:
    # Python 3
    from urllib import parse as urlparse
from . import configuration, strformat, checker, director, get_link_pat, \
    init_i18n, url as urlutil
from .decorators import synchronized

# 5 minutes timeout for requests
MAX_REQUEST_SECONDS = 300
# character set encoding for HTML output
HTML_ENCODING = 'utf-8'


def application(environ, start_response):
    """WSGI interface: start an URL check."""
    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    # When the method is POST the query string will be sent
    # in the HTTP request body which is passed by the WSGI server
    # in the file like wsgi.input environment variable.
    if request_body_size > 0:
        request_body = environ['wsgi.input'].read(request_body_size)
    else:
        request_body = environ['wsgi.input'].read()
    form = cgi.parse_qs(request_body)

    status = '200 OK'
    start_response(status, get_response_headers())
    for output in checklink(form=form, env=environ):
        yield output


_supported_langs = ('de', 'C')
# map language -> locale name
lang_locale = {
    'de': 'de_DE',
    'C': 'C',
    'en': 'en_EN',
}
_is_level = re.compile(r'^(0|1|2|3|-1)$').match

class LCFormError(Exception):
    """Form related errors."""
    pass


def get_response_headers():
    """Get list of response headers in key-value form."""
    return [("Content-type", "text/html"),
            ("Cache-Control", "no-cache"),
            ("Pragma:", "no-cache")
           ]


def formvalue (form, key):
    """Get value with given key from WSGI form."""
    field = form.get(key)
    if isinstance(field, list):
        field = field[0]
    return field


_lock = threading.Lock()
class ThreadsafeIO (object):
    """Thread-safe unicode I/O class."""

    def __init__(self):
        """Initialize buffer."""
        self.buf = []
        self.closed = False

    @synchronized(_lock)
    def write (self, data):
        """Write given unicode data to buffer."""
        assert isinstance(data, unicode)
        if self.closed:
            raise IOError("Write on closed I/O object")
        if data:
            self.buf.append(data)

    @synchronized(_lock)
    def get_data (self):
        """Get bufferd unicode data."""
        data = u"".join(self.buf)
        self.buf = []
        return data

    @synchronized(_lock)
    def close (self):
        """Reset buffer and close this I/O object."""
        self.buf = []
        self.closed = True


def encode(s):
    """Encode given string in HTML encoding."""
    return s.encode(HTML_ENCODING, 'ignore')


def checklink (form=None, env=os.environ):
    """Validates the CGI form and checks the given links."""
    if form is None:
        form = {}
    try:
        checkform(form, env)
    except LCFormError as errmsg:
        log(env, errmsg)
        yield encode(format_error(errmsg))
        return
    out = ThreadsafeIO()
    config = get_configuration(form, out)
    url = strformat.stripurl(formvalue(form, "url"))
    aggregate = director.get_aggregate(config)
    url_data = checker.get_url_from(url, 0, aggregate, extern=(0, 0))
    aggregate.urlqueue.put(url_data)
    for html_str in start_check(aggregate, out):
        yield encode(html_str)
    out.close()


def start_check (aggregate, out):
    """Start checking in background and write encoded output to out."""
    # check in background
    t = threading.Thread(target=director.check_urls, args=(aggregate,))
    t.start()
    # time to wait for new data
    sleep_seconds = 2
    # current running time
    run_seconds = 0
    while not aggregate.is_finished():
        yield out.get_data()
        time.sleep(sleep_seconds)
        run_seconds += sleep_seconds
        if run_seconds > MAX_REQUEST_SECONDS:
            director.abort(aggregate)
            break
    yield out.get_data()


def get_configuration(form, out):
    """Initialize a CGI configuration."""
    config = configuration.Configuration()
    config["recursionlevel"] = int(formvalue(form, "level"))
    config["logger"] = config.logger_new('html', fd=out, encoding=HTML_ENCODING)
    config["threads"] = 2
    if "anchors" in form:
        config["enabledplugins"].append("AnchorCheck")
    if "errors" not in form:
        config["verbose"] = True
    # avoid checking of local files or other nasty stuff
    pat = "!^%s$" % urlutil.safe_url_pattern
    config["externlinks"].append(get_link_pat(pat, strict=True))
    config.sanitize()
    return config


def get_host_name (form):
    """Return host name of given URL."""
    return urlparse.urlparse(formvalue(form, "url"))[1]


def checkform (form, env):
    """Check form data. throw exception on error
    Be sure to NOT print out any user-given data as HTML code, so use
    only plain strings as exception text."""
    # check lang support
    if "language" in form:
        lang = formvalue(form, 'language')
        if lang in _supported_langs:
            localestr = lang_locale[lang]
            try:
                # XXX this is not thread-safe, so think of something else
                locale.setlocale(locale.LC_ALL, localestr)
                init_i18n()
            except locale.Error as errmsg:
                log(env, "could not set locale %r: %s" % (localestr, errmsg))
        else:
            raise LCFormError(_("unsupported language %r") % lang)
    # check url syntax
    if "url" in form:
        url = formvalue(form, "url")
        if not url or url == "http://":
            raise LCFormError(_("empty url was given"))
        if not urlutil.is_safe_url(url):
            raise LCFormError(_("disallowed url %r was given") % url)
    else:
        raise LCFormError(_("no url was given"))
    # check recursion level
    if "level" in form:
        level = formvalue(form, "level")
        if not _is_level(level):
            raise LCFormError(_("invalid recursion level %r") % level)
    # check options
    for option in ("anchors", "errors", "intern"):
        if option in form:
            value = formvalue(form, option)
            if value != "on":
                raise LCFormError(_("invalid %s option %r") % (option, value))


def log (env, msg):
    """Log message to WSGI error output."""
    logfile = env['wsgi.errors']
    logfile.write(msg + "\n")


def dump (env, form):
    """Log environment and form."""
    for var, value in env.items():
        log(env, var+"="+value)
    for key in form:
        log(env, str(formvalue(form, key)))


def format_error (why):
    """Format standard error page.
    @param why: error message
    @ptype why: unicode
    @return: HTML page content
    @rtype: unicode
    """
    return _("""<!DOCTYPE HTML>
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>LinkChecker Online Error</title></head>
<body text=#192c83 bgcolor=#fff7e5 link=#191c83 vlink=#191c83 alink=#191c83>
<blockquote>
<b>Error: %s</b><br/>
The LinkChecker Online script has encountered an error. Please ensure
that your provided URL link begins with <code>http://</code> and
contains only these characters: <code>A-Za-z0-9./_~-</code><br/><br/>
Errors are logged.
</blockquote>
</body>
</html>""") % cgi.escape(why)
