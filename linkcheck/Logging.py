"""Logger classes.

Every Logger has to implement the following functions:
init(self)
  Called once to initialize the Logger. Why do we not use __init__(self)?
  Because we initialize the start time in init and __init__ gets not
  called at the time the checking starts.

newUrl(self,urlData)
  Called every time an url finished checking. All data we checked is in
  the UrlData object urlData.

endOfOutput(self)
  Called at the end of checking to close filehandles and such.
"""
import sys,time,Config,StringUtil

# ANSI color codes
ESC="\x1b"
COL_PARENT  =ESC+"[37m"   # white
COL_URL     =ESC+"[0m"    # standard
COL_REAL    =ESC+"[36m"   # cyan
COL_BASE    =ESC+"[35m"   # magenty
COL_VALID   =ESC+"[1;32m" # green
COL_INVALID =ESC+"[1;31m" # red
COL_INFO    =ESC+"[0m"    # standard
COL_WARNING =ESC+"[1;33m" # yellow
COL_DLTIME  =ESC+"[0m"    # standard
COL_RESET   =ESC+"[0m"    # reset to standard

# HTML colors
ColorBackground="\"#fff7e5\""
ColorUrl="\"#dcd5cf\""
ColorBorder="\"#000000\""
ColorLink="\"#191c83\""
TableWarning="<td bgcolor=\"#e0954e\">"
TableError="<td bgcolor=\"db4930\">"
TableOK="<td bgcolor=\"3ba557\">"
RowEnd="</td></tr>\n"
MyFont="<font face=\"Lucida,Verdana,Arial,sans-serif,Helvetica\">"

# return formatted time
def _strtime(t):
    return time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t))

class StandardLogger:
    """Standard text logger.
    Informal text output format spec:
    Output consists of a set of URL logs separated by one or more
    blank lines.
    A URL log consists of two or more lines. Each line consists of
    keyword and data, separated by whitespace.
    Keywords:
    Real URL (necessary)
    Result   (necessary)
    Base
    Parent URL
    Info
    Warning
    D/L Time
    Check Time
    
    Unknown keywords will be ignored.
    """

    def __init__(self, fd=sys.stdout):
        self.errors=0
        self.warnings=0
        self.fd = fd


    def init(self):
        self.starttime = time.time()
        self.fd.write(Config.AppInfo+"\n"+
                      Config.Freeware+"\n"+
                      "Get the newest version at "+Config.Url+"\n"+
                      "Write comments and bugs to "+Config.Email+"\n\n"+
                      "Start checking at "+_strtime(self.starttime)+"\n")
        self.fd.flush()


    def newUrl(self, urldata):
        self.fd.write("\nURL        "+urldata.urlName)
        if urldata.cached:
            self.fd.write(" (cached)\n")
        else:
            self.fd.write("\n")
        if urldata.parentName:
            self.fd.write("Parent URL "+urldata.parentName+", line "+
	                  str(urldata.line)+"\n")
        if urldata.baseRef:
            self.fd.write("Base       "+urldata.baseRef+"\n")
        if urldata.url:
            self.fd.write("Real URL   "+urldata.url+"\n")
        if urldata.downloadtime:
            self.fd.write("D/L Time   %.3f seconds\n" % urldata.downloadtime)
        if urldata.checktime:
            self.fd.write("Check Time %.3f seconds\n" % urldata.checktime)
        if urldata.infoString:
            self.fd.write("Info       "+StringUtil.indent(
                StringUtil.blocktext(urldata.infoString, 65), 11)+"\n")
        if urldata.warningString:
            self.warnings = self.warnings+1
            self.fd.write("Warning    "+StringUtil.indent(
                StringUtil.blocktext(urldata.warningString, 65), 11)+"\n")
        
        self.fd.write("Result     ")
        if urldata.valid:
            self.fd.write(urldata.validString+"\n")
        else:
            self.errors = self.errors+1
            self.fd.write(urldata.errorString+"\n")
        self.fd.flush()


    def endOfOutput(self):
        self.fd.write("\nThats it. ")

        if self.warnings==1:
            self.fd.write("1 warning, ")
        else:
            self.fd.write(str(self.warnings)+" warnings, ")
        if self.errors==1:
            self.fd.write("1 error")
        else:
            self.fd.write(str(self.errors)+" errors")
        self.fd.write(" found.\n")
        self.stoptime = time.time()
        self.fd.write("Stopped checking at "+_strtime(self.stoptime)+
	              (" (%.3f seconds)" % (self.stoptime - self.starttime))+
                      "\n")
        self.fd.flush()
        self.fd = None



