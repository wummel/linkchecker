""" linkcheck/__init__.py

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
class error(Exception):
    pass

# i18n suppport
LANG="EN" # default language (used for HTML output)
import LinkCheckerConf
try:
    import fintl,os,string
    gettext = fintl.gettext
    domain = 'linkcheck'
    localedir = os.path.join(LinkCheckerConf.install_data, 'locale')
    fintl.bindtextdomain(domain, localedir)
    fintl.textdomain(domain)
    languages = []
    for envvar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        if os.environ.has_key(envvar):
            languages = string.split(os.environ[envvar], ':')
            break
    if languages:
        LANG=string.upper(languages[0])

except ImportError:
    def gettext(msg):
        return msg
# set _ as an alias for gettext
_ = gettext

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
        config.log_endOfOutput()
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        sys.stderr.write("linkcheck: warning: keyboard interrupt\n")
