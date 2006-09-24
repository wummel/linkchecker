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
Store metadata and options.
"""

import sys
import os
import logging.config
import urllib
import _linkchecker_configdata
import linkcheck.log
import linkcheck.containers
import confparse

Version = _linkchecker_configdata.version
AppName = u"LinkChecker"
App = AppName+u" "+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(u' ', u'&nbsp;')
Copyright = u"Copyright (C) 2000-2006 "+Author
HtmlCopyright = u"Copyright &copy; 2000-2006 "+HtmlAuthor
AppInfo = App+u"              "+Copyright
HtmlAppInfo = App+u", "+HtmlCopyright
Url = _linkchecker_configdata.url
Email = _linkchecker_configdata.author_email
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
        self['debug'] = False
        self['trace'] = False
        self["verbose"] = False
        self["warnings"] = True
        self["ignorewarnings"] = []
        self['quiet'] = False
        self["anchors"] = False
        self["anchorcaching"] = True
        self["externlinks"] = []
        self["internlinks"] = []
        self["noproxyfor"] = []
        self["interactive"] = False
        self["maxqueuesize"] = 0
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = []
        self["proxy"] = urllib.getproxies()
        self["recursionlevel"] = -1
        self["wait"] = 0
        self['sendcookies'] = False
        self['storecookies'] = False
        self["status"] = False
        self["fileoutput"] = []
        # Logger configurations
        self["text"] = {
            "filename": "linkchecker-out.txt",
            'colorparent':  "default",
            'colorurl':     "default",
            'colorname':    "default",
            'colorreal':    "default",
            'colorbase':    "default",
            'colorvalid':   "default",
            'colorinvalid': "default",
            'colorinfo':    "default",
            'colorwarning': "default",
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
            'separator': ',',
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
        self['logger'] = self.logger_new('text')
        self["warningregex"] = None
        self["warnsizebytes"] = None
        self["nntpserver"] = os.environ.get("NNTP_SERVER", None)
        self["threads"] = 10
        # socket timeout in seconds
        self["timeout"] = 60

    def init_logging (self, debug=None):
        """
        Load logging.conf file settings to set up the
        application logging (not to be confused with check loggers).
        When debug is not None it is expected to be a list of
        logger names for which debugging will be enabled.

        If no thread debugging is enabled, threading will be disabled.
        """
        config_dir = _linkchecker_configdata.config_dir
        filename = normpath(os.path.join(config_dir, "logging.conf"))
        logging.config.fileConfig(filename)
        handler = linkcheck.ansicolor.ColoredStreamHandler(strm=sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logging.getLogger(linkcheck.LOG).addHandler(handler)
        if debug:
            self['debug'] = True
            # disable threading if no thread debugging
            if "thread" not in debug:
                self['threads'] = 0
            # set debugging on given logger names
            if 'all' in debug:
                debug = linkcheck.lognames.keys()
            for name in debug:
                logname = linkcheck.lognames[name]
                logging.getLogger(logname).setLevel(logging.DEBUG)

    def logger_new (self, loggertype, **kwargs):
        """
        Instantiate new logger and return it.
        """
        args = {}
        args.update(self[loggertype])
        args.update(kwargs)
        return linkcheck.Loggers[loggertype](**args)

    def logger_add (self, loggertype, loggerclass, loggerargs=None):
        """
        Add a new logger type to the known loggers.
        """
        if loggerargs is None:
            loggerargs = {}
        linkcheck.Loggers[loggertype] = loggerclass
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
            # system wide config settings
            config_dir = _linkchecker_configdata.config_dir
            path = normpath(os.path.join(config_dir, "linkcheckerrc"))
            cfiles.append(path)
            # per user config settings
            path = normpath("~/.linkchecker/linkcheckerrc")
            cfiles.append(path)
        # weed out invalid files
        cfiles = [f for f in cfiles if os.path.isfile(f)]
        assert None == linkcheck.log.debug(linkcheck.LOG_CHECK,
            "reading configuration from %s", cfiles)
        confparse.LCConfigParser(self).read(cfiles)
