#!/usr/bin/env python

import re,cgi,sys,urlparse,time,os

# configuration
sys.stderr = sys.stdout
cgi_dir = "/home/calvin/public_html/cgi-bin"
dist_dir = "/home/calvin/linkchecker-1.1.0"
lc = pylice_dir + "/pylice"
sys.path.insert(0,dist_dir)
cgi.logfile = cgi_dir + "/lc.log"

def testit():
    cgi.test()
    sys.exit(0)


def checkform():
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


def logit():
    logfile = open("/home/calvin/log/linkchecker.log","a")
    logfile.write("\n"+time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time()))+"\n")
    for var in ["HTTP_USER_AGENT","REMOTE_ADDR","REMOTE_HOST","REMOTE_PORT"]:
        if os.environ.has_key(var):
            logfile.write(var+"="+os.environ[var]+"\n")
    for key in ["level","url","anchors","errors","intern"]:
        if form.has_key(key):
            logfile.write(str(form[key])+"\n")
    logfile.close()

    
def printError():
    print """<html><head></head>
<body text="#192c83" bgcolor="#fff7e5" link="#191c83" vlink="#191c83" 
alink="#191c83" >
<blockquote>
<b>Error</b><br>
The LinkChecker Online script has encountered an error. Please ensure
that your provided URL link begins with <code>http://</code> and 
contains only these characters: <code>A-Za-z0-9./_~-</code><br><br>
Errors are logged.
</blockquote>
</body>
</html>
"""
    
# main
print "Content-type: text/html"
print
#testit()
form = cgi.FieldStorage()
if not checkform():
    logit()
    printError()
    sys.exit(0)
args=["", "-H", "-r "+form["level"].value, "-s"]
if form.has_key("anchors"):
    args.append("-a")
if not form.has_key("errors"):
    args.append("-v")
if form.has_key("intern"):
    args.append("--intern=^(ftp|http)://"+getHostName())
else:
    args.append("--extern=^file:")
    args.append("--intern=.+")

args.append(form["url"].value)
sys.argv = args
execfile(lc)
    
