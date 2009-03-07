# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2009 Bastian Kleineidam
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
from __future__ import with_statement # Required in 2.5
import signal
import subprocess
import os
import socket
from nose import SkipTest
from contextlib import contextmanager
from linkcheck import LinkCheckerInterrupt


class memoized (object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated."""

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            self.cache[args] = value = self.func(*args)
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__


def _run (cmd):
    null = open(os.name == 'nt' and ':NUL' or "/dev/null", 'w')
    try:
        try:
            return subprocess.call(cmd, stdout=null, stderr=subprocess.STDOUT)
        finally:
            null.close()
    except OSError:
        return -1


@memoized
def has_network ():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("www.heise.de", 80))
        s.close()
        return True
    except StandardError:
        pass
    return False


@memoized
def has_msgfmt ():
    return _run(["msgfmt", "-V"]) == 0


@memoized
def has_posix ():
    return os.name == "posix"


@memoized
def has_clamav ():
    try:
        cmd = ["grep", "LocalSocket", "/etc/clamav/clamd.conf"]
        sock = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].split()[1]
        if sock:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(sock)
            s.close()
            return True
    except StandardError:
        pass
    return False


@memoized
def has_proxy ():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 8081))
        s.close()
        return True
    except StandardError:
        pass
    return False


@contextmanager
def _limit_time (seconds):
    """Raises LinkCheckerInterrupt if given number of seconds have passed."""
    def signal_handler(signum, frame):
        raise LinkCheckerInterrupt("timed out")
    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    yield
    signal.alarm(0)
    if old_handler is not None:
        signal.signal(signal.SIGALRM, old_handler)


def limit_time (seconds, skip=False):
    """Limit test time to the given number of seconds, else fail or skip."""
    def run_limited (func):
        def new_func (*args, **kwargs):
            try:
                with _limit_time(seconds):
                    return func(*args, **kwargs)
            except LinkCheckerInterrupt, msg:
                if skip:
                    raise SkipTest
                assert False, msg
        new_func.func_name = func.func_name
        return new_func
    return run_limited


if __name__ == '__main__':
    print has_clamav(), has_network(), has_msgfmt(), has_posix(), has_proxy()
