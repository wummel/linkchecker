#!/usr/bin/env python

import sys, re, os
dist_dir = "/home/calvin/projects/linkchecker"
sys.path.insert(0,dist_dir)
import fcgi

# main
try:
    while fcgi.isFCGI():
        req = fcgi.FCGI()
        req.out.write("Content-type: text/html\r\n"
                      "Cache-Control: no-cache\r\n"
                      "\r\n")
        form = req.getFieldStorage()
        if form['language'].value == 'de':
            os.environ['LC_MESSAGES'] = 'de'
        elif form['language'].value == 'fr':
            os.environ['LC_MESSAGES'] = 'fr'
        else:
            os.environ['LC_MESSAGES'] = 'C'
        import linkcheck
        if not linkcheck.lc_cgi.checkform(form):
            linkcheck.lc_cgi.logit(form, req.env)
            linkcheck.lc_cgi.printError(req.out)
            req.Finish()
            continue
        config = linkcheck.Config.Configuration()
        config["recursionlevel"] = int(form["level"].value)
        config["log"] = config.newLogger('html', {'fd':req.out})
        config.disableThreading()
        if form.has_key('strict'): config['strict'] = 1
        if form.has_key("anchors"): config["anchors"] = 1
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
        req.Finish()
except:
    import traceback
    traceback.print_exc(file = open('traceback', 'a'))

