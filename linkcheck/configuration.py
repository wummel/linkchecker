# -*- coding: iso-8859-1 -*-
"""store metadata and options"""
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

import ConfigParser
import sys
import os
import logging
import logging.config
import re
import Cookie
import sets
import urllib
try:
    import threading
except ImportError:
    import dummy_threading as threading

import _linkchecker_configdata
import linkcheck
import linkcheck.log
import linkcheck.containers
import linkcheck.threader

from linkcheck.i18n import _

Version = _linkchecker_configdata.version
AppName = "LinkChecker"
App = AppName+" "+Version
Author =  _linkchecker_configdata.author
HtmlAuthor = Author.replace(' ', '&nbsp;')
Copyright = "Copyright © 2000-2004 "+Author
HtmlCopyright = "Copyright &copy; 2000-2004 "+HtmlAuthor
AppInfo = App+"              "+Copyright
HtmlAppInfo = App+", "+HtmlCopyright
Url = _linkchecker_configdata.url
Email = _linkchecker_configdata.author_email
UserAgent = "%s/%s (%s; %s)" % (AppName, Version, Url, Email)
Freeware = AppName+""" comes with ABSOLUTELY NO WARRANTY!
This is free software, and you are welcome to redistribute it
under certain conditions. Look at the file `LICENSE' within this
distribution."""

MAX_URL_CACHE = 30000
MAX_ROBOTS_TXT_CACHE = 5000
MAX_COOKIES_CACHE = 500


def norm (path):
    """norm given system path with all available norm funcs in os.path"""
    return os.path.normcase(os.path.normpath(os.path.expanduser(path)))


def _check_morsel (m, host, path):
    """check given cookie morsel against the desired host and path"""
    # check domain (if its stored)
    if m["domain"] and not host.endswith(m["domain"]):
        return None
    # check path (if its stored)
    if m["path"] and not path.startswith(m["path"]):
        return None
    # check expiry date (if its stored)
    if m["expires"]:
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Cookie expires %s",
                            m["expires"])
        # XXX
    return m.output(header='').strip()


