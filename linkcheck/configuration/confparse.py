# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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


def read_multiline (value):
    """Helper function reading multiline values."""
    for line in value.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        yield line


class LCConfigParser (ConfigParser.RawConfigParser, object):
    """
    Parse a LinkChecker configuration file.
    """

    def __init__ (self, config):
        super(LCConfigParser, self).__init__()
        self.config = config

    def read (self, files):
        """Read settings from given config files.

        @raises: LinkCheckerError on syntax errors in the config file(s)
        """
        try:
            super(LCConfigParser, self).read(files)
            # Read all the configuration parameters from the given files.
            self.read_output_config()
            self.read_checking_config()
            self.read_authentication_config()
            self.read_filtering_config()
        except Exception, msg:
            raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
              "Error parsing configuration: %s", str(msg))

    def read_output_config (self):
        """Read configuration options in section "output"."""
        section = "output"
        for key in linkcheck.Loggers.iterkeys():
            if self.has_section(key):
                for opt in self.options(key):
                    self.config[key][opt] = self.get(key, opt)
                if self.has_option(key, 'parts'):
                    val = self.get(key, 'parts')
                    parts = [f.strip() for f in val.split(',')]
                    self.config[key]['parts'] = parts
        if self.has_option(section, "warnings"):
            self.config["warnings"] = self.getboolean(section, "warnings")
        if self.has_option(section, "verbose"):
            if self.getboolean(section, "verbose"):
                self.config["verbose"] = True
                self.config["warnings"] = True
        if self.has_option(section, "quiet"):
            if self.getboolean(section, "quiet"):
                self.config['output'] = 'none'
                self.config['quiet'] = True
        if self.has_option(section, "debug"):
            val = self.get(section, "debug")
            parts = [f.strip() for f in val.split(',')]
            self.config.set_debug(parts)
        if self.has_option(section, "status"):
            self.config["status"] = self.getboolean(section, "status")
        if self.has_option(section, "log"):
            val = self.get(section, "log").strip()
            self.config['output'] = val
        if self.has_option(section, "fileoutput"):
            filelist = self.get(section, "fileoutput").split(",")
            for val in filelist:
                val = val.strip()
                # no file output for the blacklist and none Logger
                if linkcheck.Loggers.has_key(val) and \
                   val not in ["blacklist", "none"]:
                    output = self.config.logger_new(val, fileoutput=1)
                    self.config['fileoutput'].append(output)
        if self.has_option(section, "interactive"):
            self.config["interactive"] = self.getboolean(section, "interactive")

    def read_checking_config (self):
        """Read configuration options in section "checking"."""
        section = "checking"
        if self.has_option(section, "threads"):
            num = self.getint(section, "threads")
            self.config['threads'] = max(0, num)
        if self.has_option(section, "timeout"):
            num = self.getint(section, "timeout")
            if num < 0:
                raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                    _("invalid negative value for timeout: %d\n"), num)
            self.config['timeout'] = num
        if self.has_option(section, "anchors"):
            self.config["anchors"] = self.getboolean(section, "anchors")
        if self.has_option(section, "recursionlevel"):
            num = self.getint(section, "recursionlevel")
            self.config["recursionlevel"] = num
        if self.has_option(section, "warningregex"):
            val = self.get(section, "warningregex")
            if val:
                self.config["warningregex"] = re.compile(val)
        if self.has_option(section, "warnsizebytes"):
            val = self.get(section,"warnsizebytes")
            self.config["warnsizebytes"] = int(val)
        if self.has_option(section, "nntpserver"):
            self.config["nntpserver"] = self.get(section, "nntpserver")
        if self.has_option(section,"anchorcaching"):
            val = self.getboolean(section, "anchorcaching")
            self.config["anchorcaching"] = val

    def read_authentication_config (self):
        """Read configuration options in section "authentication"."""
        section = "authentication"
        if self.has_option(section, "entry"):
            for val in read_multiline(self.get(section, "entry")):
                auth = val.split()
                if len(auth) != 3:
                    raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                       _("missing auth part in entry %(val)r") % \
                       {"val": val})
                self.config["authentication"].insert(0,
                    {'pattern': re.compile(auth[0]),
                     'user': auth[1],
                     'password': auth[2]})
        # backward compatibility
        i = 1
        while 1:
            key = "entry%d" % i
            if not self.has_option(section, key):
                break
            val = self.get(section, key)
            auth = val.split()
            linkcheck.log.warn(linkcheck.LOG_CHECK,
              _("the entry%(num)d syntax is deprecated; use " \
                "the new multiline configuration syntax") % {"num": i})
            if len(auth) != 3:
                raise linkcheck.LinkCheckerError(linkcheck.LOG_CHECK,
                   _("missing auth part in entry %(val)r") % \
                   {"val": val})
            self.config["authentication"].insert(0,
                {'pattern': re.compile(auth[0]),
                 'user': auth[1],
                 'password': auth[2]})
            i += 1

    def read_filtering_config (self):
        """
        Read configuration options in section "filtering".
        """
        section = "filtering"
        if self.has_option(section, "nofollow"):
            for line in read_multiline(self.get(section, "nofollow")):
                pat = linkcheck.get_link_pat(line, strict=0)
                self.config["externlinks"].append(pat)
        # backward compatibility
        i = 1
        while 1:
            key = "nofollow%d" % i
            if not self.has_option(section, key):
                break
            val = self.get(section, key)
            linkcheck.log.warn(linkcheck.LOG_CHECK,
              _("the nofollow%(num)d syntax is deprecated; use " \
                "the new multiline configuration syntax") % {"num": i})
            pat = linkcheck.get_link_pat(val, strict=0)
            self.config["externlinks"].append(pat)
            i += 1
        if self.has_option(section, "noproxyfor"):
            for val in read_multiline(self.get(section, "noproxyfor")):
                self.config["noproxyfor"].append(re.compile(val))
        # backward compatibility
        i = 1
        while 1:
            key = "noproxyfor%d" % i
            if not self.has_option(section, key):
                break
            linkcheck.log.warn(linkcheck.LOG_CHECK,
                  _("the noproxyfor%(num)d syntax is deprecated; use " \
                    "the new multiline configuration syntax") % {"num": i})
            val = self.get(section, key)
            self.config["noproxyfor"].append(re.compile(val))
            i += 1
        if self.has_option(section, "ignorewarnings"):
            self.config['ignorewarnings'] = [f.strip() for f in \
                 self.get(section, 'ignorewarnings').split(',')]
        if self.has_option(section, "ignore"):
            for line in read_multiline(self.get(section, "ignore")):
                pat = linkcheck.get_link_pat(line, strict=1)
                self.config["externlinks"].append(pat)
        # backward compatibility
        i = 1
        while 1:
            key = "ignore%d" % i
            if not self.has_option(section, key):
                break
            # backwards compatibility: split and ignore second part
            val = self.get(section, key).split()[0]
            linkcheck.log.warn(linkcheck.LOG_CHECK,
              _("the ignore%(num)d syntax is deprecated; use " \
                "the new multiline configuration syntax") % {"num": i})
            pat = linkcheck.get_link_pat(val, strict=1)
            self.config["externlinks"].append(pat)
            i += 1
        if self.has_option(section, "internlinks"):
            pat = linkcheck.get_link_pat(self.get(section, "internlinks"))
            self.config["internlinks"].append(pat)
