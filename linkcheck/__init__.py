# __init__.py for this module

import Config,UrlData,OutputReader,sys,lc_cgi

def checkUrls(config = Config.Configuration()):
    config.log_init()
    try:
        while not config.finished():
            if config.hasMoreUrls():
                config.checkUrl(config.getUrl())
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        sys.exit(1) # this is not good(tm)
    config.log_endOfOutput()
