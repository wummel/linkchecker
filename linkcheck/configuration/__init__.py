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
Store metadata and options.
"""

import sys
import os
import re
import logging.config
import urllib
import urlparse
import shutil
import socket
import _LinkChecker_configdata as configdata
from .. import (log, LOG_CHECK, LOG_ROOT, ansicolor, lognames,
    get_install_data, fileutil, configdict)
from . import confparse
from ..decorators import memoized

Version = configdata.version
ReleaseDate = configdata.release_date
AppName = configdata.name
App = AppName+u" "+Version
Author = configdata.author
HtmlAuthor = Author.replace(u' ', u'&nbsp;')
Copyright = u"Copyright (C) 2000-2014 "+Author
HtmlCopyright = u"Copyright &copy; 2000-2014 "+HtmlAuthor
AppInfo = App+u"              "+Copyright
HtmlAppInfo = App+u", "+HtmlCopyright
Url = configdata.url
SupportUrl = u"https://github.com/wummel/linkchecker/issues"
DonateUrl = u"http://wummel.github.io/linkchecker/donations.html"
Email = configdata.author_email
UserAgent = u"Mozilla/5.0 (compatible; %s/%s; +%s)" % (AppName, Version, Url)
Freeware = AppName+u""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""
Portable = configdata.portable

def normpath (path):
    """Norm given system path with all available norm or expand functions
    in os.path."""
    expanded = os.path.expanduser(os.path.expandvars(path))
    return os.path.normcase(os.path.normpath(expanded))


# List optional Python modules in the form (module, name)
Modules = (
    ("PyQt4.Qsci", u"QScintilla"),
    ("argcomplete", u"Argcomplete"),
    ("GeoIP", u"GeoIP"),   # on Unix systems
    ("pygeoip", u"GeoIP"), # on Windows systems
    ("twill", u"Twill"),
    ("sqlite3", u"Sqlite"),
    ("gconf", u"Gconf"),
    ("meliae", u"Meliae"),
)

def get_modules_info ():
    """Return list of unicode strings with detected module info."""
    lines = []
    # requests
    import requests
    lines.append(u"Requests: %s" % requests.__version__)
    # PyQt
    try:
        from PyQt4 import QtCore
        lines.append(u"Qt: %s / PyQt: %s" %
                     (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
    except (ImportError, AttributeError):
        pass
    # modules
    modules = [name for (mod, name) in Modules if fileutil.has_module(mod)]
    if modules:
        lines.append(u"Modules: %s" % (u", ".join(modules)))
    return lines


def get_share_dir ():
    """Return absolute path of LinkChecker example configuration."""
    return os.path.join(get_install_data(), "share", "linkchecker")


def get_share_file (filename, devel_dir=None):
    """Return a filename in the share directory.
    @param devel_dir: directory to search when developing
    @ptype devel_dir: string
    @param filename: filename to search for
    @ptype filename: string
    @return: the found filename or None
    @rtype: string
    @raises: ValueError if not found
    """
    paths = [get_share_dir()]
    if devel_dir is not None:
        # when developing
        paths.insert(0, devel_dir)
    for path in paths:
        fullpath = os.path.join(path, filename)
        if os.path.isfile(fullpath):
            return fullpath
    # not found
    msg = "%s not found in %s; check your installation" % (filename, paths)
    raise ValueError(msg)


# dynamic options
class Configuration (dict):
    """
    Storage for configuration options. Options can both be given from
    the command line as well as from configuration files.
    """

    def __init__ (self):
        """
        Initialize the default options.
        """
        super(Configuration, self).__init__()
        ## checking options
        self["allowedschemes"] = []
        self['cookiefile'] = None
        self["debugmemory"] = False
        self["localwebroot"] = None
        self["maxfilesizeparse"] = 1*1024*1024
        self["maxfilesizedownload"] = 5*1024*1024
        self["maxnumurls"] = None
        self["maxrunseconds"] = None
        self["maxrequestspersecond"] = 10
        self["maxhttpredirects"] = 10
        self["nntpserver"] = os.environ.get("NNTP_SERVER", None)
        self["proxy"] = urllib.getproxies()
        self["sslverify"] = True
        self["threads"] = 10
        self["timeout"] = 60
        self["aborttimeout"] = 300
        self["recursionlevel"] = -1
        self["useragent"] = UserAgent
        ## authentication
        self["authentication"] = []
        self["loginurl"] = None
        self["loginuserfield"] = "login"
        self["loginpasswordfield"] = "password"
        self["loginextrafields"] = {}
        ## filtering
        self["externlinks"] = []
        self["ignorewarnings"] = []
        self["internlinks"] = []
        self["checkextern"] = False
        ## plugins
        self["pluginfolders"] = get_plugin_folders()
        self["enabledplugins"] = []
        ## output
        self['trace'] = False
        self['quiet'] = False
        self["verbose"] = False
        self["warnings"] = True
        self["fileoutput"] = []
        self['output'] = 'text'
        self["status"] = False
        self["status_wait_seconds"] = 5
        self['logger'] = None
        self.loggers = {}
        from ..logger import LoggerClasses
        for c in LoggerClasses:
            key = c.LoggerName
            self[key] = {}
            self.loggers[key] = c

    def init_logging (self, status_logger, debug=None, handler=None):
        """
        Set up the application logging (not to be confused with check
        loggers). When debug is not None it is expected to be a list of
        logger names for which debugging will be enabled.

        If no thread debugging is enabled, threading will be disabled.
        """
        logging.config.dictConfig(configdict)
        if handler is None:
            handler = ansicolor.ColoredStreamHandler(strm=sys.stderr)
        self.add_loghandler(handler, debug)
        self.set_debug(debug)
        self.status_logger = status_logger

    def set_debug (self, debug):
        """Set debugging levels for configured loggers. The argument
        is a list of logger names to enable debug for."""
        self.set_loglevel(debug, logging.DEBUG)

    def add_loghandler (self, handler, debug):
        """Add log handler to root logger LOG_ROOT and set formatting."""
        logging.getLogger(LOG_ROOT).addHandler(handler)
        format = "%(levelname)s "
        if debug:
            format += "%(asctime)s "
        if self['threads'] > 0:
            format += "%(threadName)s "
        format += "%(message)s"
        handler.setFormatter(logging.Formatter(format))

    def remove_loghandler (self, handler):
        """Remove log handler from root logger LOG_ROOT."""
        logging.getLogger(LOG_ROOT).removeHandler(handler)

    def reset_loglevel (self):
        """Reset log level to display only warnings and errors."""
        self.set_loglevel(['all'], logging.WARN)

    def set_loglevel (self, loggers, level):
        """Set logging levels for given loggers."""
        if not loggers:
            return
        if 'all' in loggers:
            loggers = lognames.keys()
        # disable threading if no thread debugging
        if "thread" not in loggers and level == logging.DEBUG:
            self['threads'] = 0
        for key in loggers:
            logging.getLogger(lognames[key]).setLevel(level)

    def logger_new (self, loggername, **kwargs):
        """Instantiate new logger and return it."""
        args = self[loggername]
        args.update(kwargs)
        return self.loggers[loggername](**args)

    def logger_add (self, loggerclass):
        """Add a new logger type to the known loggers."""
        self.loggers[loggerclass.LoggerName] = loggerclass
        self[loggerclass.LoggerName] = {}

    def read (self, files=None):
        """
        Read settings from given config files.

        @raises: LinkCheckerError on syntax errors in the config file(s)
        """
        if files is None:
            cfiles = []
        else:
            cfiles = files[:]
        if not cfiles:
            userconf = get_user_config()
            if os.path.isfile(userconf):
                cfiles.append(userconf)
        # filter invalid files
        filtered_cfiles = []
        for cfile in cfiles:
            if not os.path.isfile(cfile):
                log.warn(LOG_CHECK, _("Configuration file %r does not exist."), cfile)
            elif not fileutil.is_readable(cfile):
                log.warn(LOG_CHECK, _("Configuration file %r is not readable."), cfile)
            else:
                filtered_cfiles.append(cfile)
        log.debug(LOG_CHECK, "reading configuration from %s", filtered_cfiles)
        confparse.LCConfigParser(self).read(filtered_cfiles)
        self.sanitize()

    def add_auth (self, user=None, password=None, pattern=None):
        """Add given authentication data."""
        if not user or not pattern:
            log.warn(LOG_CHECK,
            _("missing user or URL pattern in authentication data."))
            return
        entry = dict(
            user=user,
            password=password,
            pattern=re.compile(pattern),
        )
        self["authentication"].append(entry)

    def get_user_password (self, url):
        """Get tuple (user, password) from configured authentication
        that matches the given URL.
        Both user and password can be None if not specified, or no
        authentication matches the given URL.
        """
        for auth in self["authentication"]:
            if auth['pattern'].match(url):
                return (auth['user'], auth['password'])
        return (None, None)

    def get_connectionlimits(self):
        """Get dict with limit per connection type."""
        return {key: self['maxconnections%s' % key] for key in ('http', 'https', 'ftp')}

    def sanitize (self):
        "Make sure the configuration is consistent."
        if self['logger'] is None:
            self.sanitize_logger()
        if self['loginurl']:
            self.sanitize_loginurl()
        self.sanitize_proxies()
        self.sanitize_plugins()
        self.sanitize_ssl()
        # set default socket timeout
        socket.setdefaulttimeout(self['timeout'])

    def sanitize_logger (self):
        """Make logger configuration consistent."""
        if not self['output']:
            log.warn(LOG_CHECK, _("activating text logger output."))
            self['output'] = 'text'
        self['logger'] = self.logger_new(self['output'])

    def sanitize_loginurl (self):
        """Make login configuration consistent."""
        url = self["loginurl"]
        disable = False
        if not self["loginpasswordfield"]:
            log.warn(LOG_CHECK,
            _("no CGI password fieldname given for login URL."))
            disable = True
        if not self["loginuserfield"]:
            log.warn(LOG_CHECK,
            _("no CGI user fieldname given for login URL."))
            disable = True
        if self.get_user_password(url) == (None, None):
            log.warn(LOG_CHECK,
            _("no user/password authentication data found for login URL."))
            disable = True
        if not url.lower().startswith(("http:", "https:")):
            log.warn(LOG_CHECK, _("login URL is not a HTTP URL."))
            disable = True
        urlparts = urlparse.urlsplit(url)
        if not urlparts[0] or not urlparts[1] or not urlparts[2]:
            log.warn(LOG_CHECK, _("login URL is incomplete."))
            disable = True
        if disable:
            log.warn(LOG_CHECK,
              _("disabling login URL %(url)s.") % {"url": url})
            self["loginurl"] = None

    def sanitize_proxies (self):
        """Try to read additional proxy settings which urllib does not
        support."""
        if os.name != 'posix':
            return
        if "http" not in self["proxy"]:
            http_proxy = get_gconf_http_proxy() or get_kde_http_proxy()
            if http_proxy:
                self["proxy"]["http"] = http_proxy
        if "ftp" not in self["proxy"]:
            ftp_proxy = get_gconf_ftp_proxy() or get_kde_ftp_proxy()
            if ftp_proxy:
                self["proxy"]["ftp"] = ftp_proxy

    def sanitize_plugins(self):
        """Ensure each plugin is configurable."""
        for plugin in self["enabledplugins"]:
            if plugin not in self:
                self[plugin] = {}

    def sanitize_ssl(self):
        """Use locally installed certificate file if available."""
        if self["sslverify"] is True:
            try:
                self["sslverify"] = get_share_file('cacert.pem')
            except ValueError:
                pass


def get_plugin_folders():
    """Get linkchecker plugin folders. Default is ~/.linkchecker/plugins/."""
    folders = []
    defaultfolder = normpath("~/.linkchecker/plugins")
    if not os.path.exists(defaultfolder) and not Portable:
        try:
            make_userdir(defaultfolder)
        except StandardError as errmsg:
            msg = _("could not create plugin directory %(dirname)r: %(errmsg)r")
            args = dict(dirname=defaultfolder, errmsg=errmsg)
            log.warn(LOG_CHECK, msg % args)
    if os.path.exists(defaultfolder):
        folders.append(defaultfolder)
    return folders


def make_userdir(child):
    """Create a child directory."""
    userdir = os.path.dirname(child)
    if not os.path.isdir(userdir):
        if os.name == 'nt':
            # Windows forbids filenames with leading dot unless
            # a trailing dot is added.
            userdir += "."
        os.mkdir(userdir, 0700)


def get_user_config():
    """Get the user configuration filename.
    If the user configuration file does not exist, copy it from the initial
    configuration file, but only if this is not a portable installation.
    Returns path to user config file (which might not exist due to copy
    failures or on portable systems).
    @return configuration filename
    @rtype string
    """
    # initial config (with all options explained)
    initialconf = normpath(os.path.join(get_share_dir(), "linkcheckerrc"))
    # per user config settings
    userconf = normpath("~/.linkchecker/linkcheckerrc")
    if os.path.isfile(initialconf) and not os.path.exists(userconf) and \
       not Portable:
        # copy the initial configuration to the user configuration
        try:
            make_userdir(userconf)
            shutil.copy(initialconf, userconf)
        except StandardError as errmsg:
            msg = _("could not copy initial configuration file %(src)r to %(dst)r: %(errmsg)r")
            args = dict(src=initialconf, dst=userconf, errmsg=errmsg)
            log.warn(LOG_CHECK, msg % args)
    return userconf


def get_gconf_http_proxy ():
    """Return host:port for GConf HTTP proxy if found, else None."""
    try:
        import gconf
    except ImportError:
        return None
    try:
        client = gconf.client_get_default()
        if client.get_bool("/system/http_proxy/use_http_proxy"):
            host = client.get_string("/system/http_proxy/host")
            port = client.get_int("/system/http_proxy/port")
            if host:
                if not port:
                    port = 8080
                return "%s:%d" % (host, port)
    except StandardError as msg:
        log.debug(LOG_CHECK, "error getting HTTP proxy from gconf: %s", msg)
        pass
    return None


def get_gconf_ftp_proxy ():
    """Return host:port for GConf FTP proxy if found, else None."""
    try:
        import gconf
    except ImportError:
        return None
    try:
        client = gconf.client_get_default()
        host = client.get_string("/system/proxy/ftp_host")
        port = client.get_int("/system/proxy/ftp_port")
        if host:
            if not port:
                port = 8080
            return "%s:%d" % (host, port)
    except StandardError as msg:
        log.debug(LOG_CHECK, "error getting FTP proxy from gconf: %s", msg)
        pass
    return None


def get_kde_http_proxy ():
    """Return host:port for KDE HTTP proxy if found, else None."""
    config_dir = get_kde_config_dir()
    if not config_dir:
        # could not find any KDE configuration directory
        return
    try:
        data = read_kioslaverc(config_dir)
        return data.get("http_proxy")
    except StandardError as msg:
        log.debug(LOG_CHECK, "error getting HTTP proxy from KDE: %s", msg)
        pass


def get_kde_ftp_proxy ():
    """Return host:port for KDE HTTP proxy if found, else None."""
    config_dir = get_kde_config_dir()
    if not config_dir:
        # could not find any KDE configuration directory
        return
    try:
        data = read_kioslaverc(config_dir)
        return data.get("ftp_proxy")
    except StandardError as msg:
        log.debug(LOG_CHECK, "error getting FTP proxy from KDE: %s", msg)
        pass

# The following KDE functions are largely ported and ajusted from
# Google Chromium:
# http://src.chromium.org/viewvc/chrome/trunk/src/net/proxy/proxy_config_service_linux.cc?revision=HEAD&view=markup
# Copyright (c) 2010 The Chromium Authors. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#    * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

def get_kde_config_dir ():
    """Return KDE configuration directory or None if not found."""
    kde_home = get_kde_home_dir()
    if not kde_home:
        # could not determine the KDE home directory
        return
    return kde_home_to_config(kde_home)


def kde_home_to_config (kde_home):
    """Add subdirectories for config path to KDE home directory."""
    return os.path.join(kde_home, "share", "config")


def get_kde_home_dir ():
    """Return KDE home directory or None if not found."""
    if os.environ.get("KDEHOME"):
        kde_home = os.path.abspath(os.environ["KDEHOME"])
    else:
        home = os.environ.get("HOME")
        if not home:
            # $HOME is not set
            return
        kde3_home = os.path.join(home, ".kde")
        kde4_home = os.path.join(home, ".kde4")
        if fileutil.find_executable("kde4-config"):
            # kde4
            kde3_file = kde_home_to_config(kde3_home)
            kde4_file = kde_home_to_config(kde4_home)
            if os.path.exists(kde4_file) and os.path.exists(kde3_file):
                if fileutil.get_mtime(kde4_file) >= fileutil.get_mtime(kde3_file):
                    kde_home = kde4_home
                else:
                    kde_home = kde3_home
            else:
                kde_home = kde4_home
        else:
            # kde3
            kde_home = kde3_home
    return kde_home if os.path.exists(kde_home) else None


loc_ro = re.compile(r"\[.*\]$")

@memoized
def read_kioslaverc (kde_config_dir):
    """Read kioslaverc into data dictionary."""
    data = {}
    filename = os.path.join(kde_config_dir, "kioslaverc")
    with open(filename) as fd:
        # First read all lines into dictionary since they can occur
        # in any order.
        for line in  fd:
            line = line.rstrip()
            if line.startswith('['):
                in_proxy_settings = line.startswith("[Proxy Settings]")
            elif in_proxy_settings:
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                # trim optional localization
                key = loc_ro.sub("", key).strip()
                if not key:
                    continue
                add_kde_setting(key, value, data)
    resolve_kde_settings(data)
    return data


def add_kde_proxy (key, value, data):
    """Add a proxy value to data dictionary after sanity checks."""
    if not value or value[:3] == "//:":
        return
    data[key] = value


def add_kde_setting (key, value, data):
    """Add a KDE proxy setting value to data dictionary."""
    if key == "ProxyType":
        mode = None
        int_value = int(value)
        if int_value == 1:
            mode = "manual"
        elif int_value == 2:
            # PAC URL
            mode = "pac"
        elif int_value == 3:
            # WPAD.
            mode = "wpad"
        elif int_value == 4:
            # Indirect manual via environment variables.
            mode = "indirect"
        data["mode"] = mode
    elif key == "Proxy Config Script":
        data["autoconfig_url"] = value
    elif key == "httpProxy":
        add_kde_proxy("http_proxy", value, data)
    elif key == "httpsProxy":
        add_kde_proxy("https_proxy", value, data)
    elif key == "ftpProxy":
        add_kde_proxy("ftp_proxy", value, data)
    elif key == "ReversedException":
        data["reversed_bypass"] = bool(value == "true" or int(value))
    elif key == "NoProxyFor":
        data["ignore_hosts"] = split_hosts(value)
    elif key == "AuthMode":
        mode = int(value)
        # XXX todo


def split_hosts (value):
    """Split comma-separated host list."""
    return [host for host in value.split(", ") if host]


def resolve_indirect (data, key, splithosts=False):
    """Replace name of environment variable with its value."""
    value = data[key]
    env_value = os.environ.get(value)
    if env_value:
        if splithosts:
            data[key] = split_hosts(env_value)
        else:
            data[key] = env_value
    else:
        del data[key]


def resolve_kde_settings (data):
    """Write final proxy configuration values in data dictionary."""
    if "mode" not in data:
        return
    if data["mode"] == "indirect":
        for key in ("http_proxy", "https_proxy", "ftp_proxy"):
            if key in data:
                resolve_indirect(data, key)
        if "ignore_hosts" in data:
            resolve_indirect(data, "ignore_hosts", splithosts=True)
    elif data["mode"] != "manual":
        # unsupported config
        for key in ("http_proxy", "https_proxy", "ftp_proxy"):
            if key in data:
                del data[key]
