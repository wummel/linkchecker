import os, linkcheck
config = linkcheck.Config.Configuration()
config.addLogger('test', linkcheck.test_support.TestLogger)
config['recursionlevel'] = 1
config['log'] = config.newLogger('test')
config["anchors"] = 1
config["verbose"] = 1
config.disableThreading()
htmldir = "test/html"
for file in ('base1.html','base2.html', 'codebase.html'):
    url = os.path.join(htmldir, file)
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0, config))
linkcheck.checkUrls(config)
