"""various string utils"""
#    Copyright (C) 2000,2001  Bastian Kleineidam
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import string,re,sys,htmlentitydefs

entities = htmlentitydefs.entitydefs.items()
HtmlTable = map(lambda x: (x[1], "&"+x[0]+";"), entities)
UnHtmlTable = map(lambda x: ("&"+x[0]+";", x[1]), entities)
# order matters!
HtmlTable.sort()
UnHtmlTable.sort()
UnHtmlTable.reverse()

SQLTable = [
    ("'","''")
]

TeXTable = []

def stripHtmlComments(data):
    "Remove <!-- ... --> HTML comments from data"
    i = string.find(data, "<!--")
    while i!=-1:
        j = string.find(data, "-->", i)
        if j == -1:
            break
        data = data[:i] + data[j+3:]
        i = string.find(data, "<!--")
    return data


def stripFenceComments(data):
    "Remove # ... comments from data"
    lines = string.split(data, "\n")
    ret = None
    for line in lines:
        if not re.compile("\s*#.*").match(line):
            if ret:
                ret += "\n" + line
            else:
                ret = line
    return ret


def rstripQuotes(s):
    "Strip optional ending quotes"
    if len(s)<1:
        return s
    if s[-1]=="\"" or s[-1]=="'":
        s = s[:-1]
    return s


def lstripQuotes(s):
    "Strip optional leading quotes"
    if len(s)<1:
        return s
    if s[0]=="\"" or s[0]=="'":
        s = s[1:]
    return s


def stripQuotes(s):
    "Strip optional quotes"
    if len(s)<2:
        return s
    if s[0]=="\"" or s[0]=="'":
        s = s[1:]
    if s[-1]=="\"" or s[-1]=="'":
        s = s[:-1]
    return s


def indent(s, level):
    "indent each line of s with <level> spaces"
    return indentWith(s, level * " ")


def indentWith(s, indent):
    "indent each line of s with given indent argument"
    i = 0
    while i < len(s):
        if s[i]=="\n" and (i+1) < len(s):
            s = s[0:(i+1)] + indent + s[(i+1):]
        i += 1
    return s


def blocktext(s, width):
    "Adjust lines of s to be not wider than width"
    # split into lines
    s = string.split(s, "\n")
    s.reverse()
    line = None
    ret = ""
    while len(s):
        if line:
            line += "\n"+s.pop()
        else:
            line = s.pop()
        while len(line) > width:
            i = getLastWordBoundary(line, width)
            ret += string.strip(line[0:i]) + "\n"
            line = string.strip(line[i:])
    return ret + line


def getLastWordBoundary(s, width):
    """Get maximal index i of a whitespace char in s with 0 < i < width.
    Note: if s contains no whitespace this returns width-1"""
    match = re.compile(".*\s").match(s[0:width])
    if match:
        return match.end()
    return width-1


def applyTable(table, str):
    "apply a table of replacement pairs to str"
    for mapping in table:
        str = string.replace(str, mapping[0], mapping[1])
    return str


def texify(str):
    "Escape special TeX chars and strings"
    return applyTable(TeXTable, str)


def sqlify(str):
    "Escape special SQL chars and strings"
    if not str:
        return "NULL"
    return "'"+applyTable(SQLTable, str)+"'"


def htmlify(str):
    "Escape special HTML chars and strings"
    return applyTable(HtmlTable, str)


def unhtmlify(str):
    return applyTable(UnHtmlTable, str)


def getLineNumber(str, index):
    "return the line number of str[index]"
    i=0
    if index<0: index=0
    line=1
    while i<index:
        if str[i]=='\n': 
            line += 1
        i += 1
    return line

def paginate(text, lines=22):
    """print text in pages of lines size"""
    textlines = string.split(text, "\n")
    curline = 1
    for line in textlines:
        print line
        curline += 1
        if curline >= lines and sys.stdin.isatty():
            curline = 1
            print "press return to continue..."
            sys.stdin.read(1)


if __name__=='__main__':
    print htmlify("הצü")
    print unhtmlify("&auml;&nbsp;&auml;&amp;auml;")
