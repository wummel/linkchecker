# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
Management of checking a queue of links with several threads.
"""
import os
try: # Python 3
    from _thread import error as thread_error
except ImportError: # Python 2
    from thread import error as thread_error
import time
from .. import log, LOG_CHECK, LinkCheckerInterrupt, plugins
from ..cache import urlqueue, robots_txt, results
from . import aggregator, console


def check_urls (aggregate):
    """Main check function; checks all configured URLs until interrupted
    with Ctrl-C.
    @return: None
    """
    try:
        aggregate.visit_loginurl()
    except Exception as msg:
        log.warn(LOG_CHECK, _("Error using login URL: %(msg)s.") % \
                 dict(msg=msg))
        raise
    try:
        aggregate.logger.start_log_output()
    except Exception as msg:
        log.error(LOG_CHECK, _("Error starting log output: %(msg)s.") % \
            dict(msg=msg))
        raise
    try:
        if not aggregate.urlqueue.empty():
            aggregate.start_threads()
        check_url(aggregate)
        aggregate.finish()
        aggregate.end_log_output()
    except LinkCheckerInterrupt:
        raise
    except KeyboardInterrupt:
        interrupt(aggregate)
    except thread_error:
        log.warn(LOG_CHECK,
             _("Could not start a new thread. Check that the current user" \
               " is allowed to start new threads."))
        abort(aggregate)
    except Exception:
        # Catching "Exception" is intentionally done. This saves the program
        # from libraries that raise all kinds of strange exceptions.
        console.internal_error()
        aggregate.logger.log_internal_error()
        abort(aggregate)
    # Not catched exceptions at this point are SystemExit and GeneratorExit,
    # and both should be handled by the calling layer.


def check_url (aggregate):
    """Helper function waiting for URL queue."""
    while True:
        try:
            aggregate.urlqueue.join(timeout=30)
            break
        except urlqueue.Timeout:
            # Cleanup threads every 30 seconds
            aggregate.remove_stopped_threads()
            if not any(aggregate.get_check_threads()):
                break


def interrupt (aggregate):
    """Interrupt execution and shutdown, ignoring any subsequent
    interrupts."""
    while True:
        try:
            log.warn(LOG_CHECK,
               _("interrupt; waiting for active threads to finish"))
            log.warn(LOG_CHECK,
               _("another interrupt will exit immediately"))
            abort(aggregate)
            break
        except KeyboardInterrupt:
            pass


def abort (aggregate):
    """Helper function to ensure a clean shutdown."""
    while True:
        try:
            aggregate.abort()
            aggregate.finish()
            aggregate.end_log_output(interrupt=True)
            break
        except KeyboardInterrupt:
            log.warn(LOG_CHECK, _("user abort; force shutdown"))
            aggregate.end_log_output(interrupt=True)
            abort_now()


def abort_now ():
    """Force exit of current process without cleanup."""
    if os.name == 'posix':
        # Unix systems can use signals
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGKILL)
    elif os.name == 'nt':
        # NT has os.abort()
        os.abort()
    else:
        # All other systems have os._exit() as best shot.
        os._exit(3)


def get_aggregate (config):
    """Get an aggregator instance with given configuration."""
    _urlqueue = urlqueue.UrlQueue(max_allowed_urls=config["maxnumurls"])
    _robots_txt = robots_txt.RobotsTxt(config["useragent"])
    plugin_manager = plugins.PluginManager(config)
    result_cache = results.ResultCache()
    return aggregator.Aggregate(config, _urlqueue, _robots_txt, plugin_manager,
        result_cache)
