"""String interpolation
20 Oct 1996
    Initial version called Itpl by Ka-Ping Yee
13 Jan 2000
    Modified by Bastian Kleineidam to emulate Perls Text::Template
   
Usage:
Template data consists of normal text and python code fragments.
Code fragments start with a dollar sign followed either by
1) variable or attribute reference or subscription or function call
   evaluates to the str() value of the given expression
   example: $printit()
   
2) python statements
   append arbitrary objects to the output list

Limitations:
1) Code fragments are arbitrary strings with matching "{}" parantheses.
   No further syntax verification is done.
2) Parameters to function calls must not have parantheses inside.
   Parameters to subscriptions must not have brackets inside.
   In code fragments, this is allowed, so you can use
   ${OUT = OUT + trunk[idx[1](data())]}

Example:
import Template

t = Template.Template("blabla.tmpl")
open("blabla","w").write(t.fill_in({"var1":1,"var2":'hui'}))
"""
import sys, string, re
from types import StringType

# type argument (we cannot distinguish between filename and string type)
FILENAME = 0
ARRAY    = 1
FILE     = 2
STRING   = 3

# regular expressions for lexical analysis
# note we only match a subset of the language definition
# we match identifiers, attribute reference, subscriptions,
# slicings and function calls
identifier = "[a-zA-Z_][a-zA-Z0-9_]*"
attributeref = identifier + "(\." + identifier + ")*"
subscription = "(\[.*?\])?"                        # optional
callargs = "(\(.*?\))?"                            # optional
# now the whole regex
regexvar = re.compile("^" + attributeref + subscription + callargs)


class TemplateError(StandardError):
    pass


class Template:
    def __init__(self, data, argtype = FILENAME):
        "load the template in self.data"
        if argtype == FILENAME:
            file = open(data)
            self.data = string.join(file.readlines(), "")
            file.close()
        elif argtype == FILE:
            if data.closed:
                wasclosed = 1
                open(data)
            else:
                wasclosed = 0
            self.data = string.join(data.readlines(), "")
            if wasclosed:
                data.close()
        elif argtype == ARRAY:
            self.data = string.join(data, "\n")
        else:
            self.data = data
        if type(self.data) != StringType:
            raise TemplateError, "could not read data"


    def fill_in(self, dict={}):
        "parse the template and fill in values"
        try:
            namechars = 'abcdefghijklmnopqrstuvwxyz' \
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_';
            out = ""
            pos = 0
            while pos < len(self.data) and \
                  string.find(self.data, "$", pos) != -1:
                dollar = string.find(self.data, "$", pos)
                # append pure text without dollar
                out = out + self.data[pos:dollar]
                pos = dollar + 1
                nextchar = self.data[dollar+1]

                if nextchar == '{':
                    # apply a code fragment
                    level = 1
                    while level:
                        pos = pos + 1
                        if self.data[pos] == "{":
                            level = level + 1
                        elif self.data[pos] == "}":
                            level = level - 1
                    output = []
                    exec self.data[(dollar+2):pos] in dict, {"output":output}
                    for obj in output:
                        out = out + obj
                    pos = pos + 1

                elif nextchar in namechars:
                    # scan a variable access
                    var = regexvar.match(self.data[pos:])
                    if var:
                        # Houston, we have a match!
                        # extract the string and evaluate it
                        var = var.group()
                        pos = pos + len(var)
                        out = out + str(eval(var, dict))
                else:
                    if nextchar == "$":
                        pos = pos + 1
                        out = out + "$"

            if pos < len(self.data): 
                out = out + self.data[pos:]
        except:
            sys.stderr.write("Template.py: parse error at pos "+`pos`+":\n"+\
                             out+"\n")

        return out

