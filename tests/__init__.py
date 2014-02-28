# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
import signal
import subprocess
import os
import sys
import socket
import pytest
from contextlib import contextmanager
from linkcheck import LinkCheckerInterrupt, winutil


basedir = os.path.dirname(__file__)
linkchecker_cmd = os.path.join(os.path.dirname(basedir), "linkchecker")


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


def run (cmd, verbosity=0, **kwargs):
    """Run command without error checking.
    @return: command return code"""
    if kwargs.get("shell"):
        # for shell calls the command must be a string
        cmd = " ".join(cmd)
    return subprocess.call(cmd, **kwargs)


def run_checked (cmd, ret_ok=(0,), **kwargs):
    """Run command and raise OSError on error."""
    retcode = run(cmd, **kwargs)
    if retcode not in ret_ok:
        msg = "Command `%s' returned non-zero exit status %d" % (cmd, retcode)
        raise OSError(msg)
    return retcode



def run_silent (cmd):
    """Run given command without output."""
    null = open(os.name == 'nt' and ':NUL' or "/dev/null", 'w')
    try:
        return run(cmd, stdout=null, stderr=subprocess.STDOUT)
    finally:
        null.close()


def _need_func (testfunc, name):
    """Decorator skipping test if given testfunc fails."""
    def check_func (func):
        def newfunc (*args, **kwargs):
            if not testfunc():
                pytest.skip("%s is not available" % name)
            return func(*args, **kwargs)
        newfunc.func_name = func.func_name
        return newfunc
    return check_func


@memoized
def has_network ():
    """Test if network is up."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("www.python.org", 80))
        s.close()
        return True
    except StandardError:
        pass
    return False

need_network = _need_func(has_network, "network")


@memoized
def has_msgfmt ():
    """Test if msgfmt is available."""
    return run_silent(["msgfmt", "-V"]) == 0

need_msgfmt = _need_func(has_msgfmt, "msgfmt")


@memoized
def has_posix ():
    """Test if this is a POSIX system."""
    return os.name == "posix"

need_posix = _need_func(has_posix, "POSIX system")


@memoized
def has_windows ():
    """Test if this is a Windows system."""
    return os.name == "nt"

need_windows = _need_func(has_windows, "Windows system")


@memoized
def has_linux ():
    """Test if this is a Linux system."""
    return sys.platform.startswith("linux")

need_linux = _need_func(has_linux, "Linux system")


@memoized
def has_clamav ():
    """Test if ClamAV daemon is installed and running."""
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

need_clamav = _need_func(has_clamav, "ClamAV")


@memoized
def has_proxy ():
    """Test if proxy is running on port 8081."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 8081))
        s.close()
        return True
    except StandardError:
        return False

need_proxy = _need_func(has_proxy, "proxy")


@memoized
def has_pyftpdlib ():
    """Test if pyftpdlib is available."""
    try:
        import pyftpdlib
        return True
    except ImportError:
        return False

need_pyftpdlib = _need_func(has_pyftpdlib, "pyftpdlib")


@memoized
def has_biplist ():
    """Test if biplist is available."""
    try:
        import biplist
        return True
    except ImportError:
        return False

need_biplist = _need_func(has_biplist, "biplist")


@memoized
def has_newsserver (server):
    import nntplib
    try:
        nntp = nntplib.NNTP(server, usenetrc=False)
        nntp.quit()
        return True
    except nntplib.NNTPError:
        return False


def need_newsserver (server):
    """Decorator skipping test if newsserver is not available."""
    def check_func (func):
        def newfunc (*args, **kwargs):
            if not has_newsserver(server):
                pytest.skip("Newsserver `%s' is not available" % server)
            return func(*args, **kwargs)
        newfunc.func_name = func.func_name
        return newfunc
    return check_func


@memoized
def has_pyqt ():
    """Test if PyQT is installed."""
    try:
        import PyQt4
        return True
    except ImportError:
        pass
    return False

need_pyqt = _need_func(has_pyqt, "PyQT")


@memoized
def has_x11 ():
    """Test if DISPLAY variable is set."""
    return os.getenv('DISPLAY') is not None

need_x11 = _need_func(has_x11, 'X11')


@memoized
def has_word():
    """Test if Word is available."""
    return winutil.has_word()

need_word = _need_func(has_word, 'Word')


@contextmanager
def _limit_time (seconds):
    """Raises LinkCheckerInterrupt if given number of seconds have passed."""
    if os.name == 'posix':
        def signal_handler(signum, frame):
            raise LinkCheckerInterrupt("timed out")
        old_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
    yield
    if os.name == 'posix':
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
                    pytest.skip("time limit of %d seconds exceeded" % seconds)
                assert False, msg
        new_func.func_name = func.func_name
        return new_func
    return run_limited


def get_file (filename=None):
    """
    Get file name located within 'data' directory.
    """
    directory = os.path.join("tests", "checker", "data")
    if filename:
        return unicode(os.path.join(directory, filename))
    return unicode(directory)


if __name__ == '__main__':
    print "has clamav", has_clamav()
    print "has network", has_network()
    print "has msgfmt", has_msgfmt()
    print "has POSIX", has_posix()
    print "has proxy", has_proxy()
    print "has PyQt", has_pyqt()
    print "has X11", has_x11()
