"""Output logging support for different formats"""
# Copyright (C) 2000,2001  Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import sys, time
from types import ListType
import Config, StringUtil
import linkcheck

LogFields = {
    "realurl": "Real URL",
    "result": "Result",
    "base": "Base",
    "name": "Name",
    "parenturl": "Parent URL",
    "extern": "Extern",
    "info": "Info",
    "warning": "Warning",
    "dltime": "D/L Time",
    "checktime": "Check Time",
    "url": "URL",
}
MaxIndent = max(map(lambda x: len(linkcheck._(x)), LogFields.values()))+1
Spaces = {}
for key,value in LogFields.items():
    Spaces[key] = " "*(MaxIndent - len(linkcheck._(value)))

EntityTable = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;',
    '\'': '&apos;',
}

def quote(s):
    res = list(s)
    for i in range(len(res)):
        c = res[i]
        res[i] = EntityTable.get(c, c)
    return ''.join(res)

# return formatted time
def _strtime(t):
    return time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t))

class Logger:
    def __init__(self, **args):
        self.logfields = None # all fields
        if args.has_key('fields'):
            if "all" not in args['fields']:
                self.logfields = args['fields']


    def logfield(self, name):
        if self.logfields is None:
            return 1
        return name in self.logfields


    def init(self):
        raise Exception, "abstract function"

    def newUrl(self, urlData):
        raise Exception, "abstract function"

    def endOfOutput(self, linknumber=-1):
        raise Exception, "abstract function"



