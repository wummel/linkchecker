# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
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
"""Status message handling"""
import threading
import time
import sys
import codecs
import traceback
import os
import linkcheck.i18n
from linkcheck.decorators import synchronized

# All output goes to stderr here, making sure the console gets correct
# encoded messages.
_encoding = linkcheck.i18n.default_encoding
stderr = codecs.getwriter(_encoding)(sys.stderr, errors="ignore")

def internal_error ():
    """
    Print internal error message to stderr.
    """
    print >> stderr, os.linesep
    print >> stderr, _("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
- the URL or file you are testing
- your commandline arguments and/or configuration.
- the output of a debug run with option "-Dall" of the executed command
- the system information below.

Disclosing some of the information above due to privacy reasons is ok.
I will try to help you nonetheless, but you have to give me something
I can work with ;) .
""") % linkcheck.configuration.Email
    etype, value = sys.exc_info()[:2]
    print >> stderr, etype, value
    traceback.print_exc()
    print_app_info()
    print >> stderr, os.linesep, \
            _("******** LinkChecker internal error, over and out ********")
    sys.exit(1)


def print_app_info ():
    """
    Print system and application info to stderr.
    """
    print >> stderr, _("System info:")
    print >> stderr, linkcheck.configuration.App
    print >> stderr, _("Python %s on %s") % (sys.version, sys.platform)
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> stderr, key, "=", repr(value)


# lock for status thread
_status_lock = threading.Lock()
# flag to tell when status thread should stop
status_flag = True

@synchronized(_status_lock)
def status_is_active ():
    """
    Check status control flag.
    """
    return status_flag

@synchronized(_status_lock)
def disable_status ():
    """
    Set status control flag in order to stop the status thread.
    """
    global status_flag
    status_flag = False


def do_status (urlqueue):
    """
    Print periodic status messages.
    """
    start_time = time.time()
    threading.currentThread().setName("Status")
    while True:
        for dummy in xrange(5):
            time.sleep(1)
            if not status_is_active():
                return
        print_status(urlqueue, start_time)


def print_status (urlqueue, start_time):
    """
    Print a status message.
    """
    duration = time.time() - start_time
    checked, in_progress, queue = urlqueue.status()
    msg = _n("%2d URL active,", "%2d URLs active,", in_progress) % in_progress
    print >> stderr, msg,
    msg = _n("%5d URL queued,", "%5d URLs queued,", queue) % queue
    print >> stderr, msg,
    msg = _n("%4d URL checked,", "%4d URLs checked,", checked) % checked
    print >> stderr, msg,
    msg = _("runtime %s") % linkcheck.strformat.strduration_long(duration)
    print >> stderr, msg
