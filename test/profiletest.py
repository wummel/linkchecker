#!/usr/bin/env python

# profiling test
import sys
sys.path.append("/home/calvin/projects/linkchecker/")
import linkcheck,re,profile,pstats
url="http://treasure.calvinsplayground.de/~calvin/"
config = linkcheck.Config.Configuration()
config["verbose"] = 1
config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0))
profile.run("linkcheck.checkUrls(config)", "test.prof")
p = pstats.Stats("test.prof")
p.strip_dirs().sort_stats("time").print_stats(10)
