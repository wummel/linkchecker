import string,re

HtmlTable = [
        ("ä","&auml;"),
        ("ö","&ouml;"),
        ("ü","&uuml;"),
        ("Ä","&Auml;"),
        ("Ö","&Ouml;"),
        ("Ü","&Uuml;"),
        ("ß","&szlig;"),
        ("&","&amp;"),
        ("<","&lt;"),
        (">","&gt;"),
        ("é","&eacute;"),
        ("è","&egrave")
    ]

SQLTable = [
    ("'","''")
]

def stripHtmlComments(data):
    i = string.find(data, "<!--")
    while i!=-1:
        j = string.find(data, "-->", i)
        if j == -1:
            break
        data = data[:i] + data[j+3:]
        i = string.find(data, "<!--")
    return data


def stripFenceComments(data):
    lines = string.split(data, "\n")
    ret = None
    for line in lines:
        if not re.compile("\s*#.*").match(line):
            if ret:
                ret = ret + "\n" + line
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
    return indentWith(s, level * " ")
    

def indentWith(s, indent):
    i = 0
    while i < len(s):
        if s[i]=="\n" and (i+1) < len(s):
            s = s[0:(i+1)] + indent + s[(i+1):]
        i = i+1
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
            line = line+"\n"+s.pop()
        else:
            line = s.pop()
        while len(line) > width:
            i = getLastWordBoundary(line, width)
            ret = ret + string.strip(line[0:i]) + "\n"
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
    for mapping in table:
        str = string.replace(str, mapping[0], mapping[1])
    return str
    

def texify(str):
    return applyTable(TexTable, str)

def sqlify(str):
    if not str:
        return "NULL"
    return "'"+applyTable(SQLTable, str)+"'"

def htmlify(str):
    return applyTable(HtmlTable, str)

def getLineNumber(str, index):
    i=0
    if index<0: index=0
    line=1
    while i<index:
        if str[i]=='\n': 
            line = line + 1
        i = i+1
    return line
    