class HtmlLogger(StandardLogger):
    """Logger with HTML output"""

    def init(self):
        self.starttime = time.time()
        self.fd.write("<html><head><title>"+Config.AppName+"</title></head>"+
              "<body bgcolor="+ColorBackground+" link="+ColorLink+
              " vlink="+ColorLink+" alink="+ColorLink+">"+
              "<center><h2>"+MyFont+Config.AppName+"</font>"+
              "</center></h2>"+
              "<br><blockquote>"+Config.Freeware+"<br><br>"+
              "Start checking at "+_strtime(self.starttime)+"<br><br>")
        self.fd.flush()


    def newUrl(self, urlData):
        self.fd.write("<table align=left border=\"0\" cellspacing=\"0\""
              " cellpadding=\"1\" bgcolor="+ColorBorder+
              "><tr><td><table align=left border=\"0\" cellspacing=\"0\""
              " cellpadding=\"3\" bgcolor="+ColorBackground+
              "><tr><td bgcolor="+ColorUrl+">"+
              MyFont+"URL</font></td><td bgcolor="+ColorUrl+">"+MyFont+
              StringUtil.htmlify(urlData.urlName))
        if urlData.cached:
            self.fd.write("(cached)")
        self.fd.write("</font>"+RowEnd)
        
        if urlData.parentName:
            self.fd.write("<tr><td>"+MyFont+"Parent URL</font></td><td>"+
			      MyFont+"<a href=\""+urlData.parentName+"\">"+
                  urlData.parentName+"</a> line "+str(urlData.line)+
                  "</font>"+RowEnd)
        if urlData.baseRef:
            self.fd.write("<tr><td>"+MyFont+"Base</font></td><td>"+MyFont+
                  urlData.baseRef+"</font>"+RowEnd)
        if urlData.url:
            self.fd.write("<tr><td>"+MyFont+"Real URL</font></td><td>"+MyFont+
                  "<a href=\""+StringUtil.htmlify(urlData.url)+"\">"+
                  urlData.url+"</a></font>"+RowEnd)
        if urlData.downloadtime:
            self.fd.write("<tr><td>"+MyFont+"D/L Time</font></td><td>"+MyFont+
                  ("%.3f" % urlData.downloadtime)+" seconds</font>"+RowEnd)
        if urlData.checktime:
            self.fd.write("<tr><td>"+MyFont+"Check Time</font></td><td>"+
	          MyFont+("%.3f" % urlData.checktime)+" seconds</font>"+
		  RowEnd)
        if urlData.infoString:
            self.fd.write("<tr><td>"+MyFont+"Info</font></td><td>"+MyFont+
                  StringUtil.htmlify(urlData.infoString)+"</font>"+RowEnd)
        if urlData.warningString:
            self.warnings = self.warnings+1
            self.fd.write("<tr>"+TableWarning+MyFont+"Warning</font></td>"+
                  TableWarning+MyFont+urlData.warningString+
                  "</font>"+RowEnd)
        if urlData.valid:
            self.fd.write("<tr>"+TableOK+MyFont+"Result</font></td>"+
                  TableOK+MyFont+urlData.validString+"</font>"+RowEnd)
        else:
            self.errors = self.errors+1
            self.fd.write("<tr>"+TableError+MyFont+"Result</font></td>"+
                  TableError+MyFont+urlData.errorString+"</font>"+RowEnd)
        
        self.fd.write("</table></td></tr></table><br clear=all><br>")
        self.fd.flush()        

        
    def endOfOutput(self):
        self.fd.write(MyFont+"Thats it. ")
        if self.warnings==1:
            self.fd.write("1 warning, ")
        else:
            self.fd.write(str(self.warnings)+" warnings, ")
        if self.errors==1:
            self.fd.write("1 error")
        else:
            self.fd.write(str(self.errors)+" errors")
        self.fd.write(" found.<br>")
        self.stoptime = time.time()
        self.fd.write("Stopped checking at"+_strtime(self.stoptime)+
              (" (%.3f seconds)" % (self.stoptime - self.starttime))+
	      "</font></blockquote><br><hr noshade size=1><small>"+
              MyFont+Config.HtmlAppInfo+"<br>Get the newest version at "
              "<a href=\""+Config.Url+"\">"+Config.Url+
              "</a>.<br>Write comments and bugs to <a href=\"mailto:"+
              Config.Email+"\">"+Config.Email+
              "</a>.</font></small></body></html>")
        self.fd.flush()        
        self.fd = None


