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

import ConfigParser
import sys
import os
import logging
import logging.config
import re
import urllib

import _linkchecker_configdata
import linkcheck
import linkcheck.log
import linkcheck.containers
try:
    import GeoIP
    _has_geoip = True
except ImportError:
    _has_geoip = False

Version = _linkchecker_configdata.version
AppName = u"LinkChecker"
App = AppName+u" "+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(u' ', u'&nbsp;')
Copyright = u"Copyright (C) 2000-2005 "+Author
HtmlCopyright = u"Copyright &copy; 2000-2005 "+HtmlAuthor
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
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = []
        self["proxy"] = urllib.getproxies()
        self["recursionlevel"] = -1
        self["wait"] = 0
        self['cookies'] = False
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
        self.init_geoip()

    def init_geoip (self):
        """
        If GeoIP.dat file is found, initialize a standard geoip DB and
        store it in self["geoip"]; else this value will be None.
        """
        geoip_dat = "/usr/share/GeoIP/GeoIP.dat"
        if _has_geoip and os.path.exists(geoip_dat):
            self["geoip"] = GeoIP.open(geoip_dat, GeoIP.GEOIP_STANDARD)
        else:
            self["geoip"] = None

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

    def write (self, filename="~/.linkchecker/linkcheckerrc"):
        filename = normpath(filename)
        assert linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "write configuration into %s", filename)
        fp = open(filename, 'w')
        self.write_output_config(fp)
        self.write_checking_config(fp)
        self.write_authentication_config(fp)
        self.write_filtering_config(fp)
        fp.close()

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
        self.read_config(cfiles)
        # re-init logger
        self['logger'] = self.logger_new('text')

    def read_config (self, files):
        """
        Read all the configuration parameters from the given files.
        """
        assert linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "reading configuration from %s", files)
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
            return
        self.read_output_config(cfgparser)
        self.read_checking_config(cfgparser)
        self.read_authentication_config(cfgparser)
        self.read_filtering_config(cfgparser)

    def read_output_config (self, cfgparser):
        """
        Read configuration options in section "output".
        """
        section = "output"
        for key in linkcheck.Loggers.iterkeys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try:
                        self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error, msg:
                        assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
                try:
                    self[key]['parts'] = [f.strip() for f in \
                         cfgparser.get(key, 'parts').split(',')]
                except ConfigParser.Error, msg:
                    assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = True
                self["warnings"] = True
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            if cfgparser.getboolean(section, "quiet"):
                self['logger'] = self.logger_new('none')
                self['quiet'] = True
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["status"] = cfgparser.getboolean(section, "status")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            logger = cfgparser.get(section, "log")
            if linkcheck.Loggers.has_key(logger):
                self['logger'] = self.logger_new(logger)
            else:
                linkcheck.log.warn(_("invalid log option %r"), logger)
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            filelist = cfgparser.get(section, "fileoutput").split(",")
            for arg in filelist:
                arg = arg.strip()
                # no file output for the blacklist and none Logger
                if linkcheck.Loggers.has_key(arg) and \
                   arg not in ["blacklist", "none"]:
                    self['fileoutput'].append(
                                     self.logger_new(arg, fileoutput=1))
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["interactive"] = cfgparser.getboolean(section, "interactive")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_checking_config (self, cfgparser):
        """
        Read configuration options in section "checking".
        """
        section = "checking"
        try:
            num = cfgparser.getint(section, "threads")
            self['threads'] = num
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["debug"] = cfgparser.get(section, "debug")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = cfgparser.getint(section, "recursionlevel")
            self["recursionlevel"] = num
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            arg = cfgparser.get(section, "warningregex")
            if arg:
                try:
                    self["warningregex"] = re.compile(arg)
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("syntax error in warningregex %r: %s\n"), arg, msg)
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnsizebytes"] = int(cfgparser.get(section,
                                                      "warnsizebytes"))
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchorcaching"] = cfgparser.getboolean(section,
                                    "anchorcaching")
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            i = 1
            while 1:
                arg = cfgparser.get(section, "noproxyfor%d" % i)
                try:
                    arg = re.compile(arg)
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("syntax error in noproxyfor%d %r: %s"), i, arg, msg)
                self["noproxyfor"].append(arg)
                i += 1
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_authentication_config (self, cfgparser):
        """
        Read configuration options in section "authentication".
        """
        section = "authentication"
        try:
            i = 1
            while 1:
                auth = cfgparser.get(section, "entry%d" % i).split()
                if len(auth) != 3:
                    break
                try:
                    auth[0] = re.compile(auth[0])
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("syntax error in entry%d %r: %s"), i, auth[0], msg)
                self["authentication"].insert(0, {'pattern': auth[0],
                                                  'user': auth[1],
                                                  'password': auth[2]})
                i += 1
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_filtering_config (self, cfgparser):
        """
        Read configuration options in section "filtering".
        """
        section = "filtering"
        try:
            i = 1
            while 1:
                val = cfgparser.get(section, "nofollow%d" % i)
                pat = linkcheck.get_link_pat(val, strict=0)
                self["externlinks"].append(pat)
                i += 1
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self['ignorewarnings'] = [f.strip() for f in \
                 cfgparser.get(section, 'ignorewarnings').split(',')]
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            i = 1
            while 1:
                # XXX backwards compatibility: split and ignore second part
                val = cfgparser.get(section, "ignore%d" % i).split()[0]
                pat = linkcheck.get_link_pat(val, strict=1)
                self["externlinks"].append(pat)
                i += 1
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["internlinks"].append(
               linkcheck.get_link_pat(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error, msg:
            assert linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def write_boolean_config (self, fp, boolopts):
        """
        Write a boolean value into the config file.
        """
        for opt in boolopts:
            if self[opt]:
                fp.write("%s=1%s" % (opt, os.linesep))

    def write_output_config (self, fp):
        """
        Write configuration options in section "output".
        """
        fp.write("[output]%s" % os.linesep)
        # XXX write logger output config
        # XXX write fileoutput config
        boolopts = ("verbose", "warnings", "quiet", "status", "interactive")
        self.write_boolean_config(fp, boolopts)

    def write_checking_config (self, fp):
        """
        Write configuration options in section "checking".
        """
        fp.write("[checking]%s" % os.linesep)
        # XXX todo

    def write_authentication_config (self, fp):
        """
        Write configuration options in section "authentication".
        """
        fp.write("[authentication]%s" % os.linesep)
        # XXX todo

    def write_filtering_config (self, fp):
        """
        Write configuration options in section "filtering".
        """
        fp.write("[filtering]%s" % os.linesep)
        # XXX todo
