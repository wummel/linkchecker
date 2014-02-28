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
"""Parse configuration files"""

import ConfigParser
import os
from .. import LinkCheckerError, get_link_pat, LOG_CHECK, log, fileutil, plugins


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
        assert isinstance(files, list), "Invalid file list %r" % files
        try:
            self.read_ok = super(LCConfigParser, self).read(files)
            if len(self.read_ok) < len(files):
                failed_files = set(files) - set(self.read_ok)
                log.warn(LOG_CHECK, "Could not read configuration files %s.", failed_files)
            # Read all the configuration parameters from the given files.
            self.read_checking_config()
            self.read_authentication_config()
            self.read_filtering_config()
            self.read_output_config()
            self.read_plugin_config()
        except Exception as msg:
            raise LinkCheckerError(
              _("Error parsing configuration: %s") % unicode(msg))

    def read_string_option (self, section, option, allowempty=False):
        """Read a string option."""
        if self.has_option(section, option):
            value = self.get(section, option)
            if not allowempty and not value:
                raise LinkCheckerError(_("invalid empty value for %s: %s\n") % (option, value))
            self.config[option] = value

    def read_boolean_option(self, section, option):
        """Read a boolean option."""
        if self.has_option(section, option):
            self.config[option] = self.getboolean(section, option)

    def read_int_option (self, section, option, key=None, min=None, max=None):
        """Read an integer option."""
        if self.has_option(section, option):
            num = self.getint(section, option)
            if min is not None and num < min:
                raise LinkCheckerError(
                    _("invalid value for %s: %d must not be less than %d") % (option, num, min))
            if max is not None and num < max:
                raise LinkCheckerError(
                    _("invalid value for %s: %d must not be greater than %d") % (option, num, max))
            if key is None:
                key = option
            self.config[key] = num

    def read_output_config (self):
        """Read configuration options in section "output"."""
        section = "output"
        from ..logger import LoggerClasses
        for c in LoggerClasses:
            key = c.LoggerName
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
            from ..logger import LoggerNames
            loggers = (x for x in loggers if x in LoggerNames and
                       x not in ("blacklist", "none"))
            for val in loggers:
                output = self.config.logger_new(val, fileoutput=1)
                self.config['fileoutput'].append(output)

    def read_checking_config (self):
        """Read configuration options in section "checking"."""
        section = "checking"
        self.read_int_option(section, "threads", min=-1)
        self.config['threads'] = max(0, self.config['threads'])
        self.read_int_option(section, "timeout", min=1)
        self.read_int_option(section, "aborttimeout", min=1)
        self.read_int_option(section, "recursionlevel", min=-1)
        self.read_string_option(section, "nntpserver")
        self.read_string_option(section, "useragent")
        self.read_int_option(section, "maxrequestspersecond", min=1)
        self.read_int_option(section, "maxnumurls", min=0)
        self.read_int_option(section, "maxfilesizeparse", min=1)
        self.read_int_option(section, "maxfilesizedownload", min=1)
        if self.has_option(section, "allowedschemes"):
            self.config['allowedschemes'] = [x.strip().lower() for x in \
                 self.get(section, 'allowedschemes').split(',')]
        self.read_boolean_option(section, "debugmemory")
        self.read_string_option(section, "cookiefile")
        self.read_string_option(section, "localwebroot")
        try:
            self.read_boolean_option(section, "sslverify")
        except ValueError:
            self.read_string_option(section, "sslverify")
        self.read_int_option(section, "maxrunseconds", min=0)

    def read_authentication_config (self):
        """Read configuration options in section "authentication"."""
        section = "authentication"
        password_fields = []
        if self.has_option(section, "entry"):
            for val in read_multiline(self.get(section, "entry")):
                auth = val.split()
                if len(auth) == 3:
                    self.config.add_auth(pattern=auth[0], user=auth[1],
                                         password=auth[2])
                    password_fields.append("entry/%s/%s" % (auth[0], auth[1]))
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
        self.read_string_option(section, "loginuserfield")
        self.read_string_option(section, "loginpasswordfield")
        # read login extra fields
        if self.has_option(section, "loginextrafields"):
            for val in read_multiline(self.get(section, "loginextrafields")):
                name, value = val.split(":", 1)
                self.config["loginextrafields"][name] = value
        self.check_password_readable(section, password_fields)

    def check_password_readable(self, section, fields):
        """Check if there is a readable configuration file and print a warning."""
        if not fields:
            return
        # The information which of the  configuration files
        # included which option is not available. To avoid false positives,
        # a warning is only printed if exactly one file has been read.
        if len(self.read_ok) != 1:
            return
        fn = self.read_ok[0]
        if fileutil.is_accessable_by_others(fn):
            log.warn(LOG_CHECK, "The configuration file %s contains password information (in section [%s] and options %s) and the file is readable by others. Please make the file only readable by you.", fn, section, fields)
            if os.name == 'posix':
                log.warn(LOG_CHECK, _("For example execute 'chmod go-rw %s'.") % fn)
            elif os.name == 'nt':
                log.warn(LOG_CHECK, _("See http://support.microsoft.com/kb/308419 for more info on setting file permissions."))

    def read_filtering_config (self):
        """
        Read configuration options in section "filtering".
        """
        section = "filtering"
        if self.has_option(section, "ignorewarnings"):
            self.config['ignorewarnings'] = [f.strip().lower() for f in \
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
        self.read_boolean_option(section, "checkextern")

    def read_plugin_config(self):
        """Read plugin-specific configuration values."""
        folders = self.config["pluginfolders"]
        modules = plugins.get_plugin_modules(folders)
        for pluginclass in plugins.get_plugin_classes(modules):
            section = pluginclass.__name__
            if self.has_section(section):
                self.config["enabledplugins"].append(section)
                self.config[section] = pluginclass.read_config(self)
