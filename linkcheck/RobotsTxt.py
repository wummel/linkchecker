"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
import re,urlparse,string,httplib,urllib,sys,StringUtil,Config

class RobotsTxt:
    def __init__(self, urltuple, useragent):
        self.entries = []
        self.disallowAll = 0
        self.allowAll = 0
        self.base = urltuple[0]+"://"+urltuple[1]+"/robots.txt"
        
        try:
            urlConnection = None
            if urltuple[0]=="http":
                urlConnection = httplib.HTTP(urltuple[1])
            else:
                import httpslib
                urlConnection = httpslib.HTTPS(urltuple[1])
            urlConnection.putrequest("GET", "/robots.txt")
            urlConnection.putheader("User-agent", useragent)
            urlConnection.endheaders()
            status = urlConnection.getreply()[0]
            if status==401 or status==403:
                self.disallowAll = 1
            else:
                if status>=400:
                    self.allowAll = 1
            
            if status<400:
                self.parseUrl(urlConnection)
        except:
            type, value = sys.exc_info()[:2]
            Config.debug("Hoppla. "+str(value))
            self.allowAll = 1
            
    def parseUrl(self, urlConnection):
        data = urlConnection.getfile().readlines()
        state = 0
        linenumber = 0
        entry = Entry()
        
        for line in data:
            line = string.lower(string.strip(line))
            linenumber = linenumber + 1
            
            if len(line)<=0:
                if state==1:
                    raise ParseException, \
                    "robots.txt:"+`linenumber`+": no rules found"
                elif state==2:
                    self.entries.append(entry)
                    entry = Entry()
                    state = 0
            line = string.strip(StringUtil.stripFenceComments(line))
            if len(line)<=0:
                continue
            
            if re.compile("^user-agent:.+").match(line):
                if state==2:
                    raise ParseException, \
                    "robots.txt:"+`linenumber`+": user-agent in the middle of rules"
                entry.useragents.append(string.strip(line[11:]))
                state = 1
                
            elif re.compile("^disallow:.+").match(line):
                if state==0:
                    raise ParseException, \
                    "robots.txt:"+`linenumber`+": disallow without user agents"
                line = string.strip(line[9:])
                entry.rulelines.append(RuleLine(line, 0))
                state = 2
                
            elif re.compile("^allow:.+").match(line):
                if state==0:
                    raise ParseException, \
                    "robots.txt:"+`linenumber`+": allow without user agents"
                line = string.strip(line[6:])
                entry.rulelines.append(RuleLine(line, 1))
                
            else:
                # ignore extensions
                pass
    
    
    def allowance(self, useragent, path):
        Config.debug("DEBUG: checking allowance\n")
        if self.disallowAll:
            return 0
        if self.allowAll:
            return 1
            
        # search for given user agent matches
        # the first match counts
        useragent = string.lower(useragent)
        for entry in self.entries:
            if entry.appliesToAgent(useragent):
                return entry.allowance(path)
        # agent not found ==> access granted
        Config.debug("DEBUG: no match, access granted\n")
        return 1
        
    def __str__(self):
        ret = "RobotsTxt\n"+\
              "Base: "+self.base+"\n"+\
              "AllowAll: "+`self.allowAll`+"\n"+\
              "DisallowAll: "+`self.disallowAll`+"\n"
        for entry in self.entries:
            ret = ret + str(entry) + "\n"
        return ret
    
    
    
class RuleLine:
    def __init__(self, path, allowance):
        self.path = urllib.unquote(path)
        self.allowance = allowance
    
    
    def appliesTo(self, filename):
        return self.path=="*" or re.compile(self.path).match(filename)
    
    
    def __str__(self):
        if self.allowance:
            return "Allow: "+self.path
        return "Disallow: "+self.path
    
    
    
class Entry:
    def __init__(self):
        self.useragents = []
        self.rulelines = []
    
    
    def __str__(self):
        ret = ""
        for agent in self.useragents:
            ret = ret + "User-agent: "+agent+"\n"
        for line in self.rulelines:
            ret = ret + str(line) + "\n"
        return ret
        
        
    def appliesToAgent(self, agent):
        "check if this entry applies to the specified agent"
        for cur_agent in self.useragents:
            if cur_agent=="*":
                return 1
            if re.compile("^"+cur_agent).match(agent):
                return 1
        return 0
        
        
    def allowance(self, filename):
        """Preconditions:
        - out agent applies to this entry
        - file is URL decoded"""
        for line in self.rulelines:
            if line.appliesTo(filename):
                return line.allowance
        return 1
        
