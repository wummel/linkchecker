"""__init__.py in linkcheck

    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

Here we find the main function to call: checkUrls.
This is the only entry point into the linkcheck module and is used
of course by the linkchecker script.
"""

# i18n suppport
try:
    import fintl
    gettext = fintl.gettext
    fintl.bindtextdomain('linkcheck')
    fintl.textdomain('linkcheck')
except ImportError:
    def gettext(msg):
        return msg
import Config,UrlData,sys,lc_cgi

def checkUrls(config = Config.Configuration()):
    """ checkUrls gets a complete configuration object as parameter where all
    runtime-dependent options are stored.
    If you call checkUrls more than once, you can specify different
    configurations.

    In the config object there are functions to get a new URL (getUrl) and
    to check it (checkUrl).
    """
    config.log_init()
    try:
        while not config.finished():
            if config.hasMoreUrls():
                config.checkUrl(config.getUrl())
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        sys.exit(1) # XXX this is not good(tm)
    config.log_endOfOutput()
