# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2011 Bastian Kleineidam
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
import _LinkChecker_configdata as configdata
from .. import (log, LOG_CHECK, LOG_ROOT, ansicolor, lognames, clamav,
    get_config_dir, fileutil)
from . import confparse
from ..decorators import memoized

Version = configdata.version
AppName = configdata.appname
App = AppName+u" "+Version
Author = configdata.author
HtmlAuthor = Author.replace(u' ', u'&nbsp;')
Copyright = u"Copyright (C) 2000-2011 "+Author
HtmlCopyright = u"Copyright &copy; 2000-2011 "+HtmlAuthor
AppInfo = App+u"              "+Copyright
HtmlAppInfo = App+u", "+HtmlCopyright
Url = configdata.url
SupportUrl = u"http://sourceforge.net/projects/linkchecker/support"
DonateUrl = u"http://linkchecker.sourceforge.net/donations.html"
Email = configdata.author_email
UserAgent = u"%s/%s (+%s)" % (AppName, Version, Url)
Freeware = AppName+u""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""


def normpath (path):
    """
    Norm given system path with all available norm funcs in os.path.
    """
    return os.path.normcase(os.path.normpath(os.path.expanduser(path)))


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
        self['trace'] = False
        self["verbose"] = False
        self["complete"] = False
        self["warnings"] = True
        self["ignorewarnings"] = []
        self['quiet'] = False
        self["anchors"] = False
        self["externlinks"] = []
        self["internlinks"] = []
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = []
        self["loginurl"] = None
        self["loginuserfield"] = "login"
        self["loginpasswordfield"] = "password"
        self["loginextrafields"] = {}
        self["proxy"] = urllib.getproxies()
        self["recursionlevel"] = -1
        self["wait"] = 0
        self['sendcookies'] = False
        self['storecookies'] = False
        self["status"] = False
        self["status_wait_seconds"] = 5
        self["fileoutput"] = []
        # Logger configurations
        self["text"] = {
            "filename": "linkchecker-out.txt",
            'colorparent':  "default",
            'colorurl':     "default",
            'colorname':    "default",
            'colorreal':    "cyan",
            'colorbase':    "purple",
            'colorvalid':   "bold;green",
            'colorinvalid': "bold;red",
            'colorinfo':    "default",
            'colorwarning': "bold;yellow",
            'colordltime':  "default",
            'colordlsize':  "default",
            'colorreset':   "default",
        }
        self['html'] = {
            "filename":        "linkchecker-out.html",
            'colorbackground': '#fff7e5',
            'colorurl':        '#dcd5cf',
            'colorborder':     '#000000',
            'colorlink':       '#191c83',
            'colorwarning':    '#e0954e',
            'colorerror':      '#db4930',
            'colorok':         '#3ba557',
        }
        self['gml'] = {
            "filename": "linkchecker-out.gml",
        }
        self['sql'] = {
            "filename": "linkchecker-out.sql",
            'separator': ';',
            'dbname': 'linksdb',
        }
        self['csv'] = {
            "filename": "linkchecker-out.csv",
            'separator': ';',
            "quotechar": '"',
        }
        self['blacklist'] = {
            "filename": "~/.linkchecker/blacklist",
        }
        self['xml'] = {
            "filename": "linkchecker-out.xml",
        }
        self['gxml'] = {
            "filename": "linkchecker-out.gxml",
        }
        self['dot'] = {
            "filename": "linkchecker-out.dot",
            "encoding": "ascii",
        }
        self['none'] = {}
        self['output'] = 'text'
        self['logger'] = None
        self["warningregex"] = None
        self["warnsizebytes"] = None
        self["nntpserver"] = os.environ.get("NNTP_SERVER", None)
        self["threads"] = 10
        # socket timeout in seconds
        self["timeout"] = 60
        self["checkhtml"] = False
        self["checkcss"] = False
        self["checkhtmlw3"] = False
        self["checkcssw3"] = False
        self["scanvirus"] = False
        self["clamavconf"] = clamav.canonical_clamav_conf()

    def init_logging (self, status_logger, debug=None, handler=None):
        """
        Load logging.conf file settings to set up the
        application logging (not to be confused with check loggers).
        When debug is not None it is expected to be a list of
        logger names for which debugging will be enabled.

        If no thread debugging is enabled, threading will be disabled.
        """
        filename = normpath(os.path.join(get_config_dir(), "logging.conf"))
        if os.path.isfile(filename):
            logging.config.fileConfig(filename)
        if handler is None:
            handler = ansicolor.ColoredStreamHandler(strm=sys.stderr)
        self.add_loghandler(handler)
        self.set_debug(debug)
        self.status_logger = status_logger

    def set_debug (self, debug):
        """Set debugging levels for configured loggers. The argument
        is a list of logger names to enable debug for."""
        self.set_loglevel(debug, logging.DEBUG)

    def add_loghandler (self, handler):
        """Add log handler to root logger LOG_ROOT and set formatting."""
        logging.getLogger(LOG_ROOT).addHandler(handler)
        if self['threads'] > 0:
            format = "%(levelname)s %(threadName)s %(message)s"
        else:
            format = "%(levelname)s %(message)s"
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

    def logger_new (self, loggertype, **kwargs):
        """
        Instantiate new logger and return it.
        """
        args = {}
        args.update(self[loggertype])
        args.update(kwargs)
        from ..logger import Loggers
        return Loggers[loggertype](**args)

    def logger_add (self, loggertype, loggerclass, loggerargs=None):
        """
        Add a new logger type to the known loggers.
        """
        if loggerargs is None:
            loggerargs = {}
        from ..logger import Loggers
        Loggers[loggertype] = loggerclass
        self[loggertype] = loggerargs

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
            cfiles.extend(get_standard_config_files())
        # weed out invalid files
        cfiles = [f for f in cfiles if os.path.isfile(f)]
        log.debug(LOG_CHECK, "reading configuration from %s", cfiles)
        confparse.LCConfigParser(self).read(cfiles)
        self.sanitize()

    def add_auth (self, user=None, password=None, pattern=None):
        """Add given authentication data."""
        if not user or not pattern:
            log.warn(LOG_CHECK,
            _("warning: missing user or URL pattern in authentication data."))
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

    def sanitize (self):
        "Make sure the configuration is consistent."
        if self["anchors"]:
            self.sanitize_anchors()
        if self['logger'] is None:
            self.sanitize_logger()
        if self['checkhtml']:
            self.sanitize_checkhtml()
        if self['checkcss']:
            self.sanitize_checkcss()
        if self['scanvirus']:
            self.sanitize_scanvirus()
        if self['storecookies']:
            self.sanitize_cookies()
        if self['loginurl']:
            self.sanitize_loginurl()
        self.sanitize_proxies()

    def sanitize_anchors (self):
        """Make anchor configuration consistent."""
        if not self["warnings"]:
            self["warnings"] = True
            from ..checker import Warnings
            self["ignorewarnings"] = Warnings.keys()
        if 'url-anchor-not-found' in self["ignorewarnings"]:
            self["ignorewarnings"].remove('url-anchor-not-found')

    def sanitize_logger (self):
        """Make logger configuration consistent."""
        if not self['output']:
            log.warn(LOG_CHECK, _("warning: activating text logger output."))
            self['output'] = 'text'
        self['logger'] = self.logger_new(self['output'])

    def sanitize_checkhtml (self):
        """Ensure HTML tidy is installed for checking HTML."""
        try:
            import tidy
        except ImportError:
            log.warn(LOG_CHECK,
                _("warning: tidy module is not available; " \
                 "download from http://utidylib.berlios.de/"))
            self['checkhtml'] = False

    def sanitize_checkcss (self):
        """Ensure cssutils is installed for checking CSS."""
        try:
            import cssutils
        except ImportError:
            log.warn(LOG_CHECK,
                _("warning: cssutils module is not available; " \
                 "download from http://cthedot.de/cssutils/"))
            self['checkcss'] = False

    def sanitize_scanvirus (self):
        """Ensure clamav is installed for virus checking."""
        try:
            clamav.init_clamav_conf(self['clamavconf'])
        except clamav.ClamavError:
            log.warn(LOG_CHECK,
                _("warning: Clamav could not be initialized"))
            self['scanvirus'] = False

    def sanitize_cookies (self):
        """Make cookie configuration consistent."""
        if not self['sendcookies']:
            log.warn(LOG_CHECK, _("warning: activating sendcookies " \
                                  "because storecookies is active."))
            self['sendcookies'] = True

    def sanitize_loginurl (self):
        """Make login configuration consistent."""
        url = self["loginurl"]
        disable = False
        if not self["loginpasswordfield"]:
            log.warn(LOG_CHECK,
            _("warning: no CGI password fieldname given for login URL."))
            disable = True
        if not self["loginuserfield"]:
            log.warn(LOG_CHECK,
            _("warning: no CGI user fieldname given for login URL."))
            disable = True
        if self.get_user_password(url) == (None, None):
            log.warn(LOG_CHECK,
            _("warning: no user/password authentication data found for login URL."))
            disable = True
        if not url.lower().startswith(("http:", "https:")):
            log.warn(LOG_CHECK, _("warning: login URL is not a HTTP URL."))
            disable = True
        urlparts = urlparse.urlsplit(url)
        if not urlparts[0] or not urlparts[1] or not urlparts[2]:
            log.warn(LOG_CHECK, _("warning: login URL is incomplete."))
            disable = True
        if disable:
            log.warn(LOG_CHECK,
              _("warning: disabling login URL %(url)s.") % {"url": url})
            self["loginurl"] = None
        elif not self['storecookies']:
            # login URL implies storing and sending cookies
            self['storecookies'] = self['sendcookies'] = True

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


