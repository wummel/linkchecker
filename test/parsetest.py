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
