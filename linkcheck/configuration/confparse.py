# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2012 Bastian Kleineidam
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
"""Parse configuration files"""

import ConfigParser
import re
from .. import LinkCheckerError, get_link_pat


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
        """Initialize configuration."""
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
            raise LinkCheckerError(
              _("Error parsing configuration: %s") % unicode(msg))

    def read_string_option (self, section, option, allowempty=False):
        """Read a sring option."""
        if self.has_option(section, option):
            value = self.get(section, option)
            if not allowempty and not value:
                raise LinkCheckerError(_("invalid empty value for %s: %s\n") % (option, value))
            self.config[option] = value

    def read_boolean_option(self, section, option):
        """Read a boolean option."""
        if self.has_option(section, option):
            self.config[option] = self.getboolean(section, option)

    def read_int_option (self, section, option, key=None, allownegative=False):
        """Read an integer option."""
        if self.has_option(section, option):
            num = self.getint(section, option)
            if not allownegative and num < 0:
                raise LinkCheckerError(
                    _("invalid negative value for %s: %d\n") % (option, num))
            if key is None:
                key = option
            self.config[key] = num

    def read_output_config (self):
        """Read configuration options in section "output"."""
        section = "output"
        from ..logger import Loggers
        for key in Loggers.iterkeys():
            if self.has_section(key):
                for opt in self.options(key):
                    self.config[key][opt] = self.get(key, opt)
                if self.has_option(key, 'parts'):
                    val = self.get(key, 'parts')
                    parts = [f.strip().lower() for f in val.split(',')]
                    self.config[key]['parts'] = parts
        self.read_boolean_option(section, "warnings")
        if self.has_option(section, "verbose"):
            if self.getboolean(section, "verbose"):
                self.config["verbose"] = True
                self.config["warnings"] = True
        if self.has_option(section, "complete"):
            if self.getboolean(section, "complete"):
                self.config["complete"] = True
                self.config["verbose"] = True
                self.config["warnings"] = True
        if self.has_option(section, "quiet"):
            if self.getboolean(section, "quiet"):
                self.config['output'] = 'none'
                self.config['quiet'] = True
        if self.has_option(section, "debug"):
            val = self.get(section, "debug")
            parts = [f.strip().lower() for f in val.split(',')]
            self.config.set_debug(parts)
        self.read_boolean_option(section, "status")
        if self.has_option(section, "log"):
            val = self.get(section, "log").strip().lower()
            self.config['output'] = val
        if self.has_option(section, "fileoutput"):
            loggers = self.get(section, "fileoutput").split(",")
            # strip names from whitespace
            loggers = (x.strip().lower() for x in loggers)
            # no file output for the blacklist and none Logger
            loggers = (x for x in loggers if x in Loggers and
                       x not in ("blacklist", "none"))
            for val in loggers:
                output = self.config.logger_new(val, fileoutput=1)
                self.config['fileoutput'].append(output)

    def read_checking_config (self):
        """Read configuration options in section "checking"."""
        section = "checking"
        self.read_int_option(section, "threads", allownegative=True)
        self.config['threads'] = max(0, self.config['threads'])
        self.read_int_option(section, "timeout")
        self.read_boolean_option(section, "anchors")
        self.read_int_option(section, "recursionlevel", allownegative=True)
        if self.has_option(section, "warningregex"):
            val = self.get(section, "warningregex")
            if val:
                self.config["warningregex"] = re.compile(val)
        self.read_int_option(section, "warnsizebytes")
        self.read_string_option(section, "nntpserver")
        self.read_string_option(section, "useragent")
        self.read_int_option(section, "pause", key="wait")
        self.read_check_options(section)

    def read_check_options (self, section):
        """Read check* options."""
        self.read_boolean_option(section, "checkhtml")
        self.read_boolean_option(section, "checkcss")
        self.read_boolean_option(section, "scanvirus")
        self.read_boolean_option(section, "clamavconf")
        self.read_boolean_option(section, "debugmemory")
        if self.has_option(section, "cookies"):
            self.config["sendcookies"] = self.config["storecookies"] = \
                self.getboolean(section, "cookies")
        self.read_string_option(section, "cookiefile")
        self.read_string_option(section, "localwebroot")
        self.read_int_option(section, "warnsslcertdaysvalid")
        self.read_int_option(section, "maxrunseconds")

    def read_authentication_config (self):
        """Read configuration options in section "authentication"."""
        section = "authentication"
        if self.has_option(section, "entry"):
            for val in read_multiline(self.get(section, "entry")):
                auth = val.split()
                if len(auth) == 3:
                    self.config.add_auth(pattern=auth[0], user=auth[1],
                                         password=auth[2])
                elif len(auth) == 2:
                    self.config.add_auth(pattern=auth[0], user=auth[1])
                else:
                    raise LinkCheckerError(
                       _("missing auth part in entry %(val)r") % {"val": val})
        # read login URL and field names
        if self.has_option(section, "loginurl"):
            val = self.get(section, "loginurl").strip()
            if not (val.lower().startswith("http:") or
                    val.lower().startswith("https:")):
                raise LinkCheckerError(_("invalid login URL `%s'. Only " \
                  "HTTP and HTTPS URLs are supported.") % val)
            self.config["loginurl"] = val
            self.config["storecookies"] = self.config["sendcookies"] = True
        self.read_string_option(section, "loginuserfield")
        self.read_string_option(section, "loginpasswordfield")
        # read login extra fields
        if self.has_option(section, "loginextrafields"):
            for val in read_multiline(self.get(section, "loginextrafields")):
                name, value = val.split(":", 1)
                self.config["loginextrafields"][name] = value

    def read_filtering_config (self):
        """
        Read configuration options in section "filtering".
        """
        section = "filtering"
        if self.has_option(section, "ignorewarnings"):
            self.config['ignorewarnings'] = [f.strip() for f in \
                 self.get(section, 'ignorewarnings').split(',')]
        if self.has_option(section, "ignore"):
            for line in read_multiline(self.get(section, "ignore")):
                pat = get_link_pat(line, strict=1)
                self.config["externlinks"].append(pat)
        if self.has_option(section, "nofollow"):
            for line in read_multiline(self.get(section, "nofollow")):
                pat = get_link_pat(line, strict=0)
                self.config["externlinks"].append(pat)
        if self.has_option(section, "internlinks"):
            pat = get_link_pat(self.get(section, "internlinks"))
            self.config["internlinks"].append(pat)
