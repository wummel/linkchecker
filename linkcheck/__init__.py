"""main function module for link checking"""
# Copyright (C) 2000,2001  Bastian Kleineidam
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

class error(Exception):
    pass

# i18n suppport
import _linkchecker_configdata
try:
    import gettext
    domain = 'linkcheck'
    localedir = os.path.join(_linkchecker_configdata.install_data, 'locale')
    t = gettext.translation(domain, localedir)
    _ = t.gettext
except IOError:
    _ = lambda s: s

#import timeoutsocket
#timeoutsocket.setDefaultSocketTimeout(20)

import Config,UrlData,sys,lc_cgi
from debuglevels import *
debug = Config.debug

def checkUrls(config):
    """ checkUrls gets a complete configuration object as parameter where all
    runtime-dependent options are stored.
    If you call checkUrls more than once, you can specify different
    configurations.

    In the config object there are functions to get a new URL (getUrl) and
    to check it (checkUrl).
    """
    debug(HURT_ME_PLENTY, "threads", config['threads'])
    config.log_init()
    try:
        while not config.finished():
            if config.hasMoreUrls():
                config.checkUrl(config.getUrl())
        config.log_endOfOutput()
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        sys.stderr.write("linkcheck: warning: keyboard interrupt\n")
