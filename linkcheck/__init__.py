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
"""
Main function module for link checking.
"""

# imports and checks
import sys
# Needs Python >= 2.7 because we use dictionary based logging config
# Needs Python >= 2.7.2 which fixed http://bugs.python.org/issue11467
if not (hasattr(sys, 'version_info') or
        sys.version_info < (2, 7, 2, 'final', 0)):
    raise SystemExit("This program requires Python 2.7.2 or later.")
import os
# add the custom linkcheck_dns directory to sys.path
_dnspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'linkcheck_dns'))
if _dnspath not in sys.path:
    sys.path.insert(0, _dnspath)
del _dnspath
import re
import signal
import traceback

from . import i18n
import _LinkChecker_configdata as configdata


def main_is_frozen ():
    """Return True iff running inside a py2exe-generated executable."""
    return hasattr(sys, "frozen")


def module_path ():
    """Return absolute directory of system executable."""
    return os.path.dirname(os.path.abspath(sys.executable))


def get_install_data ():
    """Return absolute path of LinkChecker data installation directory."""
    if main_is_frozen():
        return module_path()
    return configdata.install_data


def get_config_dir ():
    """Return absolute path of LinkChecker example configuration."""
    return os.path.join(get_install_data(), "share", "linkchecker")


# application log areas
LOG_ROOT = "linkcheck"
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_CACHE = "linkcheck.cache"
LOG_GUI = "linkcheck.gui"
LOG_THREAD = "linkcheck.thread"
lognames = {
    "cmdline": LOG_CMDLINE,
    "checking": LOG_CHECK,
    "cache": LOG_CACHE,
    "gui": LOG_GUI,
    "thread": LOG_THREAD,
    "all": LOG_ROOT,
}
lognamelist = ", ".join(repr(name) for name in lognames)

# logging configuration
configdict = {
    'version': 1,
    'loggers': {
    },
    'root': {
      'level': 'DEBUG',
    },
}

def init_log_config():
    """Configure the application loggers."""
    for applog in lognames.values():
        # propagate except for root app logger 'linkcheck'
        propagate = (applog != LOG_ROOT)
        configdict['loggers'][applog] = dict(level='INFO', propagate=propagate)

init_log_config()

from . import log


class LinkCheckerError (StandardError):
    """Exception to be raised on linkchecker-specific check errors."""
    pass

class LinkCheckerInterrupt (StandardError):
    """Used for testing."""
    pass


def get_link_pat (arg, strict=False):
    """Get a link pattern matcher for intern/extern links.
    Returns a compiled pattern and a negate and strict option.

    @param arg: pattern from config
    @type arg: string
    @param strict: if pattern is to be handled strict
    @type strict: bool
    @return: dictionary with keys 'pattern', 'negate' and 'strict'
    @rtype: dict
    """
    log.debug(LOG_CHECK, "Link pattern %r strict=%s", arg, strict)
    if arg.startswith('!'):
        pattern = arg[1:]
        negate = True
    else:
        pattern = arg
        negate = False
    return {
        "pattern": re.compile(pattern),
        "negate": negate,
        "strict": strict,
    }


def init_i18n (loc=None):
    """Initialize i18n with the configured locale dir. The environment
    variable LOCPATH can also specify a locale dir.

    @return: None
    """
    if 'LOCPATH' in os.environ:
        locdir = os.environ['LOCPATH']
    else:
        locdir = os.path.join(get_install_data(), 'share', 'locale')
    i18n.init(configdata.name.lower(), locdir, loc=loc)
    # install translated log level names
    import logging
    logging.addLevelName(logging.CRITICAL, _('CRITICAL'))
    logging.addLevelName(logging.ERROR, _('ERROR'))
    logging.addLevelName(logging.WARN, _('WARN'))
    logging.addLevelName(logging.WARNING, _('WARNING'))
    logging.addLevelName(logging.INFO, _('INFO'))
    logging.addLevelName(logging.DEBUG, _('DEBUG'))
    logging.addLevelName(logging.NOTSET, _('NOTSET'))

# initialize i18n, puts _() and _n() function into global namespace
init_i18n()


def drop_privileges ():
    """Make sure to drop root privileges on POSIX systems."""
    if os.name != 'posix':
        return
    if os.geteuid() == 0:
        log.warn(LOG_CHECK, _("Running as root user; "
                       "dropping privileges by changing user to nobody."))
        import pwd
        os.seteuid(pwd.getpwnam('nobody')[3])


def find_third_party_modules ():
    """Find third party modules and add them to the python path."""
    parent = os.path.dirname(os.path.dirname(__file__))
    third_party = os.path.join(parent, "third_party")
    if os.path.isdir(third_party):
        sys.path.append(os.path.join(third_party, "dnspython"))

find_third_party_modules()

# install SIGUSR1 handler
from .decorators import signal_handler
@signal_handler(signal.SIGUSR1)
def print_threadstacks(sig, frame):
    """Print stack traces of all running threads."""
    log.warn(LOG_THREAD, "*** STACKTRACE START ***")
    for threadId, stack in sys._current_frames().items():
        log.warn(LOG_THREAD, "# ThreadID: %s" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            log.warn(LOG_THREAD, 'File: "%s", line %d, in %s' % (filename, lineno, name))
            line = line.strip()
            if line:
                log.warn(LOG_THREAD, "  %s" % line)
    log.warn(LOG_THREAD, "*** STACKTRACE END ***")

