#!/usr/bin/env python

# profiling test
import linkcheck,re,profile,pstats
config = linkcheck.Config.Configuration()
config.appendUrl(linkcheck.UrlData.GetUrlDataFrom("http://www.yahoo.de/", 0))
profile.run("linkcheck.checkUrls(config)", "test.prof")

p = pstats.Stats("test.prof")
p.strip_dirs().sort_stats("time").print_stats(10)
