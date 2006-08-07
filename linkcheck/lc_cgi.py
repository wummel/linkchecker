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
Common CGI functions used by the CGI scripts.
"""

import sys
import os
import re
import time
import urlparse
import types

import linkcheck
import linkcheck.configuration
import linkcheck.url
import linkcheck.i18n
import linkcheck.strformat
import linkcheck.checker
import linkcheck.director

_logfile = None
_supported_langs = ('de', 'fr', 'nl', 'C')
_is_level = re.compile(r'^(0|1|2|3|-1)$').match

class FormError (StandardError):
    """
    Form related errors.
    """
    pass


def startoutput (out=sys.stdout):
    """
    Print leading HTML headers to given output stream.
    """
    out.write("Content-type: text/html\r\n"
              "Cache-Control: no-cache\r\n"
              "Pragma: no-cache\r\n"
              "\r\n")

def checkaccess (out=sys.stdout, hosts=None, servers=None, env=os.environ):
    """
    See if remote addr is allowed to access the CGI interface.
    """
    if hosts is None:
        hosts = []
    if servers is None:
        servers = []
    if os.environ.get('REMOTE_ADDR') in hosts and \
       os.environ.get('SERVER_ADDR') in servers:
        return True
    logit({}, env)
    print_error(out, "Access denied")
    return False


def checklink (out=sys.stdout, form=None, env=os.environ):
    """
    Main cgi function, check the given links and print out the result.
    """
    if form is None:
        form = {}
    try:
        checkform(form)
    except FormError, why:
        logit(form, env)
        print_error(out, why)
        return
    config = linkcheck.configuration.Configuration()
    config["recursionlevel"] = int(form["level"].value)
    config["logger"] = config.logger_new('html', fd=out)
    config["threads"] = 0
    if form.has_key("anchors"):
        config["anchors"] = True
    if not form.has_key("errors"):
        config["verbose"] = True
    # avoid checking of local files or other nasty stuff
    pat = "!^%s$" % linkcheck.url.safe_url_pattern
    config["externlinks"].append(linkcheck.get_link_pat(pat, strict=True))
    # start checking
    aggregate = linkcheck.director.get_aggregate(config)
    get_url_from = linkcheck.checker.get_url_from
    url = form["url"].value
    url_data = get_url_from(url, 0, aggregate, assume_local=False)
    try:
        linkcheck.add_intern_pattern(url_data, config)
    except UnicodeError:
        logit({}, env)
        print_error(out,
                    "URL has unparsable domain name: %s" % sys.exc_info()[1])
        return
    aggregate.urlqueue.put(url_data)
    linkcheck.director.check_urls(aggregate)


def get_host_name (form):
    """
    Return host name of given URL.
    """
    return urlparse.urlparse(form["url"].value)[1]


def checkform (form):
    """
    Check form data. throw exception on error
    Be sure to NOT print out any user-given data as HTML code, so use
    only plain strings as exception text.
    """
    # check lang support
    if form.has_key("language"):
        lang = form['language'].value
        if lang in _supported_langs:
            os.environ['LC_MESSAGES'] = lang
            linkcheck.init_i18n()
        else:
            raise FormError(_("unsupported language"))
    # check url syntax
    if form.has_key("url"):
        url = form["url"].value
        if not url or url == "http://":
            raise FormError(_("empty url was given"))
        if not linkcheck.url.is_safe_url(url):
            raise FormError(_("disallowed url was given"))
    else:
        raise FormError(_("no url was given"))
    # check recursion level
    if form.has_key("level"):
        level = form["level"].value
        if not _is_level(level):
            raise FormError(_("invalid recursion level"))
    # check options
    for option in ("anchors", "errors", "intern"):
        if form.has_key(option):
            if not form[option].value == "on":
                raise FormError(_("invalid %s option syntax") % option)

def logit (form, env):
    """
    Log form errors.
    """
    global _logfile
    if not _logfile:
        return
    elif type(_logfile) == types.StringType:
        _logfile = file(_logfile, "a")
    _logfile.write("\n"+linkcheck.strformat.strtime(time.time())+"\n")
    for var in ["HTTP_USER_AGENT", "REMOTE_ADDR",
                "REMOTE_HOST", "REMOTE_PORT"]:
        if env.has_key(var):
            _logfile.write(var+"="+env[var]+"\n")
    for key in ["level", "url", "anchors", "errors", "intern", "language"]:
        if form.has_key(key):
            _logfile.write(str(form[key])+"\n")


def print_error (out, why):
    """
    Print standard error page.
    """
    out.write(_("""<html><head>
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
</html>""") % why)
