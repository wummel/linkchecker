# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2010 Bastian Kleineidam
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
    get_config_dir)
from . import confparse

Version = configdata.version
AppName = configdata.appname
App = AppName+u" "+Version
Author = configdata.author
HtmlAuthor = Author.replace(u' ', u'&nbsp;')
Copyright = u"Copyright (C) 2000-2010 "+Author
HtmlCopyright = u"Copyright &copy; 2000-2010 "+HtmlAuthor
AppInfo = App+u"              "+Copyright
HtmlAppInfo = App+u", "+HtmlCopyright
Url = configdata.url
SupportUrl = u"http://sourceforge.net/projects/linkchecker/support"
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
        self["interactive"] = False
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

    def sanitize_anchors (self):
        if not self["warnings"]:
            self["warnings"] = True
            from ..checker import Warnings
            self["ignorewarnings"] = Warnings.keys()
        if 'url-anchor-not-found' in self["ignorewarnings"]:
            self["ignorewarnings"].remove('url-anchor-not-found')

    def sanitize_logger (self):
        if not self['output']:
            log.warn(LOG_CHECK, _("warning: activating text logger output."))
            self['output'] = 'text'
        self['logger'] = self.logger_new(self['output'])

    def sanitize_checkhtml (self):
        try:
            import tidy
        except ImportError:
            log.warn(LOG_CHECK,
                _("warning: tidy module is not available; " \
                 "download from http://utidylib.berlios.de/"))
            self['checkhtml'] = False

    def sanitize_checkcss (self):
        try:
            import cssutils
        except ImportError:
            log.warn(LOG_CHECK,
                _("warning: cssutils module is not available; " \
                 "download from http://cthedot.de/cssutils/"))
            self['checkcss'] = False

    def sanitize_scanvirus (self):
        try:
            clamav.init_clamav_conf(self['clamavconf'])
        except clamav.ClamavError:
            log.warn(LOG_CHECK,
                _("warning: Clamav could not be initialized"))
            self['scanvirus'] = False

    def sanitize_cookies (self):
        if not self['sendcookies']:
            log.warn(LOG_CHECK, _("warning: activating sendcookies " \
                                  "because storecookies is active."))
            self['sendcookies'] = True

    def sanitize_loginurl (self):
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
