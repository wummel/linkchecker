# -*- coding: iso-8859-1 -*-
import os, linkcheck
config = linkcheck.Config.Configuration()
config.addLogger('test', linkcheck.test_support.TestLogger)
config['recursionlevel'] = 1
config['log'] = config.newLogger('test')
config["anchors"] = True
config["verbose"] = True
config.setThreads(0)
for filename in ('mail.html',):
    url = os.path.join("test", "html", filename)
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0, config))
linkcheck.checkUrls(config)
