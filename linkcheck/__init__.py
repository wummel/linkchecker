"""__init__.py in linkcheck

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
import Config,UrlData,OutputReader,sys,lc_cgi

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
