#!/usr/bin/env python

import re,cgi,sys,urlparse,time,os

# configuration
sys.stderr = sys.stdout
dist_dir = "/home/calvin/projects/linkchecker"
sys.path.insert(0,dist_dir)
cgi.logfile = "linkchecker.log" # must be an existing file
# end configuration

def testit():
    cgi.test()
    sys.exit(0)

import linkcheck

# main
print "Content-type: text/html"
print "Cache-Control: no-cache"
print
#testit()
form = cgi.FieldStorage()
if not linkcheck.lc_cgi.checkform(form):
    linkcheck.lc_cgi.logit(form, form)
    linkcheck.lc_cgi.printError(sys.stdout)
    sys.exit(0)
config = linkcheck.Config.Configuration()
config["recursionlevel"] = int(form["level"].value)
config["log"] = linkcheck.Logging.HtmlLogger()
if form.has_key("anchors"):    config["anchors"] = 1
if not form.has_key("errors"): config["verbose"] = 1
if form.has_key("intern"):
    config["internlinks"].append(re.compile("^(ftp|https?)://"+\
    linkcheck.lc_cgi.getHostName(form)))
else:
    config["internlinks"].append(re.compile(".+"))
# avoid checking of local files
config["externlinks"].append((re.compile("^file:"), 1))

# start checking
config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(form["url"].value, 0))
linkcheck.checkUrls(config)
