# -*- coding: iso-8859-1 -*-
import os, linkcheck
config = linkcheck.Config.Configuration()
config.addLogger('test', linkcheck.test_support.TestLogger)
config['recursionlevel'] = 1
config['log'] = config.newLogger('test')
config["anchors"] = True
config["verbose"] = True
config.setThreads(0)
htmldir = "test/html"
for filename in ('misc.html','anchor.html', 'norobots'):
    url = os.path.join(htmldir, filename)
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0, config))
linkcheck.checkUrls(config)