class StandardLogger(Logger):
    """Standard text logger.

Every Logger has to implement the following functions:
init(self)
  Called once to initialize the Logger. Why do we not use __init__(self)?
  Because we initialize the start time in init and __init__ gets not
  called at the time the checking starts but when the logger object is
  created.
  Another reason is that we dont want might create several loggers
  as a default and then switch to another configured output. So we
  must not print anything out at __init__ time.

newUrl(self,urlData)
  Called every time an url finished checking. All data we checked is in
  the UrlData object urlData.

endOfOutput(self)
  Called at the end of checking to close filehandles and such.

Passing parameters to the constructor:
__init__(self, **args)
  The args dictionary is filled in Config.py. There you can specify
  default parameters. Adjust these parameters in the configuration
  files in the appropriate logger section.

    Informal text output format spec:
    Output consists of a set of URL logs separated by one or more
    blank lines.
    A URL log consists of two or more lines. Each line consists of
    keyword and data, separated by whitespace.
    Unknown keywords will be ignored.
    """

    def __init__(self, **args):
        apply(Logger.__init__, (self,), args)
        self.errors = 0
        #self.warnings = 0
        if args.has_key('fileoutput'):
            self.fd = open(args['filename'], "w")
	elif args.has_key('fd'):
            self.fd = args['fd']
        else:
	    self.fd = sys.stdout


    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield('intro'):
            self.fd.write("%s\n%s\n" % (Config.AppInfo, Config.Freeware))
            self.fd.write(linkcheck._("Get the newest version at %s\n") % Config.Url)
            self.fd.write(linkcheck._("Write comments and bugs to %s\n\n") % Config.Email)
            self.fd.write(linkcheck._("Start checking at %s\n") % _strtime(self.starttime))
            self.fd.flush()


    def newUrl(self, urlData):
        if self.fd is None: return
        if self.logfield('url'):
            self.fd.write("\n"+linkcheck._(LogFields['url'])+Spaces['url']+urlData.urlName)
            if urlData.cached:
                self.fd.write(linkcheck._(" (cached)\n"))
            else:
                self.fd.write("\n")
        if urlData.name and self.logfield('name'):
            self.fd.write(linkcheck._(LogFields["name"])+Spaces["name"]+urlData.name+"\n")
        if urlData.parentName and self.logfield('parenturl'):
            self.fd.write(linkcheck._(LogFields['parenturl'])+Spaces["parenturl"]+
	                  urlData.parentName+linkcheck._(", line ")+
	                  str(urlData.line)+"\n")
        if urlData.baseRef and self.logfield('base'):
            self.fd.write(linkcheck._(LogFields["base"])+Spaces["base"]+urlData.baseRef+"\n")
        if urlData.url and self.logfield('realurl'):
            self.fd.write(linkcheck._(LogFields["realurl"])+Spaces["realurl"]+urlData.url+"\n")
        if urlData.downloadtime and self.logfield('dltime'):
            self.fd.write(linkcheck._(LogFields["dltime"])+Spaces["dltime"]+
	                  linkcheck._("%.3f seconds\n") % urlData.downloadtime)
        if urlData.checktime and self.logfield('checktime'):
            self.fd.write(linkcheck._(LogFields["checktime"])+Spaces["checktime"]+
	                  linkcheck._("%.3f seconds\n") % urlData.checktime)
        if urlData.infoString and self.logfield('info'):
            self.fd.write(linkcheck._(LogFields["info"])+Spaces["info"]+
	                  StringUtil.indent(
                          StringUtil.blocktext(urlData.infoString, 65),
			  MaxIndent)+"\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.logfield('warning'):
                self.fd.write(linkcheck._(LogFields["warning"])+Spaces["warning"]+
	                  StringUtil.indent(
                          StringUtil.blocktext(urlData.warningString, 65),
			  MaxIndent)+"\n")

        if self.logfield('result'):
            self.fd.write(linkcheck._(LogFields["result"])+Spaces["result"])
            if urlData.valid:
                self.fd.write(urlData.validString+"\n")
            else:
                self.errors += 1
                self.fd.write(urlData.errorString+"\n")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        if self.logfield('outro'):
            self.fd.write(linkcheck._("\nThats it. "))
            #if self.warnings==1:
            #    self.fd.write(linkcheck._("1 warning, "))
            #else:
            #    self.fd.write(str(self.warnings)+linkcheck._(" warnings, "))
            if self.errors==1:
                self.fd.write(linkcheck._("1 error"))
            else:
                self.fd.write(str(self.errors)+linkcheck._(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(linkcheck._(" in 1 link"))
                else:
                    self.fd.write(linkcheck._(" in %d links") % linknumber)
            self.fd.write(linkcheck._(" found\n"))
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write(linkcheck._("Stopped checking at %s") % _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None

HTML_HEADER = """<!DOCTYPE html PUBLIC "-//W3C//DTD html 4.0//EN">
<html><head><title>%s</title>
<style type="text/css">\n<!--
 h2 { font-family: Verdana,sans-serif; font-size: 22pt;
 font-style: bold; font-weight: bold }
 body { font-family: Arial,sans-serif; font-size: 11pt }
 td   { font-family: Arial,sans-serif; font-size: 11pt }
 code { font-family: Courier }
 a:hover { color: #34a4ef }
 //-->
</style></head>
<body bgcolor=%s link=%s vlink=%s alink=%s>
"""

class HtmlLogger(StandardLogger):
    """Logger with HTML output"""

    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        self.fd.write(HTML_HEADER%(Config.App, self.colorbackground,
                      self.colorlink, self.colorlink, self.colorlink))
        if self.logfield('intro'):
            self.fd.write("<center><h2>"+Config.App+"</h2></center>"+
              "<br><blockquote>"+Config.Freeware+"<br><br>"+
              (linkcheck._("Start checking at %s\n") % _strtime(self.starttime))+
	      "<br><br>")
        self.fd.flush()


    def newUrl(self, urlData):
        if self.fd is None: return
        self.fd.write('<table align=left border=0 cellspacing=0'
              ' cellpadding=1 bgcolor='+self.colorborder+' summary=Border'
              '><tr><td><table align=left border=0 cellspacing=0'
              ' cellpadding=3 summary="checked link" bgcolor='+
	      self.colorbackground+
              ">")
        if self.logfield("url"):
	    self.fd.write("<tr><td bgcolor="+self.colorurl+">"+linkcheck._("URL")+
              "</td><td bgcolor="+self.colorurl+">"+urlData.urlName)
            if urlData.cached:
                self.fd.write(linkcheck._(" (cached)\n"))
            self.fd.write("</td></tr>\n")
        if urlData.name and self.logfield("name"):
            self.fd.write("<tr><td>"+linkcheck._("Name")+"</td><td>"+
                          urlData.name+"</td></tr>\n")
        if urlData.parentName and self.logfield("parenturl"):
            self.fd.write("<tr><td>"+linkcheck._("Parent URL")+"</td><td>"+
			  '<a href="'+urlData.parentName+'">'+
                          urlData.parentName+"</a> line "+str(urlData.line)+
                          "</td></tr>\n")
        if urlData.baseRef and self.logfield("base"):
            self.fd.write("<tr><td>"+linkcheck._("Base")+"</td><td>"+
	                  urlData.baseRef+"</td></tr>\n")
        if urlData.url and self.logfield("realurl"):
            self.fd.write("<tr><td>"+linkcheck._("Real URL")+"</td><td>"+
	                  "<a href=\""+urlData.url+
			  '">'+urlData.url+"</a></td></tr>\n")
        if urlData.downloadtime and self.logfield("dltime"):
            self.fd.write("<tr><td>"+linkcheck._("D/L Time")+"</td><td>"+
	                  (linkcheck._("%.3f seconds") % urlData.downloadtime)+
			  "</td></tr>\n")
        if urlData.checktime and self.logfield("checktime"):
            self.fd.write("<tr><td>"+linkcheck._("Check Time")+
	                  "</td><td>"+
			  (linkcheck._("%.3f seconds") % urlData.checktime)+
			  "</td></tr>\n")
        if urlData.infoString and self.logfield("info"):
            self.fd.write("<tr><td>"+linkcheck._("Info")+"</td><td>"+
	                  StringUtil.htmlify(urlData.infoString)+
			  "</td></tr>\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.logfield("warning"):
                self.fd.write("<tr>"+self.tablewarning+linkcheck._("Warning")+
	                  "</td>"+self.tablewarning+
                          urlData.warningString.replace("\n", "<br>")+
			  "</td></tr>\n")
        if self.logfield("result"):
            if urlData.valid:
                self.fd.write("<tr>"+self.tableok+linkcheck._("Result")+"</td>"+
                  self.tableok+urlData.validString+"</td></tr>\n")
            else:
                self.errors += 1
                self.fd.write("<tr>"+self.tableerror+linkcheck._("Result")+
	                  "</td>"+self.tableerror+
			  urlData.errorString+"</td></tr>\n")

        self.fd.write("</table></td></tr></table><br clear=all><br>")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        if self.logfield("outro"):
            self.fd.write(linkcheck._("\nThats it. "))
            #if self.warnings==1:
            #    self.fd.write(linkcheck._("1 warning, "))
            #else:
            #    self.fd.write(str(self.warnings)+linkcheck._(" warnings, "))
            if self.errors==1:
                self.fd.write(linkcheck._("1 error"))
            else:
                self.fd.write(str(self.errors)+linkcheck._(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(linkcheck._(" in 1 link"))
                else:
                    self.fd.write(linkcheck._(" in %d links") % linknumber)
            self.fd.write(linkcheck._(" found\n")+"<br>")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write(linkcheck._("Stopped checking at %s") % _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write("	(%.3f %s)\n" % (duration, name))
            self.fd.write("</blockquote><br><hr noshade size=1><small>"+
             Config.HtmlAppInfo+"<br>")
            self.fd.write(linkcheck._("Get the newest version at %s\n") %\
             ('<a href="'+Config.Url+'" target="_top">'+Config.Url+
	      "</a>.<br>"))
            self.fd.write(linkcheck._("Write comments and bugs to %s\n\n") %\
	     ("<a href=\"mailto:"+Config.Email+"\">"+Config.Email+"</a>."))
            self.fd.write("</small></body></html>")
        self.fd.flush()
        self.fd = None


class ColoredLogger(StandardLogger):
    """ANSI colorized output"""

    def __init__(self, **args):
        esc="\x1b[%sm"
        apply(StandardLogger.__init__, (self,), args)
        self.colorparent = esc % args['colorparent']
        self.colorurl = esc % args['colorurl']
        self.colorname = esc % args['colorname']
        self.colorreal = esc % args['colorreal']
        self.colorbase = esc % args['colorbase']
        self.colorvalid = esc % args['colorvalid']
        self.colorinvalid = esc % args['colorinvalid']
        self.colorinfo = esc % args['colorinfo']
        self.colorwarning = esc % args['colorwarning']
        self.colordltime = esc % args['colordltime']
        self.colorreset = esc % args['colorreset']
        self.currentPage = None
        self.prefix = 0

    def newUrl(self, urlData):
        if self.fd is None: return
        if self.logfield("parenturl"):
            if urlData.parentName:
                if self.currentPage != urlData.parentName:
                    if self.prefix:
                        self.fd.write("o\n")
                    self.fd.write("\n"+linkcheck._("Parent URL")+Spaces["parenturl"]+
		              self.colorparent+urlData.parentName+
			      self.colorreset+"\n")
                    self.currentPage = urlData.parentName
                    self.prefix = 1
            else:
                if self.prefix:
                    self.fd.write("o\n")
                self.prefix = 0
                self.currentPage=None
        if self.logfield("url"):
            if self.prefix:
                self.fd.write("|\n+- ")
            else:
                self.fd.write("\n")
            self.fd.write(linkcheck._("URL")+Spaces["url"]+self.colorurl+
	              urlData.urlName+self.colorreset)
            if urlData.line: self.fd.write(linkcheck._(", line ")+`urlData.line`+"")
            if urlData.cached:
                self.fd.write(linkcheck._(" (cached)\n"))
            else:
                self.fd.write("\n")

        if urlData.name and self.logfield("name"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("Name")+Spaces["name"]+self.colorname+
                          urlData.name+self.colorreset+"\n")
        if urlData.baseRef and self.logfield("base"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("Base")+Spaces["base"]+self.colorbase+
	                  urlData.baseRef+self.colorreset+"\n")
            
        if urlData.url and self.logfield("realurl"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("Real URL")+Spaces["realurl"]+self.colorreal+
	                  urlData.url+self.colorreset+"\n")
        if urlData.downloadtime and self.logfield("dltime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("D/L Time")+Spaces["dltime"]+self.colordltime+
	        (linkcheck._("%.3f seconds") % urlData.downloadtime)+self.colorreset+"\n")
        if urlData.checktime and self.logfield("checktime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("Check Time")+Spaces["checktime"]+
                self.colordltime+
	        (linkcheck._("%.3f seconds") % urlData.checktime)+self.colorreset+"\n")
            
        if urlData.infoString and self.logfield("info"):
            if self.prefix:
                self.fd.write("|  "+linkcheck._("Info")+Spaces["info"]+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "|      "+Spaces["info"]))
            else:
                self.fd.write(linkcheck._("Info")+Spaces["info"]+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "    "+Spaces["info"]))
            self.fd.write(self.colorreset+"\n")
            
        if urlData.warningString:
            #self.warnings += 1
            if self.logfield("warning"):
                if self.prefix:
                    self.fd.write("|  ")
                self.fd.write(linkcheck._("Warning")+Spaces["warning"]+
		          self.colorwarning+
	                  urlData.warningString+self.colorreset+"\n")

        if self.logfield("result"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(linkcheck._("Result")+Spaces["result"])
            if urlData.valid:
                self.fd.write(self.colorvalid+urlData.validString+
	                      self.colorreset+"\n")
            else:
                self.errors += 1
                self.fd.write(self.colorinvalid+urlData.errorString+
	                      self.colorreset+"\n")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        if self.logfield("outro"):
            if self.prefix:
                self.fd.write("o\n")
        StandardLogger.endOfOutput(self, linknumber=linknumber)



class GMLLogger(StandardLogger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.nodes = {}
        self.nodeid = 0

    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield("intro"):
            self.fd.write("# "+(linkcheck._("created by %s at %s\n") % (Config.AppName,
                      _strtime(self.starttime))))
            self.fd.write("# "+(linkcheck._("Get the newest version at %s\n") % Config.Url))
            self.fd.write("# "+(linkcheck._("Write comments and bugs to %s\n\n") % \
  	                    Config.Email))
            self.fd.write("graph [\n  directed 1\n")
            self.fd.flush()


    def newUrl(self, urlData):
        """write one node and all possible edges"""
        if self.fd is None: return
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.fd.write("  node [\n")
	    self.fd.write("    id     %d\n" % node.id)
            if self.logfield("realurl"):
                self.fd.write('    label  "%s"\n' % node.url)
            if node.downloadtime and self.logfield("dltime"):
                self.fd.write("    dltime %d\n" % node.downloadtime)
            if node.checktime and self.logfield("checktime"):
                self.fd.write("    checktime %d\n" % node.checktime)
            if self.logfield("extern"):
                self.fd.write("    extern %d\n" % (node.extern and 1 or 0))
	    self.fd.write("  ]\n")
        self.writeEdges()


    def writeEdges(self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  edge [\n")
		self.fd.write('    label  "%s"\n' % node.urlName)
                if self.logfield("parenturl"):
                    self.fd.write("    source %d\n" % \
	                          self.nodes[node.parentName].id)
                self.fd.write("    target %d\n" % node.id)
                if self.logfield("result"):
                    self.fd.write("    valid  %d\n" % (node.valid and 1 or 0))
                self.fd.write("  ]\n")
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        self.fd.write("]\n")
        if self.logfield("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("# "+linkcheck._("Stopped checking at %s") % \
	              _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None



class XMLLogger(StandardLogger):
    """XML output mirroring the GML structure. Easy to parse with any XML
       tool."""
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.nodes = {}
        self.nodeid = 0

    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        self.fd.write('<?xml version="1.0"?>\n')
        if self.logfield("intro"):
            self.fd.write("<!--\n")
            self.fd.write("  "+linkcheck._("created by %s at %s\n") % \
	              (Config.AppName, _strtime(self.starttime)))
            self.fd.write("  "+linkcheck._("Get the newest version at %s\n") % Config.Url)
            self.fd.write("  "+linkcheck._("Write comments and bugs to %s\n\n") % \
	              Config.Email)
            self.fd.write("-->\n\n")
	self.fd.write('<GraphXML>\n<graph isDirected="true">\n')
        self.fd.flush()

    def newUrl(self, urlData):
        """write one node and all possible edges"""
        if self.fd is None: return
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.fd.write('  <node name="%d" ' % node.id)
            self.fd.write(">\n")
            if self.logfield("realurl"):
                self.fd.write("    <label>%s</label>\n" % quote(node.url))
            self.fd.write("    <data>\n")
            if node.downloadtime and self.logfield("dltime"):
                self.fd.write("      <dltime>%f</dltime>\n" \
                                  % node.downloadtime)
            if node.checktime and self.logfield("checktime"):
                self.fd.write("      <checktime>%f</checktime>\n" \
                              % node.checktime)
            if self.logfield("extern"):
                self.fd.write("      <extern>%d</extern>\n" % \
	                  (node.extern and 1 or 0))
            self.fd.write("    </data>\n")
	    self.fd.write("  </node>\n")
        self.writeEdges()

    def writeEdges(self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  <edge")
                self.fd.write(' source="%d"' % \
		              self.nodes[node.parentName].id)
                self.fd.write(' target="%d"' % node.id)
                self.fd.write(">\n")
                if self.logfield("url"):
		    self.fd.write("    <label>%s</label>\n" % quote(node.urlName))
                self.fd.write("    <data>\n")
                if self.logfield("result"):
                    self.fd.write("      <valid>%d</valid>\n" % \
		              (node.valid and 1 or 0))
                self.fd.write("    </data>\n")
                self.fd.write("  </edge>\n")
        self.fd.flush()

    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        self.fd.write("</graph>\n</GraphXML>\n")
        if self.logfield("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("<!-- ")
            self.fd.write(linkcheck._("Stopped checking at %s") % _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
            self.fd.write("-->")
        self.fd.flush()
        self.fd = None



class SQLLogger(StandardLogger):
    """ SQL output for PostgreSQL, not tested"""
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.dbname = args['dbname']
        self.separator = args['separator']


    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield("intro"):
            self.fd.write("-- "+(linkcheck._("created by %s at %s\n") % (Config.AppName,
                       _strtime(self.starttime))))
            self.fd.write("-- "+(linkcheck._("Get the newest version at %s\n") % Config.Url))
            self.fd.write("-- "+(linkcheck._("Write comments and bugs to %s\n\n") % \
	                Config.Email))
            self.fd.flush()

    def newUrl(self, urlData):
        if self.fd is None: return
        self.fd.write("insert into %s(urlname,recursionlevel,parentname,"
              "baseref,errorstring,validstring,warningstring,infoString,"
	      "valid,url,line,name,checktime,downloadtime,cached) values "
              "(%s,%d,%s,%s,%s,%s,%s,%s,%d,%s,%d,%s,%d,%d,%d)%s\n" % \
	      (self.dbname,
	       StringUtil.sqlify(urlData.urlName),
               urlData.recursionLevel,
	       StringUtil.sqlify(urlData.parentName),
               StringUtil.sqlify(urlData.baseRef),
               StringUtil.sqlify(urlData.errorString),
               StringUtil.sqlify(urlData.validString),
               StringUtil.sqlify(urlData.warningString),
               StringUtil.sqlify(urlData.infoString),
               urlData.valid,
               StringUtil.sqlify(urlData.url),
               urlData.line,
               StringUtil.sqlify(urlData.name),
               urlData.checktime,
               urlData.downloadtime,
               urlData.cached,
	       self.separator))
        self.fd.flush()

    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        if self.logfield("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("-- "+linkcheck._("Stopped checking at %s") % \
	              _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write("	(%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None


class BlacklistLogger(Logger):
    """Updates a blacklist of wrong links. If a link on the blacklist
    is working (again), it is removed from the list. So after n days
    we have only links on the list which failed for n days.
    """
    def __init__(self, **args):
        apply(Logger.__init__, (self,), args)
        self.errors = 0
        self.blacklist = {}
        self.filename = args['filename']

    def init(self):
        pass

    def newUrl(self, urlData):
        if urlData.valid:
            self.blacklist[urlData.getCacheKey()] = None
        elif not urlData.cached:
            self.errors = 1
            self.blacklist[urlData.getCacheKey()] = urlData

    def endOfOutput(self, linknumber=-1):
        """write the blacklist"""
        fd = open(self.filename, "w")
        for url in self.blacklist.keys():
            if self.blacklist[url] is None:
                fd.write(url+"\n")


class CSVLogger(StandardLogger):
    """ CSV output. CSV consists of one line per entry. Entries are
    separated by a semicolon.
    """
    def __init__(self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.separator = args['separator']

    def init(self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield("intro"):
            self.fd.write("# "+(linkcheck._("created by %s at %s\n") % (Config.AppName,
                      _strtime(self.starttime))))
            self.fd.write("# "+(linkcheck._("Get the newest version at %s\n") % Config.Url))
            self.fd.write("# "+(linkcheck._("Write comments and bugs to %s\n\n") % \
	                    Config.Email))
            self.fd.write(linkcheck._("# Format of the entries:\n")+\
                          "# urlname;\n"
                          "# recursionlevel;\n"
                          "# parentname;\n"
                      "# baseref;\n"
                      "# errorstring;\n"
                      "# validstring;\n"
                      "# warningstring;\n"
                      "# infostring;\n"
                      "# valid;\n"
                      "# url;\n"
                      "# line;\n"
                      "# name;\n"
                      "# downloadtime;\n"
                      "# checktime;\n"
                      "# cached;\n")
            self.fd.flush()

    def newUrl(self, urlData):
        if self.fd is None: return
        self.fd.write(
	    "%s%s%d%s%s%s%s%s%s%s%s%s%s%s%s%s%d%s%s%s%d%s%s%s%d%s%d%s%d\n" % (
	    urlData.urlName, self.separator,
	    urlData.recursionLevel, self.separator,
	    urlData.parentName, self.separator,
            urlData.baseRef, self.separator,
            urlData.errorString, self.separator,
            urlData.validString, self.separator,
            urlData.warningString, self.separator,
            urlData.infoString, self.separator,
            urlData.valid, self.separator,
            urlData.url, self.separator,
            urlData.line, self.separator,
            urlData.name, self.separator,
            urlData.downloadtime, self.separator,
            urlData.checktime, self.separator,
            urlData.cached))
        self.fd.flush()


    def endOfOutput(self, linknumber=-1):
        if self.fd is None: return
        self.stoptime = time.time()
        if self.logfield("outro"):
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("# "+linkcheck._("Stopped checking at %s") % _strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
            self.fd.flush()
        self.fd = None



class TestLogger(Logger):
    """ Output for regression test """
    def init(self):
        pass

    def newUrl(self, urlData):
        print 'url',urlData.urlName
        if urlData.cached:
            print "cached"
        if urlData.name:
            print "name",urlData.name
        if urlData.baseRef:
            print "baseurl",urlData.baseRef
        if urlData.infoString:
            print "info",urlData.infoString
        if urlData.warningString:
            print "warning",urlData.warningString
        if urlData.valid:
            print "valid"
        else:
            print "error"

    def endOfOutput(self, linknumber=-1):
        pass
