# -*- coding: iso-8859-1 -*-
"""common CGI functions used by the CGI scripts"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import sys
import os
import re
import time
import urlparse
import types
import linkcheck

_logfile = None
_supported_langs = ('de', 'fr', 'nl', 'C')
_is_level = re.compile(r'^[0123]$').match

class FormError (Exception):
    """form related errors"""
    pass


def startoutput (out=sys.stdout):
    out.write("Content-type: text/html\r\n"
              "Cache-Control: no-cache\r\n"
              "Pragma: no-cache\r\n"
              "\r\n")

def checkaccess (out=sys.stdout, hosts=[], servers=[], env=os.environ):
    if os.environ.get('REMOTE_ADDR') in hosts and \
       os.environ.get('SERVER_ADDR') in servers:
        return True
    logit({}, env)
    printError(out, "Access denied")
    return False


def checklink (out=sys.stdout, form={}, env=os.environ):
    """main cgi function, check the given links and print out the result"""
    try: checkform(form)
    except FormError, why:
        logit(form, env)
        printError(out, why)
        return
    config = linkcheck.Config.Configuration()
    config["recursionlevel"] = int(form["level"].value)
    config["log"] = config.newLogger('html', {'fd': out})
    config.setThreads(0)
    if form.has_key('strict'): config['strict'] = True
    if form.has_key("anchors"): config["anchors"] = True
    if not form.has_key("errors"): config["verbose"] = True
    if form.has_key("intern"):
        pat = bk.url.safe_host_pattern(re.escape(getHostName(form)))
    else:
        pat = bk.url.safe_url_pattern
    config["internlinks"].append(linkcheck.getLinkPat("^%s$" % pat))
    # avoid checking of local files or other nasty stuff
    config["externlinks"].append(linkcheck.getLinkPat("^%s$" % safe_url_pattern))
    config["externlinks"].append(linkcheck.getLinkPat(".*", strict=True))
    # start checking
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(form["url"].value, 0, config))
    linkcheck.checkUrls(config)


def getHostName (form):
    """return host name of given url"""
    return urlparse.urlparse(form["url"].value)[1]


def checkform (form):
    """check form data. throw exception on error
       Be sure to NOT print out any user-given data as HTML code, so use
       only plain strings as exception text.
    """
    # check lang support
    if form.has_key("language"):
        lang = form['language'].value
        if lang in _supported_langs:
            os.environ['LC_MESSAGES'] = lang
            bk.i18n.init_gettext()
        else:
            raise FormError(bk.i18n._("unsupported language"))
    # check url syntax
    if form.has_key("url"):
        url = form["url"].value
        if not url or url=="http://":
            raise FormError(bk.i18n._("empty url was given"))
        if not bk.url.is_valid_url(url):
            raise FormError(bk.i18n._("invalid url was given"))
    else:
        raise FormError(bk.i18n._("no url was given"))
    # check recursion level
    if form.has_key("level"):
        level = form["level"].value
        if not _is_level(level):
            raise FormError(bk.i18n._("invalid recursion level"))
    # check options
    for option in ("strict", "anchors", "errors", "intern"):
        if form.has_key(option):
            if not form[option].value=="on":
                raise FormError(bk.i18n._("invalid %s option syntax") % option)

def logit (form, env):
    """log form errors"""
    global _logfile
    if not _logfile:
        return
    elif type(_logfile) == types.StringType:
        _logfile = file(_logfile, "a")
    _logfile.write("\n"+bk.strtime.strtime(time.time())+"\n")
    for var in ["HTTP_USER_AGENT", "REMOTE_ADDR",
                "REMOTE_HOST", "REMOTE_PORT"]:
        if env.has_key(var):
            _logfile.write(var+"="+env[var]+"\n")
    for key in ["level", "url", "anchors", "errors", "intern", "language"]:
        if form.has_key(key):
            _logfile.write(str(form[key])+"\n")


def printError (out, why):
    """print standard error page"""
    out.write(bk.i18n._("""<html><head>
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


if __name__=='__main__':
    class store:
        def __init__ (self, value):
            self.value = value
    form={"url": store("http://www.heise.de/"),
          "level": store("0"),
         }
    checkform(form)
