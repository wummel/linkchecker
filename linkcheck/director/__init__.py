# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2010 Bastian Kleineidam
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
import time
import os
import thread
from .. import log, LOG_CHECK, LinkCheckerInterrupt
from ..cache import urlqueue, robots_txt, cookie, connection
from . import aggregator, console


def check_urls (aggregate):
    """Main check function; checks all configured URLs until interrupted
    with Ctrl-C.
    @return: None
    """
    try:
        aggregate.logger.start_log_output()
        if not aggregate.urlqueue.empty():
            aggregate.start_threads()
        check_url(aggregate)
        aggregate.finish()
        aggregate.logger.end_log_output()
    except LinkCheckerInterrupt:
        raise
    except KeyboardInterrupt:
        interrupt(aggregate)
    except thread.error:
        log.warn(LOG_CHECK,
             _("Could not start a new thread. Check that the current user" \
               " is allowed to start new threads."))
        abort(aggregate)
    except Exception:
        # Catching "Exception" is intentionally done. This saves the program
        # from badly-programmed libraries that raise all kinds of strange
        # exceptions.
        console.internal_error()
        abort(aggregate)
    # Not catched exceptions at this point are SystemExit and GeneratorExit,
    # and both should be handled by the calling layer.


def check_url (aggregate):
    """Helper function waiting for URL queue."""
    while True:
        try:
            aggregate.urlqueue.join(timeout=1)
            break
        except urlqueue.Timeout:
            # Since urlqueue.join() is not interruptable, add a timeout
            # and a one-second slumber.
            time.sleep(1)
            aggregate.remove_stopped_threads()
            if not aggregate.threads:
                break
            if aggregate.wanted_stop:
                # some other thread wants us to stop
                raise KeyboardInterrupt


def interrupt (aggregate):
    """Interrupt execution and shutdown, ignoring any subsequent
    interrupts."""
    while True:
        try:
            log.warn(LOG_CHECK,
               _("keyboard interrupt; waiting for active threads to finish"))
            log.warn(LOG_CHECK,
               _("another keyboard interrupt will exit immediately"))
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
            aggregate.logger.end_log_output()
            break
        except KeyboardInterrupt:
            log.warn(LOG_CHECK, _("keyboard interrupt; force shutdown"))
            abort_now()


def abort_now ():
    """Force exit of current process without cleanup."""
    if os.name == 'posix':
        # Unix systems can use sigkill
        import signal
        os.kill(os.getpid(), signal.SIGKILL)
    elif os.name == 'nt':
        # NT has os.abort()
        os.abort()
    else:
        # All other systems have os._exit() as best shot.
        os._exit(3)


def get_aggregate (config):
    """Get an aggregator instance with given configuration."""
    _urlqueue = urlqueue.UrlQueue()
    connections = connection.ConnectionPool(wait=config["wait"])
    cookies = cookie.CookieJar()
    _robots_txt = robots_txt.RobotsTxt()
    return aggregator.Aggregate(config, _urlqueue, connections,
                                cookies, _robots_txt)