def get_standard_config_files ():
    """Try to generate user configuration file from the system wide
    configuration.
    Returns tuple (system config file, user config file)."""
    # system wide config settings
    syspath = normpath(os.path.join(get_config_dir(), "linkcheckerrc"))
    # per user config settings
    userpath = normpath("~/.linkchecker/linkcheckerrc")
    if os.path.isfile(syspath) and not os.path.exists(userpath):
        # copy the system configuration to the user configuration
        try:
            userdir = os.path.dirname(userpath)
            if not os.path.exists(userdir):
                os.makedirs(userdir)
            shutil.copy(syspath, userpath)
        except StandardError, msg:
            log.warn(LOG_CHECK, "could not copy system config from %r to %r",
                     syspath, userpath)
    return (syspath, userpath)


def get_gconf_http_proxy ():
    """Return host:port for GConf HTTP proxy if found, else None."""
    try:
        import gconf
    except ImportError:
        return None
    client = gconf.client_get_default()
    if client.get_bool("/system/http_proxy/use_http_proxy"):
        host = client.get_string("/system/http_proxy/host")
        port = client.get_int("/system/http_proxy/port")
        if host:
            if not port:
                port = 8080
            return "%s:%d" % (host, port)
    return None


def get_gconf_ftp_proxy ():
    """Return host:port for GConf FTP proxy if found, else None."""
    try:
        import gconf
    except ImportError:
        return None
    client = gconf.client_get_default()
    host = client.get_string("/system/proxy/ftp_host")
    port = client.get_int("/system/proxy/ftp_port")
    if host:
        if not port:
            port = 8080
        return "%s:%d" % (host, port)
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
    except:
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
    except:
        pass


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
