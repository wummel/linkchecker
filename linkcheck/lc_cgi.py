import re,time,urlparse

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

def getHostName(form):
    return urlparse.urlparse(form["url"].value)[1]

def logit(form, env):
    log = open("linkchecker.log","a")
    log.write("\n"+time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time()))+"\n")
    for var in ["HTTP_USER_AGENT","REMOTE_ADDR","REMOTE_HOST","REMOTE_PORT"]:
        if env.has_key(var):
            log.write(var+"="+env[var]+"\n")
    for key in ["level","url","anchors","errors","intern"]:
        if form.has_key(key):
            log.write(str(form[key])+"\n")
    log.close()

def printError(out):
    out.write("""<html><head></head>
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