class ColoredLogger(StandardLogger):
    """ANSI colorized output"""

    def __init__(self, fd=sys.stdout):
        StandardLogger.__init__(self, fd)
        self.currentPage = None
        self.prefix = 0

    def newUrl(self, urlData):
        if urlData.parentName:
            if self.currentPage != urlData.parentName:
                if self.prefix:
                    self.fd.write("o\n")
                self.fd.write("\nParent URL "+COL_PARENT+urlData.parentName+
  	                      COL_RESET+"\n")
                self.currentPage = urlData.parentName
                self.prefix = 1
        else:
            if self.prefix:
                self.fd.write("o\n")
            self.prefix = 0
            self.currentPage=None
            
        if self.prefix:
            self.fd.write("|\n+- ")
        else:
            self.fd.write("\n")
        self.fd.write("URL       "+COL_URL+urlData.urlName+COL_RESET)
        if urlData.line: self.fd.write(", line "+`urlData.line`+"")
        if urlData.cached:
            self.fd.write(" (cached)\n")
        else:
            self.fd.write("\n")
            
        if urlData.baseRef:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write("Base      "+COL_BASE+urlData.baseRef+COL_RESET+"\n")
            
        if urlData.url:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write("Real URL  "+COL_REAL+urlData.url+COL_RESET+"\n")
        if urlData.downloadtime:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write("D/L Time  "+COL_DLTIME+
	        ("%.3f" % urlData.downloadtime)+" seconds"+COL_RESET+"\n")
        if urlData.checktime:
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write("Check Time "+COL_DLTIME+
	        ("%.3f" % urlData.checktime)+" seconds"+COL_RESET+"\n")
            
        if urlData.infoString:
            if self.prefix:
                self.fd.write("|   Info      "+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "|             "))
            else:
                self.fd.write("Info          "+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "              "))
            self.fd.write(COL_RESET+"\n")
            
        if urlData.warningString:
            self.warnings = self.warnings+1
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write("Warning   "+COL_WARNING+urlData.warningString+
			            COL_RESET+"\n")

        if self.prefix:
            self.fd.write("|  ")
        self.fd.write("Result    ")
        if urlData.valid:
            self.fd.write(COL_VALID+urlData.validString+COL_RESET+"\n")
        else:
            self.errors = self.errors+1
            self.fd.write(COL_INVALID+urlData.errorString+COL_RESET+"\n")
        self.fd.flush()        


    def endOfOutput(self):
        if self.prefix:
            self.fd.write("o\n")
        StandardLogger.endOfOutput(self)


class GMLLogger(StandardLogger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """
    def __init__(self,fd=sys.stdout):
        StandardLogger.__init__(self,fd)
        self.nodes = []

    def init(self):
        self.fd.write("# created by "+Config.AppName+" at "+
	     _strtime(time.time())+
	    "\n# you get "+Config.AppName+" at "+Config.Url+
            "\n# write comments and bugs to "+Config.Email+
	    "\ngraph [\n  directed 1\n")
        self.fd.flush()

    def newUrl(self, urlData):
        self.nodes.append(urlData)

    def endOfOutput(self):
        writtenNodes = {}
        # write nodes
        nodeid = 1
        for node in self.nodes:
            if node.url and not writtenNodes.has_key(node.url):
                self.fd.write("  node [\n")
		self.fd.write("    id     "+`nodeid`+"\n")
                self.fd.write('    label  "'+node.url+'"'+"\n")
                if node.downloadtime:
                    self.fd.write("    dltime "+`node.downloadtime`+"\n")
                if node.checktime:
                    self.fd.write("    checktime "+`node.checktime`+"\n")
                self.fd.write("    extern ")
		if node.extern: self.fd.write("1")
		else: self.fd.write("0")
		self.fd.write("\n  ]\n")
                writtenNodes[node.url] = nodeid
                nodeid = nodeid + 1
        # write edges
        for node in self.nodes:
            if node.url and node.parentName:
                self.fd.write("  edge [\n")
		self.fd.write('    label  "'+node.urlName+'"\n')
	        self.fd.write("    source "+`writtenNodes[node.parentName]`+
		              "\n")
                self.fd.write("    target "+`writtenNodes[node.url]`+"\n")
                self.fd.write("    valid  ")
                if node.valid: self.fd.write("1")
                else: self.fd.write("0")
                self.fd.write("\n  ]\n")
        # end of output
        self.fd.write("]\n")
        self.fd.flush()
        self.fd = None


class SQLLogger(StandardLogger):
    """ SQL output for PostgreSQL, not tested"""
    def init(self):
        self.fd.write("-- created by "+Config.AppName+" at "+
                _strtime(time.time())+
		"\n-- you get "+Config.AppName+" at "+Config.Url+
		"\n-- write comments and bugs to "+Config.Email+"\n\n")
        self.fd.flush()

    def newUrl(self, urlData):
        self.fd.write("insert into linksdb(urlname,recursionlevel,parentname,"
	              "baseref,errorstring,validstring,warningstring,"
		      "infoString,valid,url,line,cached) values '"+
                      urlData.urlName+"',"+
		      `urlData.recursionLevel`+","+
		      StringUtil.sqlify(urlData.parentName)+","+
                      StringUtil.sqlify(urlData.baseRef)+","+
                      StringUtil.sqlify(urlData.errorString)+","+
                      StringUtil.sqlify(urlData.validString)+","+
                      StringUtil.sqlify(urlData.warningString)+","+
                      StringUtil.sqlify(urlData.infoString)+","+
                      `urlData.valid`+","+
                      StringUtil.sqlify(urlData.url)+","+
                      `urlData.line`+","+
                      `urlData.cached`+");\n")
        self.fd.flush()

    def endOfOutput(self):
        self.fd = None


class BlacklistLogger:
    """Updates a blacklist of wrong links"""
    def __init__(self, filename):
        self.blacklist = {}
        self.filename = filename

    def init(self):
        """initialize the blacklist"""
        pass

    def newUrl(self, urlData):
        if urlData.valid:
            self.blacklist[urlData.getCacheKey()] = None
        elif not urlData.cached:
            self.blacklist[urlData.getCacheKey()] = urlData

    def endOfOutput(self):
        """write the blacklist"""
        pass
