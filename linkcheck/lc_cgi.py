"""common CGI functions used by the CGI scripts"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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

import sys, os, re, time, urlparse, Config, i18n
from linkcheck import getLinkPat, checkUrls
from linkcheck.log import strtime
from UrlData import GetUrlDataFrom
from types import StringType

_logfile = None
_supported_langs = ('de', 'fr', 'nl', 'C')

_is_level = re.compile(r"\d").match
_is_valid_url = re.compile(r"^https?://[-\w./=%?~]+$").match

class FormError (Exception):
    """form related errors"""
    pass


def checkaccess (out=sys.stdout, hosts=[], servers=[], env=os.environ):
    if os.environ.get('REMOTE_ADDR') not in hosts or \
       os.environ.get('SERVER_ADDR') not in servers:
        logit({}, env)
        printError(out, "Access denied")


def checklink (out=sys.stdout, form={}, env=os.environ):
    """main cgi function, check the given links and print out the result"""
    out.write("Content-type: text/html\r\n"
              "Cache-Control: no-cache\r\n"
              "Pragma: no-cache\r\n"
              "\r\n")
    try: checkform(form)
    except FormError, why:
        logit(form, env)
        printError(out, why)
        return
    config = Config.Configuration()
    config["recursionlevel"] = int(form["level"].value)
    config["log"] = config.newLogger('html', {'fd': out})
    config.disableThreading()
    if form.has_key('strict'): config['strict'] = 1
    if form.has_key("anchors"): config["anchors"] = 1
    if not form.has_key("errors"): config["verbose"] = 1
    if form.has_key("intern"):
        pat = "^(ftp|https?)://"+re.escape(getHostName(form))
    else:
        pat = ".+"
    config["internlinks"].append(getLinkPat(pat))
    # avoid checking of local files
    config["externlinks"].append(getLinkPat("^file:", strict=1))
    # start checking
    config.appendUrl(GetUrlDataFrom(form["url"].value, 0, config))
    checkUrls(config)


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
            i18n.init_gettext()
        else:
            raise FormError(i18n._("unsupported language"))
    # check url syntax
    if form.has_key("url"):
        url = form["url"].value
        if not url or url=="http://":
            raise FormError(i18n._("empty url was given"))
        if not _is_valid_url(url):
            raise FormError(i18n._("invalid url was given"))
    else:
        raise FormError(i18n._("no url was given"))
    # check recursion level
    if form.has_key("level"):
        level = form["level"].value
        if not _is_level(level):
            raise FormError(i18n._("invalid recursion level syntax"))
        if int(level) > 3:
            raise FormError(i18n._("recursion level greater than 3"))
    # check options
    for option in ("strict", "anchors", "errors", "intern"):
        if form.has_key(option):
            if not form[option].value=="on":
                raise FormError(i18n._("invalid %s option syntax") % option)


def logit (form, env):
    """log form errors"""
    global _logfile
    if not _logfile:
        return
    elif type(_logfile) == StringType:
        _logfile = file(_logfile, "a")
    _logfile.write("\n"+strtime(time.time())+"\n")
    for var in ["HTTP_USER_AGENT", "REMOTE_ADDR",
                "REMOTE_HOST", "REMOTE_PORT"]:
        if env.has_key(var):
            _logfile.write(var+"="+env[var]+"\n")
    for key in ["level", "url", "anchors", "errors", "intern", "language"]:
        if form.has_key(key):
            _logfile.write(str(form[key])+"\n")


def printError (out, why):
    """print standard error page"""
    out.write(i18n._("""<html><head>
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
    checklink(form={"url": store("http://localhost"),
                "level": store("0"),
              })
