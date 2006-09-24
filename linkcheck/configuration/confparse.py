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
"""Parse configuration files"""

import ConfigParser
import re
import linkcheck.log

class LCConfigParser (ConfigParser.RawConfigParser, object):
    """
    Parse a LinkChecker configuration file.
    """

    def __init__ (self, config):
        super(LCConfigParser, self).__init__()
        self.config = config

    def read (self, files):
        """
        Read settings from given config files.

        @raises: LinkCheckerError on syntax errors in the config file(s)
        """
        try:
            super(LCConfigParser, self).read(files)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
            return
        # Read all the configuration parameters from the given files.
        self.read_output_config()
        self.read_checking_config()
        self.read_authentication_config()
        self.read_filtering_config()
        # re-init logger
        self.config['logger'] = self.config.logger_new('text')

    def read_output_config (self):
        """
        Read configuration options in section "output".
        """
        section = "output"
        for key in linkcheck.Loggers.iterkeys():
            if self.has_section(key):
                for opt in self.options(key):
                    try:
                        self.config[key][opt] = self.get(key, opt)
                    except ConfigParser.Error, msg:
                        assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
                try:
                    self.config[key]['parts'] = [f.strip() for f in \
                         self.get(key, 'parts').split(',')]
                except ConfigParser.Error, msg:
                    assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["warnings"] = self.getboolean(section, "warnings")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            if self.getboolean(section, "verbose"):
                self.config["verbose"] = True
                self.config["warnings"] = True
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            if self.getboolean(section, "quiet"):
                self.config['logger'] = self.config.logger_new('none')
                self.config['quiet'] = True
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["status"] = self.getboolean(section, "status")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            logger = self.get(section, "log")
            if linkcheck.Loggers.has_key(logger):
                self.config['logger'] = self.config.logger_new(logger)
            else:
                linkcheck.log.warn(_("invalid log option %r"), logger)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            filelist = self.get(section, "fileoutput").split(",")
            for arg in filelist:
                arg = arg.strip()
                # no file output for the blacklist and none Logger
                if linkcheck.Loggers.has_key(arg) and \
                   arg not in ["blacklist", "none"]:
                    self.config['fileoutput'].append(
                                  self.config.logger_new(arg, fileoutput=1))
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["interactive"] = self.getboolean(section, "interactive")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_checking_config (self):
        """
        Read configuration options in section "checking".
        """
        section = "checking"
        try:
            num = self.getint(section, "threads")
            self.config['threads'] = max(0, num)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = self.getint(section, "timeout")
            if num < 0:
                raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                    _("invalid negative value for timeout: %d\n"), num)
            self.config['threads'] = num
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["anchors"] = self.getboolean(section, "anchors")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["debug"] = self.get(section, "debug")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = self.getint(section, "recursionlevel")
            self.config["recursionlevel"] = num
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            arg = self.get(section, "warningregex")
            if arg:
                try:
                    self.config["warningregex"] = re.compile(arg)
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                   _("syntax error in warningregex %(regex)r: %(msg)s\n") % \
                   {"regex": arg, "msg": msg})
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["warnsizebytes"] = int(self.get(section,
                                                      "warnsizebytes"))
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["nntpserver"] = self.get(section, "nntpserver")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["anchorcaching"] = self.getboolean(section,
                                    "anchorcaching")
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            value = self.get(section, "noproxyfor")
            for line in value.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    arg = re.compile(arg)
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                   _("syntax error in noproxyfor %(line)r") % {"line": line})
                self.config["noproxyfor"].append(arg)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            # XXX backward compatibility
            i = 1
            while 1:
                arg = self.get(section, "noproxyfor%d" % i)
                linkcheck.log.warn(linkcheck.LOG_CHECK,
                  _("the noproxyfor%(num)d syntax is deprecated; use" \
                    "the new multiline configuration syntax") % {"num": i})
                try:
                    arg = re.compile(arg)
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                   _("syntax error in noproxyfor%(num)d %(arg)r: %(msg)s") % \
                    {"num": i, "arg": arg, "msg": msg})
                self.config["noproxyfor"].append(arg)
                i += 1
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            num = self.getint(section, "maxqueuesize")
            self.config["maxqueuesize"] = num
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_authentication_config (self):
        """
        Read configuration options in section "authentication".
        """
        section = "authentication"
        try:
            arg = self.get(section, "entry")
            for line in arg.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                auth = line.split()
                if len(auth) != 3:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("missing auth part in entry %(line)r") % \
                       {"line": line})
                try:
                    auth[0] = re.compile(auth[0])
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("syntax error in entry %(line)r: %(msg)s") % \
                       {"line": line, "msg": msg})
                self.config["authentication"].insert(0, {'pattern': auth[0],
                                                  'user': auth[1],
                                                  'password': auth[2]})
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            # XXX backward compatibility
            i = 1
            while 1:
                auth = self.get(section, "entry%d" % i).split()
                linkcheck.log.warn(linkcheck.LOG_CHECK,
                  _("the entry%(num)d syntax is deprecated; use" \
                    "the new multiline configuration syntax") % {"num": i})
                if len(auth) != 3:
                    break
                try:
                    auth[0] = re.compile(auth[0])
                except re.error, msg:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("syntax error in entry%(num)d %(arg)r: %(msg)s") % \
                       {"num": i, "arg": auth[0], "msg": msg})
                self.config["authentication"].insert(0, {'pattern': auth[0],
                                                  'user': auth[1],
                                                  'password': auth[2]})
                i += 1
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

    def read_filtering_config (self):
        """
        Read configuration options in section "filtering".
        """
        section = "filtering"
        try:
            arg = self.get(section, "nofollow")
            for line in arg.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                pat = linkcheck.get_link_pat(line, strict=0)
                self.config["externlinks"].append(pat)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            # XXX backward compatibility
            i = 1
            while 1:
                val = self.get(section, "nofollow%d" % i)
                linkcheck.log.warn(linkcheck.LOG_CHECK,
                  _("the nofollow%(num)d syntax is deprecated; use" \
                    "the new multiline configuration syntax") % {"num": i})
                pat = linkcheck.get_link_pat(val, strict=0)
                self.config["externlinks"].append(pat)
                i += 1
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config['ignorewarnings'] = [f.strip() for f in \
                 self.get(section, 'ignorewarnings').split(',')]
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            arg = self.get(section, "ignore")
            for line in arg.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                pat = linkcheck.get_link_pat(line, strict=1)
                self.config["externlinks"].append(pat)
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            # XXX backward compatibility
            i = 1
            while 1:
                # XXX backwards compatibility: split and ignore second part
                val = self.get(section, "ignore%d" % i).split()[0]
                linkcheck.log.warn(linkcheck.LOG_CHECK,
                  _("the ignore%(num)d syntax is deprecated; use" \
                    "the new multiline configuration syntax") % {"num": i})
                pat = linkcheck.get_link_pat(val, strict=1)
                self.config["externlinks"].append(pat)
                i += 1
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)
        try:
            self.config["internlinks"].append(
               linkcheck.get_link_pat(self.get(section, "internlinks")))
        except ConfigParser.Error, msg:
            assert None == linkcheck.log.debug(linkcheck.LOG_CHECK, msg)

