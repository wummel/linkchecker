#!/usr/bin/env python

import re,cgi,sys,urlparse,time,os
sys.stderr = sys.stdout

# begin user configuration
dist_dir = "/home/calvin/projects/linkchecker"
cgi.logfile = "linkchecker.log" # must be an existing file
# end user configuration

sys.path.insert(0,dist_dir)

def testit():
    cgi.test()
    sys.exit(0)

# main
print "Content-type: text/html"
print "Cache-Control: no-cache"
print
# uncomment the following line to test your CGI values
#testit()
form = cgi.FieldStorage()
if form['language'].value == 'de':
    os.environ['LC_MESSAGES'] = 'de'
elif form['language'].value == 'fr':
    os.environ['LC_MESSAGES'] = 'fr'
else:
    os.environ['LC_MESSAGES'] = 'C'
import linkcheck
if not linkcheck.lc_cgi.checkform(form):
    linkcheck.lc_cgi.logit(form, form)
    linkcheck.lc_cgi.printError(sys.stdout)
    sys.exit(0)
config = linkcheck.Config.Configuration()
config["recursionlevel"] = int(form["level"].value)
config['log'] = config.newLogger('html')
if form.has_key('strict'): config['strict'] = 1
if form.has_key("anchors"): config["anchors"] = 1
if not form.has_key("errors"): config["verbose"] = 1
if form.has_key("intern"):
    config["internlinks"].append(re.compile("^(ftp|https?)://"+\
    linkcheck.lc_cgi.getHostName(form)))
else:
    config["internlinks"].append(re.compile(".+"))
# avoid checking of local files (security!)
config["externlinks"].append((re.compile("^file:"), 1))

# start checking
config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(form["url"].value, 0))
linkcheck.checkUrls(config)
