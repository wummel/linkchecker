#!/usr/bin/env python

import re, sys, time, os, urlparse

def checkform(form):
    for key in ["level","url"]:
        if not form.has_key(key) or form[key].value == "": return 0
    if not re.match(r"^http://[-\w./~]+$", form["url"].value): return 0
    if not re.match(r"\d", form["level"].value): return 0
    if int(form["level"].value) > 3: return 0
    if form.has_key("anchors"):
        if not form["anchors"].value=="on": return 0
    if form.has_key("errors"):
        if not form["errors"].value=="on": return 0
    if form.has_key("intern"):
        if not form["intern"].value=="on": return 0
    return 1

def getHostName():
    return urlparse.urlparse(form["url"].value)[1]

def logit(form, req):
    log = open("linkchecker.log","a")
    log.write("\n"+time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time())))
    for var in ["HTTP_USER_AGENT","REMOTE_ADDR","REMOTE_HOST","REMOTE_PORT"]:
        if req.env.has_key(var):
            log.write(var+"="+req.env[var])
    for key in ["level","url","anchors","errors","intern"]:
        if form.has_key(key):
            log.write(str(form[key]))
    log.close()

def printError(req):
    req.out.write("""<html><head></head>
<body text="#192c83" bgcolor="#fff7e5" link="#191c83" vlink="#191c83"
alink="#191c83">
<blockquote>
<b>Error</b><br>
The LinkChecker Online script has encountered an error. Please ensure
that your provided URL link begins with <code>http://</code> and 
contains only these characters: <code>A-Za-z0-9./_~-</code><br><br>
Errors are logged.
</blockquote>
</body>
</html>""")
    req.Finish()

dist_dir = "/home/calvin/projects/linkchecker"
sys.path.insert(0,dist_dir)
import fcgi, linkcheck

# main
try:
    while isFCGI():
        req = FCGI()
        req.out.write("Content-type: text/html\r\n"
                      "Cache-Control: no-cache\r\n"
                      "\r\n")
        form = req.getFieldStorage()
        if not checkform(form):
            logit(form, req)
            printError(req)
            continue
        config = linkcheck.Config.Configuration()
        config["recursionlevel"] = int(form["level"].value)
        config["log"] = linkcheck.Logging.HtmlLogger()
        config.disableThreading()
        if form.has_key("anchors"):    config["anchors"] = 1
        if not form.has_key("errors"): config["verbose"] = 1
        if form.has_key("intern"):
            config["internlinks"].append(re.compile("^(ftp|https?)://"+getHostName()))
        else:
            config["internlinks"].append(re.compile(".+"))
        # avoid checking of local files
        config["externlinks"].append((re.compile("^file:"), 1))
        # start checking
        config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(form["url"].value, 0))
        linkcheck.checkUrls(config)
        req.Finish()
except:
    import traceback
    traceback.print_exc(file = open('traceback', 'w'))