# dynamic options
class Configuration (dict):
    """Storage for configuration options. Options can both be given from
       the command line as well as from configuration files.
       With different configuration instances, one can run several
       separate checker threads with different configurations.
    """

    def __init__ (self):
        """Initialize the default options"""
        super(Configuration, self).__init__()
        self.reset()
        # we use "reduceCount" to delay the calling of
        # threader.reduceThreads() because we would call it too often.
        # Therefore we count this variable up to 5 and then we call
        # reduceThreads(). Ok, this is a hack but ItWorksForMe(tm).
        self.reduceCount = 0

    def reset (self):
        """Reset to default values"""
        self['linknumber'] = 0
        self["verbose"] = False
        self["warnings"] = False
        self["anchors"] = False
        self["anchorcaching"] = True
        self["externlinks"] = []
        self["internlinks"] = []
        self["denyallow"] = False
        self["interactive"] = False
        # on ftp, password is set by Pythons ftplib
        self["authentication"] = [
            {'pattern': re.compile(r'^.+'),
             'user': 'anonymous',
             'password': '',
            }]
        self["proxy"] = urllib.getproxies()
        self["recursionlevel"] = -1
        self["wait"] = 0
        self['cookies'] = False
        self["strict"] = False
        self["status"] = False
        self["fileoutput"] = []
        # Logger configurations
        self["text"] = {
            "filename": "linkchecker-out.txt",
        }
        self['html'] = {
            "filename":        "linkchecker-out.html",
            'colorbackground': '#fff7e5',
            'colorurl':        '#dcd5cf',
            'colorborder':     '#000000',
            'colorlink':       '#191c83',
            'tablewarning':    '<td bgcolor="#e0954e">',
            'tableerror':      '<td bgcolor="#db4930">',
            'tableok':         '<td bgcolor="#3ba557">',
        }
        self['colored'] = {
            "filename":     "linkchecker-out.ansi",
            'colorparent':  "white",
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
        self['gml'] = {
            "filename":     "linkchecker-out.gml",
        }
        self['sql'] = {
            "filename":     "linkchecker-out.sql",
            'separator': ';',
            'dbname': 'linksdb',
        }
        self['csv'] = {
            "filename":     "linkchecker-out.csv",
            'separator': ';',
        }
        self['blacklist'] = {
            "filename":     "~/.linkchecker_blacklist",
        }
        self['xml'] = {
            "filename":     "linkchecker-out.xml",
        }
        self['none'] = {}
        self['logger'] = self.logger_new('text')
        self.logger_lock = threading.Lock()
        self["quiet"] = False
        self["warningregex"] = None
        self["warnsizebytes"] = None
        self["nntpserver"] = os.environ.get("NNTP_SERVER", None)
        self["threads"] = True
        self.threader = linkcheck.threader.Threader()
        self.set_threads(10)
        self.url_seen = sets.Set()
        self.url_seen_lock = threading.Lock()
        self.url_cache = linkcheck.containers.LRU(MAX_URL_CACHE)
        self.url_cache_lock = threading.Lock()
        self.robots_txt_cache = linkcheck.containers.LRU(MAX_ROBOTS_TXT_CACHE)
        self.robots_txt_cache_lock = threading.Lock()
        self.urls = []
        self.url_counter = 0
        self.urls_lock = threading.Lock()
        # basic data lock (eg for cookies, link numbers etc.)
        self.data_lock = threading.Lock()
        self.cookies = linkcheck.containers.LRU(MAX_COOKIES_CACHE)

    def init_logging (self, debug=None):
        """Load linkcheck/logging.conf file settings to set up the
           application logging (not to be confused with check loggers).
           When debug is not None it is expected to be a list of
           logger names for which debugging will be enabled.
        """
        config_dir = _linkchecker_configdata.config_dir
        filename = norm(os.path.join(config_dir, "logging.conf"))
        logging.config.fileConfig(filename)
        handler = linkcheck.ansicolor.ColoredStreamHandler(strm=sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logging.getLogger(linkcheck.LOG).addHandler(handler)
        if debug is not None:
            self['debug'] = True
            # debugging disables threading
            self.set_threads(0)
            # set debugging on given logger names
            if 'all' in debug:
                debug = linkcheck.lognames.values()
            for name in debug:
                logging.getLogger(name).setLevel(logging.DEBUG)

    def set_threads (self, num):
        """set number of checker threads to start"""
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "set threading with %d threads", num)
        self.threader.threads_max = num
        if num > 0:
            sys.setcheckinterval(50)
        else:
            sys.setcheckinterval(100)

    def logger_new (self, loggertype, **kwargs):
        """instantiate new logger and return it"""
        args = {}
        args.update(self[loggertype])
        args.update(kwargs)
        return linkcheck.Loggers[loggertype](**args)

    def logger_add (self, loggertype, loggerclass, loggerargs=None):
        """add a new logger type to the known loggers"""
        if loggerargs is None:
            loggerargs = {}
        linkcheck.Loggers[loggertype] = loggerclass
        self[loggertype] = loggerargs

    def logger_start_output (self):
        """start output of all configured loggers"""
        if not self["quiet"]:
            self["logger"].start_output()
        for logger in self["fileoutput"]:
            logger.start_output()

    def logger_new_url (self, url):
        """send new url to all configured loggers"""
        self.logger_lock.acquire()
        try:
            if not self["quiet"]:
                self["logger"].new_url(url)
            for log in self["fileoutput"]:
                log.new_url(url)
        finally:
            self.logger_lock.release()

    def logger_end_output (self):
        """end output of all configured loggers"""
        if not self["quiet"]:
            self["logger"].end_output(linknumber=self['linknumber'])
        for logger in self["fileoutput"]:
            logger.end_output(linknumber=self['linknumber'])

    def increment_linknumber (self):
        """increment stored link number thread-safe by one"""
        try:
            self.data_lock.acquire()
            self['linknumber'] += 1
        finally:
            self.data_lock.release()

    def has_more_urls (self):
        """return True if more urls need to be checked"""
        return self.urls

    def finished (self):
        """return True if checking is finished"""
        return self.threader.finished() and not self.urls

    def finish (self):
        """remove stopped thread from thread list"""
        self.threader.finish()

    def append_url (self, url_data):
        """add new url to list of urls to check"""
        self.urls_lock.acquire()
        try:
            # check syntax
            if not url_data.check_syntax():
                return
            # check the cache
            if not url_data.check_cache():
                return
            self.url_counter += 1
            if self.url_counter == 1000:
                self.url_counter = 0
                self.filter_url_queue()
            self.urls.append(url_data)
        finally:
            self.urls_lock.release()

    def filter_url_queue (self):
        """remove already cached urls from queue"""
        # note: url lock must be acquired
        olen = len(self.urls)
        self.urls = [ u for u in self.urls if u.check_cache() ]
        removed = olen - len(self.urls)
        print >> sys.stderr, \
          _("removed %d cached urls from incoming queue")%removed

    def get_url (self):
        """get first url in queue and return it"""
        self.urls_lock.acquire()
        try:
            u = self.urls[0]
            del self.urls[0]
            return u
        finally:
            self.urls_lock.release()

    def check_url (self, url):
        """start new thread checking the given url"""
        self.threader.start_thread(url.check, ())

    def url_seen_has_key (self, key):
        """thread-safe visited url cache lookup function"""
        self.url_seen_lock.acquire()
        try:
            return key in self.url_seen
        finally:
            self.url_seen_lock.release()

    def url_seen_set (self, key):
        """thread-safe visited url cache setter function"""
        self.url_seen_lock.acquire()
        try:
            self.url_seen.add(key)
        finally:
            self.url_seen_lock.release()

    def url_cache_has_key (self, key):
        """thread-safe checked url cache lookup function"""
        self.url_cache_lock.acquire()
        try:
            return key in self.url_cache
        finally:
            self.url_cache_lock.release()

    def url_cache_get (self, key):
        """thread-safe checked url cache getter function"""
        self.url_cache_lock.acquire()
        try:
            return self.url_cache[key]
        finally:
            self.url_cache_lock.release()

    def url_cache_set (self, key, val):
        """thread-safe checked url cache setter function"""
        self.url_cache_lock.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CHECK, "caching %r", key)
            self.url_cache[key] = val
        finally:
            self.url_cache_lock.release()

    def robots_txt_cache_has_key (self, key):
        """thread-safe robots.txt cache lookup function"""
        self.robots_txt_cache_lock.acquire()
        try:
            return self.robots_txt_cache.has_key(key)
        finally:
            self.robots_txt_cache_lock.release()

    def robots_txt_cache_get (self, key):
        """thread-safe robots.txt cache getter function"""
        self.robots_txt_cache_lock.acquire()
        try:
            return self.robots_txt_cache[key]
        finally:
            self.robots_txt_cache_lock.release()

    def robots_txt_cache_set (self, key, val):
        """thread-safe robots.txt cache setter function"""
        self.robots_txt_cache_lock.acquire()
        try:
            self.robots_txt_cache[key] = val
        finally:
            self.robots_txt_cache_lock.release()

    def store_cookies (self, headers, host):
        """thread-safe cookie cache setter function"""
        self.data_lock.acquire()
        try:
            output = []
            for h in headers.getallmatchingheaders("Set-Cookie"):
                output.append(h)
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Store Cookie %s", h)
                c = self.cookies.setdefault(host, Cookie.SimpleCookie())
                c.load(h)
            return output
        finally:
            self.data_lock.release()

    def get_cookies (self, host, path):
        """thread-safe cookie cache getter function"""
        self.data_lock.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "Get Cookie %s (%s)", host, path)
            if not self.cookies.has_key(host):
                return []
            cookievals = []
            for m in self.cookies[host].values():
                val = _check_morsel(m, host, path)
                if val:
                    cookievals.append(val)
            return cookievals
        finally:
            self.data_lock.release()

    def read (self, files=None):
        """read settings from given config files"""
        if files is None:
            cfiles = []
        else:
            cfiles = files[:]
        if not cfiles:
            # system wide config settings
            config_dir = _linkchecker_configdata.config_dir
            cfiles.append(norm(os.path.join(config_dir, "linkcheckerrc")))
            # per user config settings
            cfiles.append(norm("~/.linkcheckerrc"))
        self.read_config(cfiles)

    def read_config (self, files):
        """read all the configuration parameters from the given files"""
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "reading configuration from %s", files)
        try:
            cfgparser = ConfigParser.ConfigParser()
            cfgparser.read(files)
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
            return
        self.read_output_config(cfgparser)
        self.read_checking_config(cfgparser)
        self.read_authentication_config(cfgparser)
        self.read_filtering_config(cfgparser)

    def read_output_config (self, cfgparser):
        """read configuration options in section "output"."""
        section = "output"
        for key in linkcheck.Loggers.keys():
            if cfgparser.has_section(key):
                for opt in cfgparser.options(key):
                    try:
                        self[key][opt] = cfgparser.get(key, opt)
                    except ConfigParser.Error, msg:
                        linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
                try:
                    self[key]['fields'] = [f.strip() \
                            for f in cfgparser.get(key, 'fields').split(',')]
                except ConfigParser.Error, msg:
                    linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            logger = cfgparser.get(section, "log")
            if linkcheck.Loggers.has_key(logger):
                self['logger'] = self.logger_new(logger)
            else:
                linkcheck.log.warn(_("invalid log option %r"), logger)
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            if cfgparser.getboolean(section, "verbose"):
                self["verbose"] = True
                self["warnings"] = True
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["quiet"] = cfgparser.getboolean(section, "quiet")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["status"] = cfgparser.getboolean(section, "status")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnings"] = cfgparser.getboolean(section, "warnings")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
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
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["interactive"] = cfgparser.getboolean(section, "interactive")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_checking_config (self, cfgparser):
        """read configuration options in section "checking"."""
        section = "checking"
        try:
            num = cfgparser.getint(section, "threads")
            self.set_threads(num)
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchors"] = cfgparser.getboolean(section, "anchors")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["debug"] = cfgparser.get(section, "debug")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = cfgparser.getint(section, "recursionlevel")
            self["recursionlevel"] = num
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["strict"] = cfgparser.getboolean(section, "strict")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            wr = cfgparser.get(section, "warningregex")
            if wr:
                self["warningregex"] = re.compile(wr)
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["warnsizebytes"] = int(cfgparser.get(section,
                                                      "warnsizebytes"))
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["nntpserver"] = cfgparser.get(section, "nntpserver")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["anchorcaching"] = cfgparser.getboolean(section,
                                    "anchorcaching")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_authentication_config (self, cfgparser):
        """read configuration options in section "authentication"."""
        section = "authentication"
        try:
            i = 1
            while 1:
                auth = cfgparser.get(section, "entry%d" % i).split()
                if len(auth)!=3:
                    break
                auth[0] = re.compile(auth[0])
                self["authentication"].insert(0, {'pattern': auth[0],
                                                  'user': auth[1],
                                                  'password': auth[2]})
                i += 1
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_filtering_config (self, cfgparser):
        """read configuration options in section "filtering"."""
        section = "filtering"
        try:
            i = 1
            while 1:
                ctuple = cfgparser.get(section, "extern%d" % i).split()
                if len(ctuple)!=2:
                    linkcheck.log.error(
                               _("extern%d: syntax error %s\n")%(i, ctuple))
                    break
                self["externlinks"].append(
                    linkcheck.get_link_pat(ctuple[0], strict=int(ctuple[1])))
                i += 1
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["internlinks"].append(
               linkcheck.get_link_pat(cfgparser.get(section, "internlinks")))
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self["denyallow"] = cfgparser.getboolean(section, "denyallow")
        except ConfigParser.Error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
