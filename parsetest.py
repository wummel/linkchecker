import sys,StringIO,LinkChecker

def linkcheck(urls):
    "Check a list of http://, file:// etc. urls"
    config = LinkChecker.Config.Configuration()
    config["verbose"]=1
    config["warnings"]=1
    # no more options, use defaults
    
    # add urls
    for url in urls:
        config.appendUrl(LinkChecker.UrlData.GetUrlDataFrom(url, 0))
    
    # check it
    LinkChecker.checkUrls(config)

old_stdout = sys.stdout
sys.stdout = StringIO.StringIO()
linkcheck(['http://fsinfo.cs.uni-sb.de/~calvin'])
sys.stdout.seek(0)
reader = LinkChecker.OutputReader.OutputReader()
old_stdout.write(sys.stdout.getvalue())
result =  reader.parse(sys.stdout)
sys.stdout = old_stdout
for url in result:
    print str(url)
