import os, sys
import linkcheck
config = linkcheck.Config.Configuration()
config['recursionlevel'] = 1
config['log'] = config.newLogger('test')
config["anchors"] = 1
config["verbose"] = 1
config.disableThreading()
htmldir = "test/html"
for file in ('https.html',):
    url = os.path.join(htmldir, file)
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0))
linkcheck.checkUrls(config)
